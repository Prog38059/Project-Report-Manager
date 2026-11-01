"""Application service for orchestrating Financial Engine Projections and Statements."""

from datetime import datetime, timezone
from decimal import Decimal
import hashlib
import json
from typing import Dict, List, Optional
import uuid

from sqlalchemy import select

from app.application.dtos.financial_statements_dto import (
    AssetScheduleRowDTO,
    CalculationRunDTO,
    HorizontalStatementRowDTO,
    LoanScheduleRowDTO,
    StatementsTableDTO,
)
from app.common.exceptions import ValidationError
from app.common.money import paise_to_rupees, rupees_to_paise
from app.common.types import ConstitutionCode
from app.domain.financial.depreciation import AssetAdditionInput, AssetScheduleCalculator
from app.domain.financial.loan_engine import LoanAmortizationCalculator
from app.domain.financial.statement_pipeline import PeriodFinancialStatements, StatementPipeline
from app.domain.financial.working_capital import WorkingCapitalAssumptions
from app.infrastructure.database.connection import DatabaseManager
from app.infrastructure.database.models.calculation_model import (
    AssetScheduleResultModel,
    CalculationRunModel,
    CalculationRunSnapshotModel,
    LoanScheduleResultModel,
    StatementLineDefinitionModel,
    StatementLineResultModel,
)
from app.infrastructure.database.models.entity_model import EntityModel
from app.infrastructure.database.models.expense_model import ExpenseForecastModel, ExpenseHeadModel
from app.infrastructure.database.models.funding_model import FundingHeadModel, FundingSourceModel
from app.infrastructure.database.models.project_cost_model import ProjectCostItemModel
from app.infrastructure.database.models.project_model import ProjectModel, ProjectPeriodModel, ProjectScenarioModel
from app.infrastructure.database.models.revenue_model import RevenueForecastModel, RevenueStreamModel
from app.infrastructure.repositories.calculation_repository import CalculationRepository


class FinancialEngineService:
    def __init__(self, db_manager: DatabaseManager) -> None:
        self.db_manager = db_manager

    def execute_projection(
        self,
        scenario_id: uuid.UUID,
        prepared_by_label: str = "System",
        engine_version: str = "1.0.0",
        wc_assumptions: Optional[WorkingCapitalAssumptions] = None,
    ) -> CalculationRunDTO:
        """Executes full multi-year financial projection, creates snapshot, and saves run results."""
        if wc_assumptions is None:
            wc_assumptions = WorkingCapitalAssumptions()

        with self.db_manager.session_scope() as session:
            calc_repo = CalculationRepository(session)

            # 1. Fetch Scenario, Project, and Entity
            scenario = session.get(ProjectScenarioModel, scenario_id)
            if not scenario:
                raise ValidationError(f"Project Scenario with id '{scenario_id}' not found.")

            project = session.get(ProjectModel, scenario.project_id)
            if not project:
                raise ValidationError(f"Project with id '{scenario.project_id}' not found.")

            entity = session.get(EntityModel, project.entity_id)
            constitution_code = ConstitutionCode(entity.constitution_code) if entity else ConstitutionCode.PRIVATE_LIMITED

            # 2. Fetch Project Periods
            periods_stmt = (
                select(ProjectPeriodModel)
                .where(ProjectPeriodModel.project_id == project.id)
                .order_by(ProjectPeriodModel.period_sequence)
            )
            period_models = list(session.execute(periods_stmt).scalars().all())
            if not period_models:
                raise ValidationError(f"No financial projection periods defined for project '{project.id}'.")

            period_defs = [
                {"id": p.id, "sequence": p.period_sequence, "label": p.period_label}
                for p in period_models
            ]
            period_seq_to_id = {p.period_sequence: p.id for p in period_models}
            period_seq_to_label = {p.period_sequence: p.period_label for p in period_models}

            # 3. Project Capex / Costs
            costs_stmt = select(ProjectCostItemModel).where(
                ProjectCostItemModel.scenario_id == scenario_id,
                ProjectCostItemModel.is_active.is_(True),
            )
            cost_items = list(session.execute(costs_stmt).scalars().all())
            total_capex_paise = sum(item.capitalised_amount_paise for item in cost_items)
            # Default capex to period 1
            total_capex_by_period = {p.period_sequence: 0 for p in period_models}
            if period_models:
                total_capex_by_period[1] = total_capex_paise

            # 4. Funding Sources
            funding_stmt = (
                select(FundingSourceModel, FundingHeadModel)
                .join(FundingHeadModel, FundingSourceModel.funding_head_id == FundingHeadModel.id)
                .where(
                    FundingSourceModel.scenario_id == scenario_id,
                    FundingSourceModel.is_active.is_(True),
                )
            )
            funding_rows = session.execute(funding_stmt).all()

            term_loan_sanctioned_paise = 0
            term_loan_interest_rate_pct = Decimal("11.5")
            equity_introduced_by_period = {p.period_sequence: 0 for p in period_models}

            for source, head in funding_rows:
                cat = head.funding_category.upper()
                if "DEBT" in cat or "LOAN" in cat:
                    term_loan_sanctioned_paise += source.amount_paise
                    if source.terms_note and "%" in source.terms_note:
                        try:
                            # Try parsing interest rate from terms e.g. "11.5% interest"
                            rate_str = source.terms_note.split("%")[0].split()[-1]
                            term_loan_interest_rate_pct = Decimal(rate_str)
                        except Exception:
                            pass
                elif "EQUITY" in cat or "PROMOTER" in cat:
                    equity_introduced_by_period[1] += source.amount_paise

            # 5. Revenue Forecasts
            rev_stmt = (
                select(RevenueForecastModel, RevenueStreamModel)
                .join(RevenueStreamModel, RevenueForecastModel.revenue_stream_id == RevenueStreamModel.id)
                .where(
                    RevenueStreamModel.scenario_id == scenario_id,
                    RevenueForecastModel.is_active.is_(True),
                )
            )
            rev_rows = session.execute(rev_stmt).all()
            net_revenue_by_period = {p.period_sequence: 0 for p in period_models}
            for forecast, stream in rev_rows:
                p_model = session.get(ProjectPeriodModel, forecast.period_id)
                if p_model:
                    # Calculate or use gross billing override
                    amount = forecast.gross_billing_override_paise or 0
                    if not amount and forecast.units_decimal_text and forecast.price_per_unit_decimal_text:
                        units = Decimal(forecast.units_decimal_text)
                        price = Decimal(forecast.price_per_unit_decimal_text)
                        amount = rupees_to_paise(units * price)
                    net_revenue_by_period[p_model.period_sequence] = (
                        net_revenue_by_period.get(p_model.period_sequence, 0) + amount
                    )

            # If no revenues configured, provide minimal positive values based on capex for demonstration
            if all(v == 0 for v in net_revenue_by_period.values()):
                base_rev = max(500000000, total_capex_paise)  # 50L or capex
                for p in period_models:
                    net_revenue_by_period[p.period_sequence] = int(base_rev * (1 + 0.10 * (p.period_sequence - 1)))

            # 6. Expenses by Period
            exp_stmt = (
                select(ExpenseForecastModel, ExpenseHeadModel)
                .join(ExpenseHeadModel, ExpenseForecastModel.expense_head_id == ExpenseHeadModel.id)
                .where(
                    ExpenseForecastModel.scenario_id == scenario_id,
                    ExpenseForecastModel.is_active.is_(True),
                )
            )
            exp_rows = session.execute(exp_stmt).all()

            material_cost_by_period = {p.period_sequence: 0 for p in period_models}
            other_direct_cost_by_period = {p.period_sequence: 0 for p in period_models}
            employee_cost_by_period = {p.period_sequence: 0 for p in period_models}
            admin_cost_by_period = {p.period_sequence: 0 for p in period_models}
            selling_cost_by_period = {p.period_sequence: 0 for p in period_models}

            for forecast, head in exp_rows:
                p_model = session.get(ProjectPeriodModel, forecast.period_id)
                if p_model:
                    seq = p_model.period_sequence
                    cat = head.category_code.upper()
                    amt = forecast.forecast_amount_paise
                    if "RAW_MATERIAL" in cat or "MATERIAL" in cat:
                        material_cost_by_period[seq] += amt
                    elif "DIRECT" in cat or "POWER" in cat or "FUEL" in cat:
                        other_direct_cost_by_period[seq] += amt
                    elif "EMPLOYEE" in cat or "SALARY" in cat or "WAGE" in cat:
                        employee_cost_by_period[seq] += amt
                    elif "SELLING" in cat or "DISTRIBUTION" in cat:
                        selling_cost_by_period[seq] += amt
                    else:
                        admin_cost_by_period[seq] += amt

            # If expenses are 0, estimate standard operational percentages from revenue
            for seq, rev in net_revenue_by_period.items():
                if material_cost_by_period[seq] == 0:
                    material_cost_by_period[seq] = int(rev * 0.40)
                if other_direct_cost_by_period[seq] == 0:
                    other_direct_cost_by_period[seq] = int(rev * 0.05)
                if employee_cost_by_period[seq] == 0:
                    employee_cost_by_period[seq] = int(rev * 0.15)
                if admin_cost_by_period[seq] == 0:
                    admin_cost_by_period[seq] = int(rev * 0.05)
                if selling_cost_by_period[seq] == 0:
                    selling_cost_by_period[seq] = int(rev * 0.03)

            # 7. Create Canonical Snapshot & Hash
            snapshot_dict = {
                "project_id": str(project.id),
                "scenario_id": str(scenario.id),
                "constitution_code": constitution_code.value,
                "periods": period_defs,
                "capex_by_period": total_capex_by_period,
                "term_loan_sanctioned_paise": term_loan_sanctioned_paise,
                "term_loan_interest_rate_pct": str(term_loan_interest_rate_pct),
                "equity_introduced_by_period": equity_introduced_by_period,
                "net_revenue_by_period": net_revenue_by_period,
                "material_cost_by_period": material_cost_by_period,
                "other_direct_cost_by_period": other_direct_cost_by_period,
                "employee_cost_by_period": employee_cost_by_period,
                "admin_cost_by_period": admin_cost_by_period,
                "selling_cost_by_period": selling_cost_by_period,
                "wc_assumptions": {
                    "rm_holding_days": str(wc_assumptions.rm_holding_days),
                    "wip_holding_days": str(wc_assumptions.wip_holding_days),
                    "fg_holding_days": str(wc_assumptions.fg_holding_days),
                    "debtor_collection_days": str(wc_assumptions.debtor_collection_days),
                    "creditor_payment_days": str(wc_assumptions.creditor_payment_days),
                    "bank_margin_pct": str(wc_assumptions.bank_margin_pct),
                },
            }
            snapshot_json = json.dumps(snapshot_dict, sort_keys=True, default=str)
            input_hash = hashlib.sha256(snapshot_json.encode("utf-8")).hexdigest()

            # 8. Run Statement Pipeline
            statements = StatementPipeline.run_projection(
                period_definitions=period_defs,
                constitution_code=constitution_code,
                net_revenue_by_period=net_revenue_by_period,
                material_cost_by_period=material_cost_by_period,
                other_direct_cost_by_period=other_direct_cost_by_period,
                employee_cost_by_period=employee_cost_by_period,
                admin_cost_by_period=admin_cost_by_period,
                selling_cost_by_period=selling_cost_by_period,
                total_capex_by_period=total_capex_by_period,
                asset_useful_life_years=Decimal("10"),
                promoter_equity_introduced_by_period=equity_introduced_by_period,
                term_loan_sanctioned_paise=term_loan_sanctioned_paise,
                term_loan_interest_rate_pct=term_loan_interest_rate_pct,
                term_loan_tenure_months=84,
                term_loan_moratorium_months=0,
                wc_assumptions=wc_assumptions,
            )

            # 9. Persist Calculation Run, Snapshot, Statement Lines, and Schedules
            run = calc_repo.create_calculation_run(
                project_id=project.id,
                scenario_id=scenario.id,
                engine_version=engine_version,
                input_hash=input_hash,
                run_status="SUCCESS",
                prepared_by_label=prepared_by_label,
                summary_note=f"Automated 7-year projection for {project.project_name}",
            )

            calc_repo.save_snapshot(
                calculation_run_id=run.id,
                input_snapshot_json=snapshot_json,
                input_hash=input_hash,
                snapshot_schema_version="1.0",
            )

            # Persist Statement Lines
            line_models: List[StatementLineResultModel] = []
            for stmt in statements:
                pid = stmt.period_id

                # P&L items
                pl_items = [
                    ("GROSS_REVENUE", "Gross Billing / Revenue from Operations", stmt.gross_billing_paise),
                    ("OUTPUT_GST", "Less: Output GST", stmt.output_gst_paise),
                    ("NET_REVENUE", "Net Revenue from Operations", stmt.net_revenue_paise),
                    ("RAW_MATERIAL_COST", "Raw Material Consumed", stmt.raw_material_cost_paise),
                    ("OTHER_DIRECT_COSTS", "Other Direct Costs", stmt.other_direct_costs_paise),
                    ("TOTAL_DIRECT_COSTS", "Total Direct Costs", stmt.total_direct_costs_paise),
                    ("GROSS_PROFIT", "Gross Profit", stmt.gross_profit_paise),
                    ("EMPLOYEE_EXPENSES", "Employee Benefit Expenses", stmt.employee_benefit_expenses_paise),
                    ("ADMIN_EXPENSES", "Administrative & General Expenses", stmt.admin_and_other_expenses_paise),
                    ("SELLING_EXPENSES", "Selling & Distribution Expenses", stmt.selling_and_distribution_expenses_paise),
                    ("TOTAL_OPEX", "Total Operating Expenses", stmt.total_operating_expenses_paise),
                    ("EBITDA", "Operating Profit (EBITDA)", stmt.ebitda_paise),
                    ("DEPRECIATION", "Depreciation & Amortisation", stmt.depreciation_paise),
                    ("EBIT", "Earnings Before Interest & Tax (EBIT)", stmt.ebit_paise),
                    ("FINANCE_COSTS", "Finance Costs / Interest", stmt.finance_costs_paise),
                    ("PBT", "Profit Before Tax (PBT)", stmt.profit_before_tax_paise),
                    ("TAX_PROVISION", "Provision for Income Tax", stmt.tax_provision_paise),
                    ("PAT", "Profit After Tax (PAT)", stmt.profit_after_tax_paise),
                ]
                for code, label, amt in pl_items:
                    line_models.append(
                        StatementLineResultModel(
                            id=uuid.uuid4(),
                            calculation_run_id=run.id,
                            period_id=pid,
                            statement_type="PL",
                            line_code=code,
                            line_label_snapshot=label,
                            amount_paise=amt,
                        )
                    )

                # Balance Sheet items
                bs_items = [
                    ("FIXED_ASSETS_NET", "Property, Plant & Equipment (Net)", stmt.bs_net_fixed_assets_paise),
                    ("INVENTORY_TOTAL", "Inventories (RM, WIP, FG)", stmt.bs_total_inventory_paise),
                    ("TRADE_RECEIVABLES", "Trade Receivables (Debtors)", stmt.bs_trade_receivables_paise),
                    ("CASH_AND_BANK", "Cash & Bank Balances", stmt.bs_cash_and_bank_paise),
                    ("TOTAL_CURRENT_ASSETS", "Total Current Assets", stmt.bs_total_current_assets_paise),
                    ("TOTAL_ASSETS", "Total Assets", stmt.bs_total_assets_paise),
                    ("NET_WORTH", "Capital / Equity & Reserves", stmt.bs_net_worth_paise),
                    ("LONG_TERM_DEBT", "Term Borrowings (Secured Loans)", stmt.bs_long_term_debt_paise),
                    ("SHORT_TERM_WC_DEBT", "Short-Term Bank Borrowings (CC/OD)", stmt.bs_short_term_wc_debt_paise),
                    ("TRADE_PAYABLES", "Trade Payables (Creditors)", stmt.bs_trade_payables_paise),
                    ("OTHER_CURRENT_LIAB", "Other Current Liabilities", stmt.bs_other_current_liabilities_paise),
                    ("TOTAL_CURRENT_LIAB", "Total Current Liabilities", stmt.bs_total_current_liabilities_paise),
                    ("TOTAL_LIABILITIES_EQUITY", "Total Liabilities & Equity", stmt.bs_total_liabilities_and_equity_paise),
                ]
                for code, label, amt in bs_items:
                    line_models.append(
                        StatementLineResultModel(
                            id=uuid.uuid4(),
                            calculation_run_id=run.id,
                            period_id=pid,
                            statement_type="BS",
                            line_code=code,
                            line_label_snapshot=label,
                            amount_paise=amt,
                        )
                    )

                # Cash Flow items
                cf_items = [
                    ("CF_OP_PROFIT", "Operating Cash Flow before WC (PAT + Dep)", stmt.cf_operating_profit_paise),
                    ("CF_WC_CHANGES", "Working Capital Adjustments", stmt.cf_working_capital_changes_paise),
                    ("CF_NET_OPERATING", "Net Cash from Operating Activities", stmt.cf_net_operating_cash_flow_paise),
                    ("CF_CAPEX", "Purchase of Fixed Assets (Capex)", stmt.cf_capital_expenditure_paise),
                    ("CF_NET_INVESTING", "Net Cash used in Investing Activities", stmt.cf_net_investing_cash_flow_paise),
                    ("CF_EQUITY_INTRODUCED", "Capital / Equity Introduced", stmt.cf_equity_introduced_paise),
                    ("CF_LOAN_DISBURSEMENT", "Term Loan Disbursements", stmt.cf_loan_disbursements_paise),
                    ("CF_LOAN_REPAYMENT", "Repayment of Term Borrowings", stmt.cf_loan_repayments_paise),
                    ("CF_DRAWINGS", "Drawings / Dividends Paid", stmt.cf_drawings_paise),
                    ("CF_NET_FINANCING", "Net Cash from Financing Activities", stmt.cf_net_financing_cash_flow_paise),
                    ("NET_CASH_FLOW", "Net Increase / (Decrease) in Cash", stmt.net_cash_flow_paise),
                    ("OPENING_CASH", "Opening Cash & Bank Balances", stmt.opening_cash_paise),
                    ("CLOSING_CASH", "Closing Cash & Bank Balances", stmt.closing_cash_paise),
                ]
                for code, label, amt in cf_items:
                    line_models.append(
                        StatementLineResultModel(
                            id=uuid.uuid4(),
                            calculation_run_id=run.id,
                            period_id=pid,
                            statement_type="CASH_FLOW",
                            line_code=code,
                            line_label_snapshot=label,
                            amount_paise=amt,
                        )
                    )

            calc_repo.save_statement_results(line_models)

            # Persist Monthly Loan Schedule
            monthly_loan_sched = LoanAmortizationCalculator.calculate_monthly_schedule(
                sanctioned_amount_paise=term_loan_sanctioned_paise,
                annual_rate_pct=term_loan_interest_rate_pct,
                tenure_months=84,
                moratorium_months=0,
            )
            loan_result_models = [
                LoanScheduleResultModel(
                    id=uuid.uuid4(),
                    calculation_run_id=run.id,
                    loan_facility_id=None,
                    installment_number=inst.month_number,
                    due_date=datetime.now(timezone.utc).date(),
                    opening_balance_paise=inst.opening_principal_paise,
                    disbursement_paise=inst.disbursement_paise,
                    payment_paise=inst.total_installment_paise,
                    interest_paise=inst.interest_paise,
                    principal_paise=inst.principal_paise,
                    closing_balance_paise=inst.closing_principal_paise,
                )
                for inst in monthly_loan_sched
            ]
            calc_repo.save_loan_results(loan_result_models)

            # Persist Asset Schedule
            asset_additions = [
                AssetAdditionInput(
                    period_id=p["id"],
                    period_sequence=p["sequence"],
                    gross_addition_paise=total_capex_by_period.get(p["sequence"], 0),
                    useful_life_years=Decimal("10"),
                )
                for p in period_defs
            ]
            asset_results = AssetScheduleCalculator.calculate_schedule(asset_additions)
            asset_result_models = [
                AssetScheduleResultModel(
                    id=uuid.uuid4(),
                    calculation_run_id=run.id,
                    asset_item_id=None,
                    period_id=res.period_id,
                    opening_gross_paise=res.book_opening_gross_paise,
                    additions_paise=res.book_additions_paise,
                    disposals_paise=0,
                    closing_gross_paise=res.book_closing_gross_paise,
                    depreciation_paise=res.book_depreciation_paise,
                    accumulated_depreciation_paise=res.book_closing_accum_dep_paise,
                    closing_nbv_paise=res.book_net_block_paise,
                )
                for res in asset_results
            ]
            calc_repo.save_asset_results(asset_result_models)

            # 10. Format and return CalculationRunDTO
            return self._build_run_dto(
                run_model=run,
                period_models=period_models,
                statements=statements,
                loan_results=loan_result_models,
                asset_results=asset_results,
            )

    def _build_run_dto(
        self,
        run_model: CalculationRunModel,
        period_models: List[ProjectPeriodModel],
        statements: List[PeriodFinancialStatements],
        loan_results: List[LoanScheduleResultModel],
        asset_results: list,
    ) -> CalculationRunDTO:
        period_headers = [f"Year {p.period_sequence} ({p.period_label})" for p in period_models]
        stmt_by_seq = {s.period_sequence: s for s in statements}

        # Build PL Table
        pl_rows = [
            HorizontalStatementRowDTO("1", "I", "Gross Revenue / Sales", False, False, {s: paise_to_rupees(stmt_by_seq[s].gross_billing_paise) for s in stmt_by_seq}),
            HorizontalStatementRowDTO("2", "II", "Less: Output GST", False, False, {s: paise_to_rupees(stmt_by_seq[s].output_gst_paise) for s in stmt_by_seq}),
            HorizontalStatementRowDTO("3", "III", "Net Revenue from Operations", False, True, {s: paise_to_rupees(stmt_by_seq[s].net_revenue_paise) for s in stmt_by_seq}),
            HorizontalStatementRowDTO("4", "IV", "Raw Material Consumed", False, False, {s: paise_to_rupees(stmt_by_seq[s].raw_material_cost_paise) for s in stmt_by_seq}),
            HorizontalStatementRowDTO("5", "V", "Other Direct / Power & Fuel Costs", False, False, {s: paise_to_rupees(stmt_by_seq[s].other_direct_costs_paise) for s in stmt_by_seq}),
            HorizontalStatementRowDTO("6", "VI", "Total Direct Costs", False, True, {s: paise_to_rupees(stmt_by_seq[s].total_direct_costs_paise) for s in stmt_by_seq}),
            HorizontalStatementRowDTO("7", "VII", "Gross Profit (III - VI)", False, True, {s: paise_to_rupees(stmt_by_seq[s].gross_profit_paise) for s in stmt_by_seq}),
            HorizontalStatementRowDTO("8", "VIII", "Employee Benefit Expenses", False, False, {s: paise_to_rupees(stmt_by_seq[s].employee_benefit_expenses_paise) for s in stmt_by_seq}),
            HorizontalStatementRowDTO("9", "IX", "Administrative & General Expenses", False, False, {s: paise_to_rupees(stmt_by_seq[s].admin_and_other_expenses_paise) for s in stmt_by_seq}),
            HorizontalStatementRowDTO("10", "X", "Selling & Distribution Expenses", False, False, {s: paise_to_rupees(stmt_by_seq[s].selling_and_distribution_expenses_paise) for s in stmt_by_seq}),
            HorizontalStatementRowDTO("11", "XI", "Total Operating Expenses", False, True, {s: paise_to_rupees(stmt_by_seq[s].total_operating_expenses_paise) for s in stmt_by_seq}),
            HorizontalStatementRowDTO("12", "XII", "Operating Profit (EBITDA)", False, True, {s: paise_to_rupees(stmt_by_seq[s].ebitda_paise) for s in stmt_by_seq}),
            HorizontalStatementRowDTO("13", "XIII", "Depreciation & Amortisation", False, False, {s: paise_to_rupees(stmt_by_seq[s].depreciation_paise) for s in stmt_by_seq}),
            HorizontalStatementRowDTO("14", "XIV", "Earnings Before Interest & Tax (EBIT)", False, True, {s: paise_to_rupees(stmt_by_seq[s].ebit_paise) for s in stmt_by_seq}),
            HorizontalStatementRowDTO("15", "XV", "Finance Costs / Loan Interest", False, False, {s: paise_to_rupees(stmt_by_seq[s].finance_costs_paise) for s in stmt_by_seq}),
            HorizontalStatementRowDTO("16", "XVI", "Profit Before Tax (PBT)", False, True, {s: paise_to_rupees(stmt_by_seq[s].profit_before_tax_paise) for s in stmt_by_seq}),
            HorizontalStatementRowDTO("17", "XVII", "Provision for Income Tax", False, False, {s: paise_to_rupees(stmt_by_seq[s].tax_provision_paise) for s in stmt_by_seq}),
            HorizontalStatementRowDTO("18", "XVIII", "Profit After Tax (PAT)", False, True, {s: paise_to_rupees(stmt_by_seq[s].profit_after_tax_paise) for s in stmt_by_seq}),
        ]
        pl_table = StatementsTableDTO("PL", "Projected Profit & Loss Statement", period_headers, pl_rows)

        # Build BS Table
        bs_rows = [
            HorizontalStatementRowDTO("A", "ASSETS", "--- ASSETS ---", True, False, {}),
            HorizontalStatementRowDTO("1", "1", "Property, Plant & Equipment (Net)", False, False, {s: paise_to_rupees(stmt_by_seq[s].bs_net_fixed_assets_paise) for s in stmt_by_seq}),
            HorizontalStatementRowDTO("2", "2", "Inventories (RM, WIP, FG)", False, False, {s: paise_to_rupees(stmt_by_seq[s].bs_total_inventory_paise) for s in stmt_by_seq}),
            HorizontalStatementRowDTO("3", "3", "Trade Receivables (Debtors)", False, False, {s: paise_to_rupees(stmt_by_seq[s].bs_trade_receivables_paise) for s in stmt_by_seq}),
            HorizontalStatementRowDTO("4", "4", "Cash & Bank Balances", False, False, {s: paise_to_rupees(stmt_by_seq[s].bs_cash_and_bank_paise) for s in stmt_by_seq}),
            HorizontalStatementRowDTO("5", "5", "Total Current Assets", False, True, {s: paise_to_rupees(stmt_by_seq[s].bs_total_current_assets_paise) for s in stmt_by_seq}),
            HorizontalStatementRowDTO("6", "TOTAL", "TOTAL ASSETS", False, True, {s: paise_to_rupees(stmt_by_seq[s].bs_total_assets_paise) for s in stmt_by_seq}),
            HorizontalStatementRowDTO("B", "EQUITY & LIABILITIES", "--- EQUITY & LIABILITIES ---", True, False, {}),
            HorizontalStatementRowDTO("7", "6", "Capital / Net Worth", False, False, {s: paise_to_rupees(stmt_by_seq[s].bs_net_worth_paise) for s in stmt_by_seq}),
            HorizontalStatementRowDTO("8", "7", "Term Borrowings (Secured Loans)", False, False, {s: paise_to_rupees(stmt_by_seq[s].bs_long_term_debt_paise) for s in stmt_by_seq}),
            HorizontalStatementRowDTO("9", "8", "Short-Term Bank Borrowings (CC/OD)", False, False, {s: paise_to_rupees(stmt_by_seq[s].bs_short_term_wc_debt_paise) for s in stmt_by_seq}),
            HorizontalStatementRowDTO("10", "9", "Trade Payables (Creditors)", False, False, {s: paise_to_rupees(stmt_by_seq[s].bs_trade_payables_paise) for s in stmt_by_seq}),
            HorizontalStatementRowDTO("11", "10", "Other Current Liabilities & Provisions", False, False, {s: paise_to_rupees(stmt_by_seq[s].bs_other_current_liabilities_paise) for s in stmt_by_seq}),
            HorizontalStatementRowDTO("12", "11", "Total Current Liabilities", False, True, {s: paise_to_rupees(stmt_by_seq[s].bs_total_current_liabilities_paise) for s in stmt_by_seq}),
            HorizontalStatementRowDTO("13", "TOTAL", "TOTAL LIABILITIES & EQUITY", False, True, {s: paise_to_rupees(stmt_by_seq[s].bs_total_liabilities_and_equity_paise) for s in stmt_by_seq}),
        ]
        bs_table = StatementsTableDTO("BS", "Projected Balance Sheet", period_headers, bs_rows)

        # Build Cash Flow Table
        cf_rows = [
            HorizontalStatementRowDTO("1", "I", "Operating Cash Flow before WC (PAT + Dep)", False, False, {s: paise_to_rupees(stmt_by_seq[s].cf_operating_profit_paise) for s in stmt_by_seq}),
            HorizontalStatementRowDTO("2", "II", "Working Capital Adjustments", False, False, {s: paise_to_rupees(stmt_by_seq[s].cf_working_capital_changes_paise) for s in stmt_by_seq}),
            HorizontalStatementRowDTO("3", "III", "Net Cash from Operating Activities", False, True, {s: paise_to_rupees(stmt_by_seq[s].cf_net_operating_cash_flow_paise) for s in stmt_by_seq}),
            HorizontalStatementRowDTO("4", "IV", "Purchase of Fixed Assets (Capex)", False, False, {s: paise_to_rupees(stmt_by_seq[s].cf_capital_expenditure_paise) for s in stmt_by_seq}),
            HorizontalStatementRowDTO("5", "V", "Net Cash used in Investing Activities", False, True, {s: paise_to_rupees(stmt_by_seq[s].cf_net_investing_cash_flow_paise) for s in stmt_by_seq}),
            HorizontalStatementRowDTO("6", "VI", "Capital / Equity Introduced", False, False, {s: paise_to_rupees(stmt_by_seq[s].cf_equity_introduced_paise) for s in stmt_by_seq}),
            HorizontalStatementRowDTO("7", "VII", "Term Loan Disbursements", False, False, {s: paise_to_rupees(stmt_by_seq[s].cf_loan_disbursements_paise) for s in stmt_by_seq}),
            HorizontalStatementRowDTO("8", "VIII", "Repayment of Term Borrowings", False, False, {s: paise_to_rupees(stmt_by_seq[s].cf_loan_repayments_paise) for s in stmt_by_seq}),
            HorizontalStatementRowDTO("9", "IX", "Drawings / Dividends", False, False, {s: paise_to_rupees(stmt_by_seq[s].cf_drawings_paise) for s in stmt_by_seq}),
            HorizontalStatementRowDTO("10", "X", "Net Cash from Financing Activities", False, True, {s: paise_to_rupees(stmt_by_seq[s].cf_net_financing_cash_flow_paise) for s in stmt_by_seq}),
            HorizontalStatementRowDTO("11", "XI", "Net Increase / (Decrease) in Cash", False, True, {s: paise_to_rupees(stmt_by_seq[s].net_cash_flow_paise) for s in stmt_by_seq}),
            HorizontalStatementRowDTO("12", "XII", "Opening Cash & Bank Balances", False, False, {s: paise_to_rupees(stmt_by_seq[s].opening_cash_paise) for s in stmt_by_seq}),
            HorizontalStatementRowDTO("13", "XIII", "Closing Cash & Bank Balances", False, True, {s: paise_to_rupees(stmt_by_seq[s].closing_cash_paise) for s in stmt_by_seq}),
        ]
        cf_table = StatementsTableDTO("CASH_FLOW", "Projected Cash Flow Statement (Indirect Method)", period_headers, cf_rows)

        # Loan schedule rows
        loan_dtos = [
            LoanScheduleRowDTO(
                installment_number=r.installment_number,
                due_date=str(r.due_date),
                opening_balance_rupees=paise_to_rupees(r.opening_balance_paise),
                disbursement_rupees=paise_to_rupees(r.disbursement_paise),
                payment_rupees=paise_to_rupees(r.payment_paise),
                interest_rupees=paise_to_rupees(r.interest_paise),
                principal_rupees=paise_to_rupees(r.principal_paise),
                closing_balance_rupees=paise_to_rupees(r.closing_balance_paise),
            )
            for r in loan_results
        ]

        # Asset schedule rows
        asset_dtos = [
            AssetScheduleRowDTO(
                period_sequence=r.period_sequence,
                period_label=period_models[r.period_sequence - 1].period_label if r.period_sequence <= len(period_models) else f"Year {r.period_sequence}",
                opening_gross_rupees=paise_to_rupees(r.book_opening_gross_paise),
                additions_rupees=paise_to_rupees(r.book_additions_paise),
                disposals_rupees=Decimal("0.00"),
                closing_gross_rupees=paise_to_rupees(r.book_closing_gross_paise),
                depreciation_rupees=paise_to_rupees(r.book_depreciation_paise),
                accumulated_depreciation_rupees=paise_to_rupees(r.book_closing_accum_dep_paise),
                closing_nbv_rupees=paise_to_rupees(r.book_net_block_paise),
            )
            for r in asset_results
        ]

        return CalculationRunDTO(
            id=run_model.id,
            project_id=run_model.project_id,
            scenario_id=run_model.scenario_id,
            run_number=run_model.run_number,
            engine_version=run_model.engine_version,
            input_hash=run_model.input_hash,
            run_timestamp=run_model.run_timestamp,
            run_status=run_model.run_status,
            prepared_by_label=run_model.prepared_by_label,
            summary_note=run_model.summary_note,
            validation_error_count=run_model.validation_error_count,
            validation_warning_count=run_model.validation_warning_count,
            pl_table=pl_table,
            bs_table=bs_table,
            cf_table=cf_table,
            loan_schedule=loan_dtos,
            asset_schedule=asset_dtos,
        )

    def get_latest_run(self, scenario_id: uuid.UUID) -> Optional[CalculationRunDTO]:
        with self.db_manager.session_scope() as session:
            repo = CalculationRepository(session)
            run = repo.get_latest_run(scenario_id)
            if not run:
                return None
            return CalculationRunDTO(
                id=run.id,
                project_id=run.project_id,
                scenario_id=run.scenario_id,
                run_number=run.run_number,
                engine_version=run.engine_version,
                input_hash=run.input_hash,
                run_timestamp=run.run_timestamp,
                run_status=run.run_status,
                prepared_by_label=run.prepared_by_label,
                summary_note=run.summary_note,
                validation_error_count=run.validation_error_count,
                validation_warning_count=run.validation_warning_count,
            )
