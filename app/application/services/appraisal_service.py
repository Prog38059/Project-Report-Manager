"""Application service for Appraisal Metrics, Ratios, Break-Even, and Cross-Statement Validation."""

from datetime import datetime, timezone
from decimal import Decimal, ROUND_HALF_UP
from typing import Dict, List, Optional, Tuple
import uuid

from sqlalchemy import select

from app.application.dtos.appraisal_dto import (
    AppraisalReportDTO,
    ProjectLifetimeReturnsDTO,
    RatioMetricRowDTO,
    SensitivityRowDTO,
    ValidationIssueDTO,
)
from app.common.exceptions import ValidationError
from app.common.money import format_inr, paise_to_rupees, rupees_to_paise
from app.domain.financial.appraisal import (
    AppraisalEngine,
    PeriodRatioResult,
    ProjectAppraisalSummary,
)
from app.domain.financial.statement_pipeline import PeriodFinancialStatements
from app.domain.financial.validation import (
    FinancialValidationEngine,
    ValidationIssue,
    ValidationSeverity,
)
from app.infrastructure.database.connection import DatabaseManager
from app.infrastructure.database.models.calculation_model import (
    CalculationRunModel,
    LoanScheduleResultModel,
    RatioResultModel,
    StatementLineResultModel,
    ValidationResultModel,
)
from app.infrastructure.database.models.funding_model import FundingSourceModel
from app.infrastructure.database.models.project_cost_model import ProjectCostItemModel
from app.infrastructure.database.models.project_model import ProjectModel, ProjectPeriodModel, ProjectScenarioModel
from app.infrastructure.repositories.calculation_repository import CalculationRepository


class AppraisalService:
    """Orchestrates lender appraisal metrics, ratios, break-even, sensitivity, and validation rules."""

    def __init__(self, db_manager: DatabaseManager) -> None:
        self.db_manager = db_manager

    def evaluate_appraisal(
        self,
        scenario_id: uuid.UUID,
        calculation_run_id: Optional[uuid.UUID] = None,
        discount_rate_pct: Decimal = Decimal("10.0"),
        min_acceptable_dscr: Decimal = Decimal("1.25"),
        max_acceptable_der: Decimal = Decimal("3.00"),
        min_acceptable_cr: Decimal = Decimal("1.33"),
    ) -> AppraisalReportDTO:
        """Evaluates appraisal ratios and validation rules for a calculation run, persists results, and returns DTO."""
        with self.db_manager.session_scope() as session:
            calc_repo = CalculationRepository(session)

            # 1. Fetch Target Calculation Run
            if calculation_run_id:
                run = calc_repo.get_run_by_id(calculation_run_id)
            else:
                run = calc_repo.get_latest_run(scenario_id)

            if not run:
                raise ValidationError(f"No calculation run found for scenario '{scenario_id}'. Please run projections first.")

            # 2. Fetch Project Periods
            periods_stmt = (
                select(ProjectPeriodModel)
                .join(ProjectScenarioModel, ProjectScenarioModel.project_id == ProjectPeriodModel.project_id)
                .where(ProjectScenarioModel.id == scenario_id)
                .order_by(ProjectPeriodModel.period_sequence)
            )
            periods = list(session.execute(periods_stmt).scalars().all())
            if not periods:
                raise ValidationError(f"No projection periods defined for scenario '{scenario_id}'.")

            period_seq_to_model = {p.period_sequence: p for p in periods}
            period_id_to_seq = {p.id: p.period_sequence for p in periods}
            period_headers = [f"{p.period_label} (Y{p.period_sequence})" for p in periods]

            # 3. Fetch Line Results & Loan Schedules
            line_results = calc_repo.get_statement_lines_for_run(run.id)
            loan_results = calc_repo.get_loan_schedules_for_run(run.id)

            if not line_results:
                raise ValidationError(f"No statement line results found for calculation run '{run.id}'.")

            # 4. Fetch Project Capex and Funding Sources for Initial Outflow and Funding Gap
            costs_stmt = select(ProjectCostItemModel).where(
                ProjectCostItemModel.scenario_id == scenario_id,
                ProjectCostItemModel.is_active.is_(True),
            )
            cost_items = list(session.execute(costs_stmt).scalars().all())
            total_capex_paise = sum(item.capitalised_amount_paise for item in cost_items)

            funding_stmt = select(FundingSourceModel).where(
                FundingSourceModel.scenario_id == scenario_id,
                FundingSourceModel.is_active.is_(True),
            )
            funding_sources = list(session.execute(funding_stmt).scalars().all())
            total_funding_paise = sum(source.amount_paise for source in funding_sources)
            funding_gap_paise = total_capex_paise - total_funding_paise

            # Initial investment is capex (minimum 1 paise to prevent div by 0)
            initial_investment_paise = max(1, total_capex_paise)

            # 5. Aggregate Annual Debt Service from Loan Results
            term_loan_principal_by_seq: Dict[int, int] = {p.period_sequence: 0 for p in periods}
            term_loan_interest_by_seq: Dict[int, int] = {p.period_sequence: 0 for p in periods}

            for loan_row in loan_results:
                # Map installment month to year sequence (1..7)
                inst_num = loan_row.installment_number
                seq = ((inst_num - 1) // 12) + 1
                if seq in term_loan_principal_by_seq:
                    term_loan_principal_by_seq[seq] += loan_row.principal_paise
                    term_loan_interest_by_seq[seq] += loan_row.interest_paise

            # 6. Reconstruct Period Statements from Line Results
            statements = self._reconstruct_statements_from_lines(
                line_results=line_results,
                periods=periods,
            )

            # 7. Execute Domain Appraisal Calculations
            appraisal = AppraisalEngine.calculate_project_appraisal(
                statements=statements,
                initial_investment_paise=initial_investment_paise,
                discount_rate_pct=discount_rate_pct,
                term_loan_principal_repaid_by_seq=term_loan_principal_by_seq,
                term_loan_interest_by_seq=term_loan_interest_by_seq,
            )

            # 8. Execute Domain Validation Engine
            validation_issues = FinancialValidationEngine.audit_projection(
                statements=statements,
                appraisal=appraisal,
                funding_gap_paise=funding_gap_paise,
                min_acceptable_dscr=min_acceptable_dscr,
                max_acceptable_der=max_acceptable_der,
                min_acceptable_cr=min_acceptable_cr,
            )

            # 9. Execute Sensitivity Scenarios
            sensitivity_rows = self._calculate_sensitivity_analysis(
                statements=statements,
                initial_investment_paise=initial_investment_paise,
                discount_rate_pct=discount_rate_pct,
                term_loan_principal_by_seq=term_loan_principal_by_seq,
                term_loan_interest_by_seq=term_loan_interest_by_seq,
            )

            # 10. Persist Ratios and Validation Issues to Database
            self._persist_appraisal_results(
                session=session,
                run=run,
                periods=periods,
                appraisal=appraisal,
                validation_issues=validation_issues,
            )

            # 11. Build and Return AppraisalReportDTO
            return self._build_report_dto(
                run=run,
                period_headers=period_headers,
                appraisal=appraisal,
                validation_issues=validation_issues,
                sensitivity_rows=sensitivity_rows,
            )

    def _reconstruct_statements_from_lines(
        self,
        line_results: List[StatementLineResultModel],
        periods: List[ProjectPeriodModel],
    ) -> List[PeriodFinancialStatements]:
        """Reconstructs PeriodFinancialStatements from persisted line results."""
        by_period_and_code: Dict[uuid.UUID, Dict[str, int]] = {}
        for line in line_results:
            by_period_and_code.setdefault(line.period_id, {})[line.line_code] = line.amount_paise

        statements: List[PeriodFinancialStatements] = []
        for p in periods:
            c = by_period_and_code.get(p.id, {})

            # P&L
            gross_bill = c.get("GROSS_REVENUE", 0)
            out_gst = c.get("OUTPUT_GST", 0)
            net_rev = c.get("NET_REVENUE", 0)
            rm_cost = c.get("RAW_MATERIAL_COST", 0)
            other_dir = c.get("OTHER_DIRECT_COSTS", 0)
            total_dir = c.get("TOTAL_DIRECT_COSTS", rm_cost + other_dir)
            gp = c.get("GROSS_PROFIT", net_rev - total_dir)
            emp = c.get("EMPLOYEE_EXPENSES", 0)
            admin = c.get("ADMIN_EXPENSES", 0)
            selling = c.get("SELLING_EXPENSES", 0)
            total_opex = c.get("TOTAL_OPEX", emp + admin + selling)
            ebitda = c.get("EBITDA", gp - total_opex)
            dep = c.get("DEPRECIATION", 0)
            ebit = c.get("EBIT", ebitda - dep)
            fin = c.get("FINANCE_COSTS", 0)
            pbt = c.get("PBT", ebit - fin)
            tax = c.get("TAX_PROVISION", 0)
            pat = c.get("PAT", pbt - tax)

            # Cash Flow
            cf_op = c.get("CF_OP_PROFIT", pat + dep)
            cf_wc = c.get("CF_WC_CHANGES", 0)
            cf_net_op = c.get("CF_NET_OPERATING", cf_op + cf_wc)
            cf_capex = c.get("CF_CAPEX", 0)
            cf_net_inv = c.get("CF_NET_INVESTING", -cf_capex)
            cf_eq = c.get("CF_EQUITY_INTRODUCED", 0)
            cf_disb = c.get("CF_LOAN_DISBURSEMENT", 0)
            cf_rep = c.get("CF_LOAN_REPAYMENT", 0)
            cf_draw = c.get("CF_DRAWINGS", 0)
            cf_net_fin = c.get("CF_NET_FINANCING", 0)
            net_cf = c.get("NET_CASH_FLOW", 0)
            open_cash = c.get("OPENING_CASH", 0)
            close_cash = c.get("CLOSING_CASH", 0)

            # Balance Sheet
            fa_net = c.get("FIXED_ASSETS_NET", 0)
            inv_total = c.get("INVENTORY_TOTAL", 0)
            rec = c.get("TRADE_RECEIVABLES", 0)
            cash_bank = c.get("CASH_AND_BANK", close_cash)
            ca_total = c.get("TOTAL_CURRENT_ASSETS", 0)
            assets_total = c.get("TOTAL_ASSETS", fa_net + ca_total)

            nw = c.get("NET_WORTH", 0)
            lt_debt = c.get("LONG_TERM_DEBT", 0)
            st_wc = c.get("SHORT_TERM_WC_DEBT", 0)
            payables = c.get("TRADE_PAYABLES", 0)
            other_cl = c.get("OTHER_CURRENT_LIAB", 0)
            cl_total = c.get("TOTAL_CURRENT_LIAB", st_wc + payables + other_cl)
            liab_eq_total = c.get("TOTAL_LIABILITIES_EQUITY", nw + lt_debt + cl_total)

            bal_diff = assets_total - liab_eq_total

            statements.append(
                PeriodFinancialStatements(
                    period_id=p.id,
                    period_sequence=p.period_sequence,
                    period_label=p.period_label,
                    gross_billing_paise=gross_bill,
                    output_gst_paise=out_gst,
                    net_revenue_paise=net_rev,
                    raw_material_cost_paise=rm_cost,
                    other_direct_costs_paise=other_dir,
                    total_direct_costs_paise=total_dir,
                    gross_profit_paise=gp,
                    employee_benefit_expenses_paise=emp,
                    admin_and_other_expenses_paise=admin,
                    selling_and_distribution_expenses_paise=selling,
                    total_operating_expenses_paise=total_opex,
                    ebitda_paise=ebitda,
                    depreciation_paise=dep,
                    ebit_paise=ebit,
                    finance_costs_paise=fin,
                    profit_before_tax_paise=pbt,
                    tax_provision_paise=tax,
                    profit_after_tax_paise=pat,
                    cf_operating_profit_paise=cf_op,
                    cf_working_capital_changes_paise=cf_wc,
                    cf_net_operating_cash_flow_paise=cf_net_op,
                    cf_capital_expenditure_paise=cf_capex,
                    cf_net_investing_cash_flow_paise=cf_net_inv,
                    cf_equity_introduced_paise=cf_eq,
                    cf_loan_disbursements_paise=cf_disb,
                    cf_loan_repayments_paise=cf_rep,
                    cf_drawings_paise=cf_draw,
                    cf_net_financing_cash_flow_paise=cf_net_fin,
                    net_cash_flow_paise=net_cf,
                    opening_cash_paise=open_cash,
                    closing_cash_paise=close_cash,
                    bs_net_fixed_assets_paise=fa_net,
                    bs_raw_materials_paise=0,
                    bs_wip_paise=0,
                    bs_finished_goods_paise=0,
                    bs_total_inventory_paise=inv_total,
                    bs_trade_receivables_paise=rec,
                    bs_cash_and_bank_paise=cash_bank,
                    bs_deposits_and_other_assets_paise=0,
                    bs_total_current_assets_paise=ca_total,
                    bs_total_assets_paise=assets_total,
                    bs_net_worth_paise=nw,
                    bs_long_term_debt_paise=lt_debt,
                    bs_short_term_wc_debt_paise=st_wc,
                    bs_trade_payables_paise=payables,
                    bs_other_current_liabilities_paise=other_cl,
                    bs_total_current_liabilities_paise=cl_total,
                    bs_total_liabilities_and_equity_paise=liab_eq_total,
                    balance_difference_paise=bal_diff,
                )
            )
        return statements

    def _calculate_sensitivity_analysis(
        self,
        statements: List[PeriodFinancialStatements],
        initial_investment_paise: int,
        discount_rate_pct: Decimal,
        term_loan_principal_by_seq: Dict[int, int],
        term_loan_interest_by_seq: Dict[int, int],
    ) -> List[SensitivityRowDTO]:
        """Runs sensitivity variations (+/- 5%, 10%) on Selling Price, Raw Material Cost, and Sales Volume."""
        scenarios: List[SensitivityRowDTO] = []
        variations = [Decimal("-10.0"), Decimal("-5.0"), Decimal("5.0"), Decimal("10.0")]

        # 1. Base Case Reference
        base_appraisal = AppraisalEngine.calculate_project_appraisal(
            statements=statements,
            initial_investment_paise=initial_investment_paise,
            discount_rate_pct=discount_rate_pct,
            term_loan_principal_repaid_by_seq=term_loan_principal_by_seq,
            term_loan_interest_by_seq=term_loan_interest_by_seq,
        )
        base_avg_dscr = f"{base_appraisal.average_gross_dscr:.2f}x" if base_appraisal.average_gross_dscr else "N/A"
        base_irr = f"{base_appraisal.project_irr_pct:.2f}%" if base_appraisal.project_irr_pct else "N/A"
        base_avg_pat = (
            sum(s.profit_after_tax_paise for s in statements) / len(statements)
            if statements else 0
        )
        first_bep = (
            base_appraisal.period_ratios[0].break_even_capacity_pct
            if base_appraisal.period_ratios else Decimal("0.00")
        )

        scenarios.append(
            SensitivityRowDTO(
                parameter_name="Base Case (Current Projection)",
                variation_pct=Decimal("0.0"),
                average_dscr=base_avg_dscr,
                irr_pct=base_irr,
                avg_pat_rupees=paise_to_rupees(int(base_avg_pat)),
                first_year_bep_pct=first_bep,
            )
        )

        # 2. Selling Price Variation (+/- 5%, 10%)
        for v in variations:
            multiplier = Decimal("1.0") + (v / Decimal("100"))
            mod_stmts: List[PeriodFinancialStatements] = []
            for s in statements:
                adj_net_rev = int((Decimal(s.net_revenue_paise) * multiplier).quantize(Decimal("1"), rounding=ROUND_HALF_UP))
                rev_diff = adj_net_rev - s.net_revenue_paise
                # Rev diff flows directly into EBITDA and PBT
                adj_ebitda = s.ebitda_paise + rev_diff
                adj_pbt = s.profit_before_tax_paise + rev_diff
                tax_rate = Decimal("0.25")
                adj_tax = max(0, int((Decimal(adj_pbt) * tax_rate).quantize(Decimal("1"), rounding=ROUND_HALF_UP))) if adj_pbt > 0 else 0
                adj_pat = adj_pbt - adj_tax

                # Modified operating cash flow
                adj_net_op = s.cf_net_operating_cash_flow_paise + (adj_pat - s.profit_after_tax_paise)

                mod_stmts.append(
                    PeriodFinancialStatements(
                        period_id=s.period_id,
                        period_sequence=s.period_sequence,
                        period_label=s.period_label,
                        gross_billing_paise=int((Decimal(s.gross_billing_paise) * multiplier).quantize(Decimal("1"), rounding=ROUND_HALF_UP)),
                        output_gst_paise=s.output_gst_paise,
                        net_revenue_paise=adj_net_rev,
                        raw_material_cost_paise=s.raw_material_cost_paise,
                        other_direct_costs_paise=s.other_direct_costs_paise,
                        total_direct_costs_paise=s.total_direct_costs_paise,
                        gross_profit_paise=s.gross_profit_paise + rev_diff,
                        employee_benefit_expenses_paise=s.employee_benefit_expenses_paise,
                        admin_and_other_expenses_paise=s.admin_and_other_expenses_paise,
                        selling_and_distribution_expenses_paise=s.selling_and_distribution_expenses_paise,
                        total_operating_expenses_paise=s.total_operating_expenses_paise,
                        ebitda_paise=adj_ebitda,
                        depreciation_paise=s.depreciation_paise,
                        ebit_paise=s.ebit_paise + rev_diff,
                        finance_costs_paise=s.finance_costs_paise,
                        profit_before_tax_paise=adj_pbt,
                        tax_provision_paise=adj_tax,
                        profit_after_tax_paise=adj_pat,
                        cf_operating_profit_paise=adj_pat + s.depreciation_paise,
                        cf_working_capital_changes_paise=s.cf_working_capital_changes_paise,
                        cf_net_operating_cash_flow_paise=adj_net_op,
                        cf_capital_expenditure_paise=s.cf_capital_expenditure_paise,
                        cf_net_investing_cash_flow_paise=s.cf_net_investing_cash_flow_paise,
                        cf_equity_introduced_paise=s.cf_equity_introduced_paise,
                        cf_loan_disbursements_paise=s.cf_loan_disbursements_paise,
                        cf_loan_repayments_paise=s.cf_loan_repayments_paise,
                        cf_drawings_paise=s.cf_drawings_paise,
                        cf_net_financing_cash_flow_paise=s.cf_net_financing_cash_flow_paise,
                        net_cash_flow_paise=s.net_cash_flow_paise,
                        opening_cash_paise=s.opening_cash_paise,
                        closing_cash_paise=s.closing_cash_paise,
                        bs_net_fixed_assets_paise=s.bs_net_fixed_assets_paise,
                        bs_raw_materials_paise=s.bs_raw_materials_paise,
                        bs_wip_paise=s.bs_wip_paise,
                        bs_finished_goods_paise=s.bs_finished_goods_paise,
                        bs_total_inventory_paise=s.bs_total_inventory_paise,
                        bs_trade_receivables_paise=s.bs_trade_receivables_paise,
                        bs_cash_and_bank_paise=s.bs_cash_and_bank_paise,
                        bs_deposits_and_other_assets_paise=s.bs_deposits_and_other_assets_paise,
                        bs_total_current_assets_paise=s.bs_total_current_assets_paise,
                        bs_total_assets_paise=s.bs_total_assets_paise,
                        bs_net_worth_paise=s.bs_net_worth_paise,
                        bs_long_term_debt_paise=s.bs_long_term_debt_paise,
                        bs_short_term_wc_debt_paise=s.bs_short_term_wc_debt_paise,
                        bs_trade_payables_paise=s.bs_trade_payables_paise,
                        bs_other_current_liabilities_paise=s.bs_other_current_liabilities_paise,
                        bs_total_current_liabilities_paise=s.bs_total_current_liabilities_paise,
                        bs_total_liabilities_and_equity_paise=s.bs_total_liabilities_and_equity_paise,
                        balance_difference_paise=0,
                    )
                )

            mod_appr = AppraisalEngine.calculate_project_appraisal(
                statements=mod_stmts,
                initial_investment_paise=initial_investment_paise,
                discount_rate_pct=discount_rate_pct,
                term_loan_principal_repaid_by_seq=term_loan_principal_by_seq,
                term_loan_interest_by_seq=term_loan_interest_by_seq,
            )
            dscr_str = f"{mod_appr.average_gross_dscr:.2f}x" if mod_appr.average_gross_dscr else "N/A"
            irr_str = f"{mod_appr.project_irr_pct:.2f}%" if mod_appr.project_irr_pct else "N/A"
            avg_pat = sum(s.profit_after_tax_paise for s in mod_stmts) / len(mod_stmts) if mod_stmts else 0
            bep_pct = mod_appr.period_ratios[0].break_even_capacity_pct if mod_appr.period_ratios else Decimal("0.00")

            scenarios.append(
                SensitivityRowDTO(
                    parameter_name="Selling Price / Billing",
                    variation_pct=v,
                    average_dscr=dscr_str,
                    irr_pct=irr_str,
                    avg_pat_rupees=paise_to_rupees(int(avg_pat)),
                    first_year_bep_pct=bep_pct,
                )
            )

        # 3. Raw Material Cost Variation (+/- 5%, 10%)
        for v in variations:
            multiplier = Decimal("1.0") + (v / Decimal("100"))
            mod_stmts = []
            for s in statements:
                adj_rm = int((Decimal(s.raw_material_cost_paise) * multiplier).quantize(Decimal("1"), rounding=ROUND_HALF_UP))
                rm_diff = adj_rm - s.raw_material_cost_paise
                # Increase in RM cost reduces EBITDA and PBT
                adj_ebitda = s.ebitda_paise - rm_diff
                adj_pbt = s.profit_before_tax_paise - rm_diff
                tax_rate = Decimal("0.25")
                adj_tax = max(0, int((Decimal(adj_pbt) * tax_rate).quantize(Decimal("1"), rounding=ROUND_HALF_UP))) if adj_pbt > 0 else 0
                adj_pat = adj_pbt - adj_tax

                adj_net_op = s.cf_net_operating_cash_flow_paise + (adj_pat - s.profit_after_tax_paise)

                mod_stmts.append(
                    PeriodFinancialStatements(
                        period_id=s.period_id,
                        period_sequence=s.period_sequence,
                        period_label=s.period_label,
                        gross_billing_paise=s.gross_billing_paise,
                        output_gst_paise=s.output_gst_paise,
                        net_revenue_paise=s.net_revenue_paise,
                        raw_material_cost_paise=adj_rm,
                        other_direct_costs_paise=s.other_direct_costs_paise,
                        total_direct_costs_paise=adj_rm + s.other_direct_costs_paise,
                        gross_profit_paise=s.gross_profit_paise - rm_diff,
                        employee_benefit_expenses_paise=s.employee_benefit_expenses_paise,
                        admin_and_other_expenses_paise=s.admin_and_other_expenses_paise,
                        selling_and_distribution_expenses_paise=s.selling_and_distribution_expenses_paise,
                        total_operating_expenses_paise=s.total_operating_expenses_paise,
                        ebitda_paise=adj_ebitda,
                        depreciation_paise=s.depreciation_paise,
                        ebit_paise=s.ebit_paise - rm_diff,
                        finance_costs_paise=s.finance_costs_paise,
                        profit_before_tax_paise=adj_pbt,
                        tax_provision_paise=adj_tax,
                        profit_after_tax_paise=adj_pat,
                        cf_operating_profit_paise=adj_pat + s.depreciation_paise,
                        cf_working_capital_changes_paise=s.cf_working_capital_changes_paise,
                        cf_net_operating_cash_flow_paise=adj_net_op,
                        cf_capital_expenditure_paise=s.cf_capital_expenditure_paise,
                        cf_net_investing_cash_flow_paise=s.cf_net_investing_cash_flow_paise,
                        cf_equity_introduced_paise=s.cf_equity_introduced_paise,
                        cf_loan_disbursements_paise=s.cf_loan_disbursements_paise,
                        cf_loan_repayments_paise=s.cf_loan_repayments_paise,
                        cf_drawings_paise=s.cf_drawings_paise,
                        cf_net_financing_cash_flow_paise=s.cf_net_financing_cash_flow_paise,
                        net_cash_flow_paise=s.net_cash_flow_paise,
                        opening_cash_paise=s.opening_cash_paise,
                        closing_cash_paise=s.closing_cash_paise,
                        bs_net_fixed_assets_paise=s.bs_net_fixed_assets_paise,
                        bs_raw_materials_paise=s.bs_raw_materials_paise,
                        bs_wip_paise=s.bs_wip_paise,
                        bs_finished_goods_paise=s.bs_finished_goods_paise,
                        bs_total_inventory_paise=s.bs_total_inventory_paise,
                        bs_trade_receivables_paise=s.bs_trade_receivables_paise,
                        bs_cash_and_bank_paise=s.bs_cash_and_bank_paise,
                        bs_deposits_and_other_assets_paise=s.bs_deposits_and_other_assets_paise,
                        bs_total_current_assets_paise=s.bs_total_current_assets_paise,
                        bs_total_assets_paise=s.bs_total_assets_paise,
                        bs_net_worth_paise=s.bs_net_worth_paise,
                        bs_long_term_debt_paise=s.bs_long_term_debt_paise,
                        bs_short_term_wc_debt_paise=s.bs_short_term_wc_debt_paise,
                        bs_trade_payables_paise=s.bs_trade_payables_paise,
                        bs_other_current_liabilities_paise=s.bs_other_current_liabilities_paise,
                        bs_total_current_liabilities_paise=s.bs_total_current_liabilities_paise,
                        bs_total_liabilities_and_equity_paise=s.bs_total_liabilities_and_equity_paise,
                        balance_difference_paise=0,
                    )
                )

            mod_appr = AppraisalEngine.calculate_project_appraisal(
                statements=mod_stmts,
                initial_investment_paise=initial_investment_paise,
                discount_rate_pct=discount_rate_pct,
                term_loan_principal_repaid_by_seq=term_loan_principal_by_seq,
                term_loan_interest_by_seq=term_loan_interest_by_seq,
            )
            dscr_str = f"{mod_appr.average_gross_dscr:.2f}x" if mod_appr.average_gross_dscr else "N/A"
            irr_str = f"{mod_appr.project_irr_pct:.2f}%" if mod_appr.project_irr_pct else "N/A"
            avg_pat = sum(s.profit_after_tax_paise for s in mod_stmts) / len(mod_stmts) if mod_stmts else 0
            bep_pct = mod_appr.period_ratios[0].break_even_capacity_pct if mod_appr.period_ratios else Decimal("0.00")

            scenarios.append(
                SensitivityRowDTO(
                    parameter_name="Raw Material Cost",
                    variation_pct=v,
                    average_dscr=dscr_str,
                    irr_pct=irr_str,
                    avg_pat_rupees=paise_to_rupees(int(avg_pat)),
                    first_year_bep_pct=bep_pct,
                )
            )

        return scenarios

    def _persist_appraisal_results(
        self,
        session,
        run: CalculationRunModel,
        periods: List[ProjectPeriodModel],
        appraisal: ProjectAppraisalSummary,
        validation_issues: List[ValidationIssue],
    ) -> None:
        """Saves ratio results and validation issues to database, updating run validation counts."""
        calc_repo = CalculationRepository(session)

        # 1. Clear any prior ratio and validation results for this run
        old_ratios = calc_repo.get_ratio_results_for_run(run.id)
        for r in old_ratios:
            session.delete(r)

        old_issues = calc_repo.get_validation_results_for_run(run.id)
        for i in old_issues:
            session.delete(i)
        session.flush()

        # 2. Persist Ratio Results
        ratio_models: List[RatioResultModel] = []
        seq_to_period_id = {p.period_sequence: p.id for p in periods}

        for pr in appraisal.period_ratios:
            pid = seq_to_period_id.get(pr.period_sequence)

            # Define rows to persist per period
            rows = [
                ("CURRENT_RATIO", str(pr.current_ratio) if pr.current_ratio else None, "x", "STANDARD", "Min 1.33x"),
                ("QUICK_RATIO", str(pr.quick_ratio) if pr.quick_ratio else None, "x", "STANDARD", "Min 1.00x"),
                ("DEBT_EQUITY", str(pr.debt_equity_ratio) if pr.debt_equity_ratio else None, "x", "TOTAL_DEBT", "Max 3.00x"),
                ("GROSS_DSCR", str(pr.gross_dscr) if pr.gross_dscr else None, "x", "GROSS_CASH_FLOW", "Min 1.25x"),
                ("NET_CFADS_DSCR", str(pr.net_cfads_dscr) if pr.net_cfads_dscr else None, "x", "NET_CFADS", "Min 1.25x"),
                ("INTEREST_COVERAGE", str(pr.interest_coverage) if pr.interest_coverage else None, "x", "EBITDA_INTEREST", "Min 2.00x"),
                ("EBITDA_MARGIN", str(pr.ebitda_margin_pct), "%", "EBITDA_REVENUE", "Benchmark 10-25%"),
                ("PAT_MARGIN", str(pr.pat_margin_pct), "%", "PAT_REVENUE", "Benchmark 5-15%"),
                ("ROCE", str(pr.roce_pct) if pr.roce_pct else None, "%", "EBIT_CAPITAL_EMPLOYED", "Min 12.0%"),
                ("RONW", str(pr.ronw_pct) if pr.ronw_pct else None, "%", "PAT_NET_WORTH", "Min 15.0%"),
                ("BEP_CAPACITY_PCT", str(pr.break_even_capacity_pct), "%", "BREAK_EVEN_SALES", "Max 60%"),
                ("MARGIN_OF_SAFETY_PCT", str(pr.margin_of_safety_pct), "%", "MOS_REVENUE", "Min 30%"),
            ]
            for code, val, unit, method, benchmark in rows:
                ratio_models.append(
                    RatioResultModel(
                        id=uuid.uuid4(),
                        calculation_run_id=run.id,
                        period_id=pid,
                        ratio_code=code,
                        ratio_value_text=val,
                        unit_code=unit,
                        method_code=method,
                        benchmark_note=benchmark,
                    )
                )

        # Lifetime / Project-level ratio records (period_id = None)
        lifetime_rows = [
            ("NPV", str(paise_to_rupees(appraisal.npv_paise)), "₹", "NPV_DISCOUNTED", f"At {appraisal.discount_rate_pct}%"),
            ("PROJECT_IRR", str(appraisal.project_irr_pct) if appraisal.project_irr_pct else None, "%", "EXACT_BISECTION", "Must exceed WACC/Cost of Debt"),
            ("PAYBACK_YEARS", str(appraisal.simple_payback_years), "years", "SIMPLE_PAYBACK", "Within loan tenure"),
            ("PROFITABILITY_INDEX", str(appraisal.profitability_index) if appraisal.profitability_index else None, "x", "PI", "Min 1.0x"),
            ("AVERAGE_GROSS_DSCR", str(appraisal.average_gross_dscr) if appraisal.average_gross_dscr else None, "x", "ARITHMETIC_MEAN", "Min 1.25x"),
            ("CUMULATIVE_DSCR", str(appraisal.cumulative_gross_dscr) if appraisal.cumulative_gross_dscr else None, "x", "CUMULATIVE_SUM", "Min 1.25x"),
        ]
        for code, val, unit, method, benchmark in lifetime_rows:
            ratio_models.append(
                RatioResultModel(
                    id=uuid.uuid4(),
                    calculation_run_id=run.id,
                    period_id=None,
                    ratio_code=code,
                    ratio_value_text=val,
                    unit_code=unit,
                    method_code=method,
                    benchmark_note=benchmark,
                )
            )

        calc_repo.save_ratio_results(ratio_models)

        # 3. Persist Validation Results
        val_models: List[ValidationResultModel] = []
        err_count = 0
        warn_count = 0

        for issue in validation_issues:
            if issue.severity == ValidationSeverity.ERROR:
                err_count += 1
            elif issue.severity == ValidationSeverity.WARNING:
                warn_count += 1

            val_models.append(
                ValidationResultModel(
                    id=uuid.uuid4(),
                    calculation_run_id=run.id,
                    rule_code=issue.rule_code,
                    severity=issue.severity.value,
                    scope_code=issue.scope_code,
                    message=issue.message,
                    expected_value_text=issue.expected_value_text,
                    actual_value_text=issue.actual_value_text,
                    resolution_status="OPEN",
                )
            )

        calc_repo.save_validation_results(val_models)

        # 4. Update Run Validation Counts and Run Status
        status = "SUCCESS"
        if err_count > 0:
            status = "COMPLETED_WITH_ERRORS"
        elif warn_count > 0:
            status = "COMPLETED_WITH_WARNINGS"

        calc_repo.update_run_validation_counts(
            run_id=run.id,
            error_count=err_count,
            warning_count=warn_count,
            run_status=status,
        )

    def _build_report_dto(
        self,
        run: CalculationRunModel,
        period_headers: List[str],
        appraisal: ProjectAppraisalSummary,
        validation_issues: List[ValidationIssue],
        sensitivity_rows: List[SensitivityRowDTO],
    ) -> AppraisalReportDTO:
        """Constructs the comprehensive AppraisalReportDTO for GUI presentation and reporting."""
        # 1. Lifetime Returns
        lifetime_dto = ProjectLifetimeReturnsDTO(
            initial_investment_rupees=paise_to_rupees(appraisal.initial_investment_paise),
            discount_rate_pct=appraisal.discount_rate_pct,
            npv_rupees=paise_to_rupees(appraisal.npv_paise),
            irr_pct=appraisal.project_irr_pct,
            payback_years=appraisal.simple_payback_years,
            profitability_index=appraisal.profitability_index,
            average_gross_dscr=appraisal.average_gross_dscr,
            average_net_cfads_dscr=appraisal.average_net_cfads_dscr,
            cumulative_dscr=appraisal.cumulative_gross_dscr,
        )

        # 2. Ratio Rows
        metric_configs = [
            # Liquidity
            ("CURRENT_RATIO", "Current Ratio", "LIQUIDITY", "x", ">= 1.33x", lambda r: f"{r.current_ratio:.2f}x" if r.current_ratio else "N/A", lambda r: (r.current_ratio >= Decimal("1.33")) if r.current_ratio else True),
            ("QUICK_RATIO", "Quick Ratio (Acid Test)", "LIQUIDITY", "x", ">= 1.00x", lambda r: f"{r.quick_ratio:.2f}x" if r.quick_ratio else "N/A", lambda r: (r.quick_ratio >= Decimal("1.00")) if r.quick_ratio else True),
            # Coverage / DSCR
            ("GROSS_DSCR", "Gross Cash Flow DSCR", "COVERAGE", "x", ">= 1.25x", lambda r: f"{r.gross_dscr:.2f}x" if r.gross_dscr else "N/A", lambda r: (r.gross_dscr >= Decimal("1.25")) if r.gross_dscr else True),
            ("NET_CFADS_DSCR", "Net Operating CFADS DSCR", "COVERAGE", "x", ">= 1.25x", lambda r: f"{r.net_cfads_dscr:.2f}x" if r.net_cfads_dscr else "N/A", lambda r: (r.net_cfads_dscr >= Decimal("1.25")) if r.net_cfads_dscr else True),
            ("INTEREST_COVERAGE", "Interest Coverage Ratio (ICR)", "COVERAGE", "x", ">= 2.00x", lambda r: f"{r.interest_coverage:.2f}x" if r.interest_coverage else "N/A", lambda r: (r.interest_coverage >= Decimal("2.00")) if r.interest_coverage else True),
            # Solvency / Leverage
            ("DEBT_EQUITY", "Debt-Equity Ratio (Total Debt / Net Worth)", "LEVERAGE", "x", "<= 3.00x", lambda r: f"{r.debt_equity_ratio:.2f}x" if r.debt_equity_ratio else "N/A", lambda r: (r.debt_equity_ratio <= Decimal("3.00")) if r.debt_equity_ratio else True),
            ("TERM_DEBT_EQUITY", "Term Debt-Equity Ratio", "LEVERAGE", "x", "<= 2.00x", lambda r: f"{r.term_debt_equity_ratio:.2f}x" if r.term_debt_equity_ratio else "N/A", lambda r: (r.term_debt_equity_ratio <= Decimal("2.00")) if r.term_debt_equity_ratio else True),
            # Profitability
            ("GROSS_PROFIT_MARGIN", "Gross Profit Margin", "PROFITABILITY", "%", "Benchmark", lambda r: f"{r.gross_profit_margin_pct:.2f}%", lambda r: True),
            ("EBITDA_MARGIN", "Operating EBITDA Margin", "PROFITABILITY", "%", "10% - 25%", lambda r: f"{r.ebitda_margin_pct:.2f}%", lambda r: r.ebitda_margin_pct >= Decimal("10.0")),
            ("PAT_MARGIN", "Net Profit (PAT) Margin", "PROFITABILITY", "%", "5% - 15%", lambda r: f"{r.pat_margin_pct:.2f}%", lambda r: r.pat_margin_pct >= Decimal("5.0")),
            ("ROCE", "Return on Capital Employed (ROCE)", "PROFITABILITY", "%", ">= 12.0%", lambda r: f"{r.roce_pct:.2f}%" if r.roce_pct else "N/A", lambda r: (r.roce_pct >= Decimal("12.0")) if r.roce_pct else True),
            ("RONW", "Return on Net Worth (RONW)", "PROFITABILITY", "%", ">= 15.0%", lambda r: f"{r.ronw_pct:.2f}%" if r.ronw_pct else "N/A", lambda r: (r.ronw_pct >= Decimal("15.0")) if r.ronw_pct else True),
            # Break-Even
            ("FIXED_COSTS", "Total Fixed Costs", "BREAK_EVEN", "₹", "Schedules", lambda r: format_inr(paise_to_rupees(r.fixed_costs_paise)), lambda r: True),
            ("VARIABLE_COSTS", "Total Variable Costs", "BREAK_EVEN", "₹", "Schedules", lambda r: format_inr(paise_to_rupees(r.variable_costs_paise)), lambda r: True),
            ("CONTRIBUTION_MARGIN", "Contribution Margin %", "BREAK_EVEN", "%", "Higher is better", lambda r: f"{r.contribution_margin_pct:.2f}%", lambda r: True),
            ("BEP_SALES", "Break-Even Sales (₹)", "BREAK_EVEN", "₹", "Coverage", lambda r: format_inr(paise_to_rupees(r.break_even_sales_paise)), lambda r: True),
            ("BEP_CAPACITY", "Break-Even Capacity Utilization %", "BREAK_EVEN", "%", "<= 60.0%", lambda r: f"{r.break_even_capacity_pct:.2f}%", lambda r: r.break_even_capacity_pct <= Decimal("60.0")),
            ("CASH_BEP_SALES", "Cash Break-Even Sales (₹)", "BREAK_EVEN", "₹", "Excl. Dep", lambda r: format_inr(paise_to_rupees(r.cash_break_even_sales_paise)), lambda r: True),
            ("MARGIN_OF_SAFETY", "Margin of Safety %", "BREAK_EVEN", "%", ">= 30.0%", lambda r: f"{r.margin_of_safety_pct:.2f}%", lambda r: r.margin_of_safety_pct >= Decimal("30.0")),
        ]

        ratio_rows: List[RatioMetricRowDTO] = []
        for code, name, cat, unit, bench, fmt_fn, pass_fn in metric_configs:
            period_vals: Dict[int, str] = {}
            row_status = "PASS"
            for pr in appraisal.period_ratios:
                period_vals[pr.period_sequence] = fmt_fn(pr)
                if not pass_fn(pr):
                    row_status = "WARNING"

            ratio_rows.append(
                RatioMetricRowDTO(
                    metric_code=code,
                    metric_name=name,
                    category=cat,
                    unit=unit,
                    benchmark_text=bench,
                    period_values=period_vals,
                    status=row_status,
                )
            )

        # 3. Validation Issues DTOs
        issue_dtos: List[ValidationIssueDTO] = []
        err_c = 0
        warn_c = 0
        for vi in validation_issues:
            if vi.severity == ValidationSeverity.ERROR:
                err_c += 1
            elif vi.severity == ValidationSeverity.WARNING:
                warn_c += 1

            issue_dtos.append(
                ValidationIssueDTO(
                    rule_code=vi.rule_code,
                    severity=vi.severity.value,
                    scope_code=vi.scope_code,
                    message=vi.message,
                    period_sequence=vi.period_sequence,
                    expected_value=vi.expected_value_text,
                    actual_value=vi.actual_value_text,
                    is_overridable=vi.is_overridable,
                    suggested_action=vi.suggested_action,
                )
            )

        return AppraisalReportDTO(
            calculation_run_id=run.id,
            run_number=run.run_number,
            period_headers=period_headers,
            lifetime_returns=lifetime_dto,
            ratio_rows=ratio_rows,
            validation_issues=issue_dtos,
            sensitivity_rows=sensitivity_rows,
            error_count=err_c,
            warning_count=warn_c,
        )
