"""Application service for orchestrating multi-format report generation (Excel, Word, PDF)."""

from datetime import datetime, timezone
from decimal import Decimal
import hashlib
from pathlib import Path
from typing import Dict, List, Optional
import uuid

from sqlalchemy import select

from app.application.dtos.financial_statements_dto import (
    AssetScheduleRowDTO,
    LoanScheduleRowDTO,
)
from app.application.dtos.report_dto import (
    AnnualLoanSummaryDTO,
    CostAndFundingDTO,
    CostItemRowDTO,
    ExecutiveSummaryDTO,
    FundingSourceRowDTO,
    GeneratedReportResultDTO,
    HorizontalStatementDTO,
    HorizontalTableRowDTO,
    ProjectReportDataDTO,
    ReportDocumentMetadataDTO,
)
from app.application.services.appraisal_service import AppraisalService
from app.common.exceptions import ValidationError
from app.common.money import paise_to_rupees, rupees_to_paise
from app.config import AppConfig
from app.infrastructure.database.connection import DatabaseManager
from app.infrastructure.database.models.calculation_model import (
    CalculationRunModel,
    LoanScheduleResultModel,
    StatementLineResultModel,
)
from app.infrastructure.database.models.client_model import ClientModel
from app.infrastructure.database.models.entity_model import EntityModel
from app.infrastructure.database.models.funding_model import FundingSourceModel
from app.infrastructure.database.models.project_cost_model import ProjectCostItemModel
from app.infrastructure.database.models.project_model import ProjectModel, ProjectPeriodModel, ProjectScenarioModel
from app.infrastructure.database.models.report_model import GeneratedReportModel, ReportTemplateModel
from app.infrastructure.reporting.docx_renderer import DocxReportRenderer
from app.infrastructure.reporting.excel_renderer import ExcelReportRenderer
from app.infrastructure.reporting.pdf_renderer import PdfReportRenderer
from app.infrastructure.repositories.calculation_repository import CalculationRepository
from app.infrastructure.repositories.report_repository import ReportRepository


class ReportService:
    """Orchestrates report model creation, document rendering (Excel, Word, PDF), and export audit logging."""

    def __init__(self, db_manager: DatabaseManager, config: Optional[AppConfig] = None) -> None:
        self.db_manager = db_manager
        self.config = config
        self.appraisal_service = AppraisalService(db_manager)

    def list_templates(self) -> List[ReportTemplateModel]:
        with self.db_manager.session_scope() as session:
            repo = ReportRepository(session)
            return repo.list_templates()

    def list_generated_reports(self, project_id: Optional[uuid.UUID] = None) -> List[GeneratedReportModel]:
        with self.db_manager.session_scope() as session:
            repo = ReportRepository(session)
            return repo.list_generated_reports(project_id=project_id)

    def build_report_data_model(
        self,
        scenario_id: uuid.UUID,
        calculation_run_id: Optional[uuid.UUID] = None,
        template_code: str = "TMPL_CMA_BANK",
    ) -> ProjectReportDataDTO:
        """Constructs an immutable ProjectReportDataDTO from a calculation run for rendering across all formats."""
        with self.db_manager.session_scope() as session:
            calc_repo = CalculationRepository(session)
            report_repo = ReportRepository(session)

            # 1. Fetch Scenario, Project, Entity, Client
            scenario = session.get(ProjectScenarioModel, scenario_id)
            if not scenario:
                raise ValidationError(f"Scenario with ID '{scenario_id}' not found.")

            project = session.get(ProjectModel, scenario.project_id)
            if not project:
                raise ValidationError(f"Project with ID '{scenario.project_id}' not found.")

            entity = session.get(EntityModel, project.entity_id)
            if not entity:
                raise ValidationError(f"Entity with ID '{project.entity_id}' not found.")

            client = session.get(ClientModel, entity.client_id)
            client_name = client.display_name if client else "Client"

            # 2. Fetch Calculation Run
            if calculation_run_id:
                run = calc_repo.get_run_by_id(calculation_run_id)
            else:
                run = calc_repo.get_latest_run(scenario_id)

            if not run:
                raise ValidationError(f"No calculation run found for scenario '{scenario_id}'. Please run projections first.")

            # 3. Fetch Project Periods
            periods_stmt = (
                select(ProjectPeriodModel)
                .where(ProjectPeriodModel.project_id == project.id)
                .order_by(ProjectPeriodModel.period_sequence)
            )
            periods = list(session.execute(periods_stmt).scalars().all())
            period_headers = [f"{p.period_label} (Y{p.period_sequence})" for p in periods]
            period_id_to_seq = {p.id: p.period_sequence for p in periods}

            # 4. Fetch Template
            template = report_repo.get_template_by_code(template_code)
            template_name = template.template_name if template else "Bank Credit Appraisal Template"
            template_version = template.template_version if template else "1.0"

            # 5. Fetch Cost & Funding
            costs_stmt = select(ProjectCostItemModel).where(
                ProjectCostItemModel.scenario_id == scenario_id,
                ProjectCostItemModel.is_active.is_(True),
            )
            cost_items = list(session.execute(costs_stmt).scalars().all())
            cost_rows: List[CostItemRowDTO] = [
                CostItemRowDTO(
                    head_name=item.cost_head.head_name if item.cost_head else "Capital Expenditure",
                    description=item.description,
                    basic_rupees=paise_to_rupees(item.basic_amount_paise),
                    gst_rate_pct=Decimal(item.gst_rate_pct_text) if item.gst_rate_pct_text else Decimal("0.0"),
                    capitalised_rupees=paise_to_rupees(item.capitalised_amount_paise),
                    cash_required_rupees=paise_to_rupees(item.project_cash_requirement_paise),
                )
                for item in cost_items
            ]
            total_cost_rupees = sum(c.capitalised_rupees for c in cost_rows)

            funding_stmt = select(FundingSourceModel).where(
                FundingSourceModel.scenario_id == scenario_id,
                FundingSourceModel.is_active.is_(True),
            )
            funding_sources = list(session.execute(funding_stmt).scalars().all())
            total_fund_paise = sum(f.amount_paise for f in funding_sources)
            total_fund_rupees = paise_to_rupees(total_fund_paise)

            funding_rows: List[FundingSourceRowDTO] = [
                FundingSourceRowDTO(
                    head_name=f.funding_head.funding_name if f.funding_head else "Finance Facility",
                    source_name=f.source_name,
                    amount_rupees=paise_to_rupees(f.amount_paise),
                    percentage=(
                        (Decimal(f.amount_paise) / Decimal(total_fund_paise) * Decimal("100"))
                        if total_fund_paise > 0 else Decimal("0.00")
                    ),
                    terms_note=f.terms_note or "-",
                )
                for f in funding_sources
            ]

            funding_gap_rupees = total_cost_rupees - total_fund_rupees
            term_debt_rupees = sum(
                f.amount_rupees for f in funding_rows if "TERM" in f.head_name.upper() or "LOAN" in f.head_name.upper()
            )
            equity_rupees = sum(
                f.amount_rupees for f in funding_rows if "EQUITY" in f.head_name.upper() or "PROMOTER" in f.head_name.upper()
            )
            der = (term_debt_rupees / equity_rupees) if equity_rupees > 0 else None

            cost_and_funding_dto = CostAndFundingDTO(
                cost_items=cost_rows,
                funding_sources=funding_rows,
                total_cost_rupees=total_cost_rupees,
                total_funding_rupees=total_fund_rupees,
                funding_gap_rupees=funding_gap_rupees,
                debt_equity_ratio=der,
            )

            # 6. Fetch Statements & Build Horizontal Tables
            line_results = calc_repo.get_statement_lines_for_run(run.id)
            by_type_code_seq: Dict[str, Dict[str, Dict[int, Decimal]]] = {}
            line_labels: Dict[str, str] = {}

            for line in line_results:
                seq = period_id_to_seq.get(line.period_id, 1)
                by_type_code_seq.setdefault(line.statement_type, {}).setdefault(line.line_code, {})[seq] = paise_to_rupees(line.amount_paise)
                line_labels[line.line_code] = line.line_label_snapshot

            pl_stmt = self._build_horizontal_statement(
                statement_type="PL",
                title="Projected Profit & Loss Account",
                period_headers=period_headers,
                code_data=by_type_code_seq.get("PL", {}),
                line_labels=line_labels,
                line_specs=[
                    ("1", "A", "GROSS_REVENUE", False, False),
                    ("2", "A", "OUTPUT_GST", False, False),
                    ("3", "A", "NET_REVENUE", False, True),
                    ("4", "B", "RAW_MATERIAL_COST", False, False),
                    ("5", "B", "OTHER_DIRECT_COSTS", False, False),
                    ("6", "B", "TOTAL_DIRECT_COSTS", False, True),
                    ("7", "C", "GROSS_PROFIT", False, True),
                    ("8", "D", "EMPLOYEE_EXPENSES", False, False),
                    ("9", "D", "ADMIN_EXPENSES", False, False),
                    ("10", "D", "SELLING_EXPENSES", False, False),
                    ("11", "D", "TOTAL_OPEX", False, True),
                    ("12", "E", "EBITDA", False, True),
                    ("13", "F", "DEPRECIATION", False, False),
                    ("14", "G", "EBIT", False, True),
                    ("15", "H", "FINANCE_COSTS", False, False),
                    ("16", "I", "PBT", False, True),
                    ("17", "J", "TAX_PROVISION", False, False),
                    ("18", "K", "PAT", False, True),
                ],
            )

            bs_stmt = self._build_horizontal_statement(
                statement_type="BS",
                title="Projected Balance Sheet",
                period_headers=period_headers,
                code_data=by_type_code_seq.get("BS", {}),
                line_labels=line_labels,
                line_specs=[
                    ("I", "", "EQUITY AND LIABILITIES", True, False),
                    ("1", "1", "NET_WORTH", False, False),
                    ("2", "2", "LONG_TERM_DEBT", False, False),
                    ("3", "3", "SHORT_TERM_WC_DEBT", False, False),
                    ("4", "4", "TRADE_PAYABLES", False, False),
                    ("5", "5", "OTHER_CURRENT_LIAB", False, False),
                    ("6", "6", "TOTAL_CURRENT_LIAB", False, True),
                    ("7", "7", "TOTAL_LIABILITIES_EQUITY", False, True),
                    ("II", "", "ASSETS", True, False),
                    ("8", "8", "FIXED_ASSETS_NET", False, False),
                    ("9", "9", "INVENTORY_TOTAL", False, False),
                    ("10", "10", "TRADE_RECEIVABLES", False, False),
                    ("11", "11", "CASH_AND_BANK", False, False),
                    ("12", "12", "TOTAL_CURRENT_ASSETS", False, True),
                    ("13", "13", "TOTAL_ASSETS", False, True),
                ],
            )

            cf_stmt = self._build_horizontal_statement(
                statement_type="CASH_FLOW",
                title="Projected Cash Flow Statement (Indirect Method)",
                period_headers=period_headers,
                code_data=by_type_code_seq.get("CASH_FLOW", {}),
                line_labels=line_labels,
                line_specs=[
                    ("A", "", "CASH FLOW FROM OPERATING ACTIVITIES", True, False),
                    ("1", "A1", "CF_OP_PROFIT", False, False),
                    ("2", "A2", "CF_WC_CHANGES", False, False),
                    ("3", "A3", "CF_NET_OPERATING", False, True),
                    ("B", "", "CASH FLOW FROM INVESTING ACTIVITIES", True, False),
                    ("4", "B1", "CF_CAPEX", False, False),
                    ("5", "B2", "CF_NET_INVESTING", False, True),
                    ("C", "", "CASH FLOW FROM FINANCING ACTIVITIES", True, False),
                    ("6", "C1", "CF_EQUITY_INTRODUCED", False, False),
                    ("7", "C2", "CF_LOAN_DISBURSEMENT", False, False),
                    ("8", "C3", "CF_LOAN_REPAYMENT", False, False),
                    ("9", "C4", "CF_DRAWINGS", False, False),
                    ("10", "C5", "CF_NET_FINANCING", False, True),
                    ("D", "", "NET INCREASE / (DECREASE) IN CASH", False, True),
                    ("11", "D1", "NET_CASH_FLOW", False, True),
                    ("12", "D2", "OPENING_CASH", False, False),
                    ("13", "D3", "CLOSING_CASH", False, True),
                ],
            )

            # 7. Fetch Loan Schedules & Aggregate Annual Summaries
            loan_models = calc_repo.get_loan_schedules_for_run(run.id)
            loan_rows = [
                LoanScheduleRowDTO(
                    installment_number=m.installment_number,
                    due_date=str(m.due_date),
                    opening_balance_rupees=paise_to_rupees(m.opening_balance_paise),
                    disbursement_rupees=paise_to_rupees(m.disbursement_paise),
                    payment_rupees=paise_to_rupees(m.payment_paise),
                    interest_rupees=paise_to_rupees(m.interest_paise),
                    principal_rupees=paise_to_rupees(m.principal_paise),
                    closing_balance_rupees=paise_to_rupees(m.closing_balance_paise),
                )
                for m in loan_models
            ]

            annual_loan_summaries: List[AnnualLoanSummaryDTO] = []
            for p in periods:
                seq = p.period_sequence
                # Installments for year seq (1..12, 13..24, etc.)
                start_m = (seq - 1) * 12 + 1
                end_m = seq * 12
                y_insts = [m for m in loan_models if start_m <= m.installment_number <= end_m]
                if y_insts:
                    open_bal = paise_to_rupees(y_insts[0].opening_balance_paise)
                    disb = paise_to_rupees(sum(i.disbursement_paise for i in y_insts))
                    prin = paise_to_rupees(sum(i.principal_paise for i in y_insts))
                    intr = paise_to_rupees(sum(i.interest_paise for i in y_insts))
                    tot_service = prin + intr
                    close_bal = paise_to_rupees(y_insts[-1].closing_balance_paise)
                else:
                    open_bal = disb = prin = intr = tot_service = close_bal = Decimal("0.00")

                annual_loan_summaries.append(
                    AnnualLoanSummaryDTO(
                        period_sequence=seq,
                        period_label=p.period_label,
                        opening_balance_rupees=open_bal,
                        disbursement_rupees=disb,
                        principal_repaid_rupees=prin,
                        interest_paid_rupees=intr,
                        total_debt_service_rupees=tot_service,
                        closing_balance_rupees=close_bal,
                    )
                )

            # 8. Fetch Asset Schedule
            asset_models = calc_repo.get_asset_schedules_for_run(run.id)
            seq_to_label = {p.period_sequence: p.period_label for p in periods}
            asset_rows = [
                AssetScheduleRowDTO(
                    period_sequence=period_id_to_seq.get(a.period_id, 1),
                    period_label=seq_to_label.get(period_id_to_seq.get(a.period_id, 1), f"Y{period_id_to_seq.get(a.period_id, 1)}"),
                    opening_gross_rupees=paise_to_rupees(a.opening_gross_paise),
                    additions_rupees=paise_to_rupees(a.additions_paise),
                    disposals_rupees=paise_to_rupees(a.disposals_paise),
                    closing_gross_rupees=paise_to_rupees(a.closing_gross_paise),
                    depreciation_rupees=paise_to_rupees(a.depreciation_paise),
                    accumulated_depreciation_rupees=paise_to_rupees(a.accumulated_depreciation_paise),
                    closing_nbv_rupees=paise_to_rupees(a.closing_nbv_paise),
                )
                for a in asset_models
            ]

        # 9. Evaluate Appraisal Metrics & Validation via AppraisalService
        appraisal_report = self.appraisal_service.evaluate_appraisal(
            scenario_id=scenario_id,
            calculation_run_id=run.id,
        )

        # 10. Horizontal Ratios Statement
        ratios_rows = []
        for idx, r in enumerate(appraisal_report.ratio_rows, start=1):
            if r.category != "BREAK_EVEN":
                amounts_dict = {}
                for seq, val_str in r.period_values.items():
                    # Parse numeric value if possible
                    clean = val_str.replace("₹", "").replace("%", "").replace("x", "").replace(",", "").strip()
                    try:
                        amounts_dict[seq] = Decimal(clean)
                    except Exception:
                        amounts_dict[seq] = None
                ratios_rows.append(
                    HorizontalTableRowDTO(
                        sr_no=str(idx),
                        note_ref=r.benchmark_text,
                        particulars=r.metric_name,
                        is_heading=False,
                        is_total=False,
                        amounts=amounts_dict,
                    )
                )

        ratios_stmt = HorizontalStatementDTO(
            statement_type="RATIOS",
            title="Financial Ratios & Lender DSCR Appraisal",
            period_headers=period_headers,
            rows=ratios_rows,
        )

        # 11. Horizontal Break-Even Statement
        bep_rows = []
        bep_metrics = [r for r in appraisal_report.ratio_rows if r.category == "BREAK_EVEN"]
        for idx, r in enumerate(bep_metrics, start=1):
            amounts_dict = {}
            for seq, val_str in r.period_values.items():
                clean = val_str.replace("₹", "").replace("%", "").replace("x", "").replace(",", "").strip()
                try:
                    amounts_dict[seq] = Decimal(clean)
                except Exception:
                    amounts_dict[seq] = None
            bep_rows.append(
                HorizontalTableRowDTO(
                    sr_no=str(idx),
                    note_ref=r.benchmark_text,
                    particulars=r.metric_name,
                    is_heading=False,
                    is_total="Sales" in r.metric_name or "Capacity" in r.metric_name,
                    amounts=amounts_dict,
                )
            )

        bep_stmt = HorizontalStatementDTO(
            statement_type="BREAK_EVEN",
            title="Break-Even Analysis & Safety Margins",
            period_headers=period_headers,
            rows=bep_rows,
        )

        # 12. Executive Summary DTO
        ret = appraisal_report.lifetime_returns
        first_yr_rev = pl_stmt.rows[2].amounts.get(1, Decimal("0.00")) if len(pl_stmt.rows) > 2 else Decimal("0.00")
        term_yr_rev = pl_stmt.rows[2].amounts.get(len(period_headers), Decimal("0.00")) if len(pl_stmt.rows) > 2 else Decimal("0.00")
        bep_cap_first = bep_rows[4].amounts.get(1, Decimal("0.00")) if len(bep_rows) > 4 else Decimal("0.00")

        val_status = "PASSED"
        if appraisal_report.error_count > 0:
            val_status = "ERRORS_DETECTED"
        elif appraisal_report.warning_count > 0:
            val_status = "WARNINGS_DETECTED"

        exec_summary_dto = ExecutiveSummaryDTO(
            total_project_cost_rupees=total_cost_rupees,
            promoter_equity_rupees=equity_rupees,
            term_loan_rupees=term_debt_rupees,
            working_capital_limit_rupees=Decimal("0.00"),
            first_year_net_revenue_rupees=first_yr_rev,
            terminal_year_net_revenue_rupees=term_yr_rev,
            average_gross_dscr=ret.average_gross_dscr,
            average_net_cfads_dscr=ret.average_net_cfads_dscr,
            cumulative_dscr=ret.cumulative_dscr,
            project_irr_pct=ret.irr_pct,
            npv_rupees=ret.npv_rupees,
            payback_years=ret.payback_years,
            first_year_bep_capacity_pct=bep_cap_first,
            validation_status=val_status,
            validation_error_count=appraisal_report.error_count,
            validation_warning_count=appraisal_report.warning_count,
        )

        # 13. Metadata DTO
        meta_dto = ReportDocumentMetadataDTO(
            report_title=template_name,
            client_name=client_name,
            entity_legal_name=entity.legal_name,
            constitution_label=entity.constitution_code,
            project_name=project.project_name,
            project_code=project.project_code,
            scenario_name=scenario.scenario_name,
            calculation_run_number=run.run_number,
            calculation_run_id=run.id,
            engine_version=run.engine_version,
            input_hash=run.input_hash,
            generated_at=datetime.now(timezone.utc),
            template_name=template_name,
            template_version=template_version,
            prepared_by=run.prepared_by_label or "Lead Financial Analyst",
        )

        return ProjectReportDataDTO(
            metadata=meta_dto,
            executive_summary=exec_summary_dto,
            cost_and_funding=cost_and_funding_dto,
            pl_statement=pl_stmt,
            bs_statement=bs_stmt,
            cf_statement=cf_stmt,
            ratios_statement=ratios_stmt,
            break_even_statement=bep_stmt,
            sensitivity_scenarios=appraisal_report.sensitivity_rows,
            loan_annual_summaries=annual_loan_summaries,
            loan_monthly_installments=loan_rows,
            asset_schedules=asset_rows,
            validation_issues=appraisal_report.validation_issues,
        )

    def _build_horizontal_statement(
        self,
        statement_type: str,
        title: str,
        period_headers: List[str],
        code_data: Dict[str, Dict[int, Decimal]],
        line_labels: Dict[str, str],
        line_specs: List[tuple],
    ) -> HorizontalStatementDTO:
        rows: List[HorizontalTableRowDTO] = []
        for sr, note, code, is_hdr, is_tot in line_specs:
            lbl = line_labels.get(code, code.replace("_", " ").title())
            amounts = code_data.get(code, {})
            rows.append(
                HorizontalTableRowDTO(
                    sr_no=sr,
                    note_ref=note,
                    particulars=lbl,
                    is_heading=is_hdr,
                    is_total=is_tot,
                    amounts=amounts,
                )
            )
        return HorizontalStatementDTO(
            statement_type=statement_type,
            title=title,
            period_headers=period_headers,
            rows=rows,
        )

    def generate_report(
        self,
        scenario_id: uuid.UUID,
        output_type: str = "EXCEL",  # EXCEL, DOCX, PDF
        template_code: str = "TMPL_CMA_BANK",
        calculation_run_id: Optional[uuid.UUID] = None,
        custom_output_path: Optional[str] = None,
    ) -> GeneratedReportResultDTO:
        """Generates document in selected format, hashes file, records generation in DB, and returns result."""
        # 1. Build immutable data model
        report_data = self.build_report_data_model(
            scenario_id=scenario_id,
            calculation_run_id=calculation_run_id,
            template_code=template_code,
        )

        # 2. Determine output path
        out_type = output_type.upper()
        if custom_output_path:
            out_file = Path(custom_output_path)
        else:
            safe_name = report_data.metadata.project_name.replace(" ", "_").replace("/", "_")
            timestamp_str = datetime.now().strftime("%Y%m%d_%H%M%S")
            ext_map = {"EXCEL": ".xlsx", "XLSX": ".xlsx", "DOCX": ".docx", "WORD": ".docx", "PDF": ".pdf"}
            ext = ext_map.get(out_type, ".xlsx")
            export_dir = Path("exports")
            export_dir.mkdir(exist_ok=True)
            out_file = export_dir / f"{safe_name}_Run{report_data.metadata.calculation_run_number}_{timestamp_str}{ext}"

        out_path_str = str(out_file.resolve())

        # 3. Render according to format
        if out_type in ("EXCEL", "XLSX"):
            ExcelReportRenderer.render(report_data, out_path_str)
        elif out_type in ("DOCX", "WORD"):
            DocxReportRenderer.render(report_data, out_path_str)
        elif out_type == "PDF":
            PdfReportRenderer.render(report_data, out_path_str)
        else:
            raise ValidationError(f"Unsupported report output format '{output_type}'. Choose EXCEL, DOCX, or PDF.")

        # 4. Compute SHA-256 Hash of output file
        with open(out_path_str, "rb") as f:
            file_bytes = f.read()
            file_hash = hashlib.sha256(file_bytes).hexdigest()
            file_size = len(file_bytes)

        # 5. Persist record in generated_reports table
        with self.db_manager.session_scope() as session:
            repo = ReportRepository(session)
            template = repo.get_template_by_code(template_code)
            template_id = template.id if template else uuid.uuid4()

            scenario = session.get(ProjectScenarioModel, scenario_id)
            project_id = scenario.project_id if scenario else uuid.uuid4()

            db_record = repo.create_generated_report(
                project_id=project_id,
                scenario_id=scenario_id,
                calculation_run_id=report_data.metadata.calculation_run_id,
                report_template_id=template_id,
                output_type=out_type,
                stored_relative_path=out_path_str,
                file_hash=file_hash,
                report_version=report_data.metadata.template_version,
                generation_status="SUCCESS",
            )
            report_id = db_record.id

        return GeneratedReportResultDTO(
            report_id=report_id,
            calculation_run_id=report_data.metadata.calculation_run_id,
            output_type=out_type,
            file_path=out_path_str,
            file_hash=file_hash,
            generated_at=datetime.now(timezone.utc),
            file_size_bytes=file_size,
        )
