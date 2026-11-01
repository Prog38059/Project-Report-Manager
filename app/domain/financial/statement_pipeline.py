"""Integrated Three-Statement Financial Projection Pipeline.

Compiles Profit & Loss, Balance Sheet, and Cash Flow Statement across
multi-year projection horizons while enforcing the strict zero-plug balance sheet invariant.
"""

from dataclasses import dataclass
from decimal import Decimal
from typing import Dict, List, Optional
from uuid import UUID

from app.common.exceptions import ValidationError
from app.common.money import format_inr, paise_to_rupees, rupees_to_paise
from app.common.types import ConstitutionCode
from app.domain.financial.depreciation import AssetAdditionInput, AssetScheduleCalculator, PeriodDepreciationResult
from app.domain.financial.equity_engine import EquityRollForwardCalculator, PeriodEquityMovement
from app.domain.financial.loan_engine import AnnualLoanSummary, LoanAmortizationCalculator
from app.domain.financial.tax_engine import TaxProvisionCalculator
from app.domain.financial.working_capital import WorkingCapitalAssumptions, WorkingCapitalCalculator, WorkingCapitalResult


@dataclass
class PeriodFinancialStatements:
    """Integrated statement results for a single projection financial year."""
    period_id: UUID
    period_sequence: int
    period_label: str

    # 1. Profit & Loss Statement (paise)
    gross_billing_paise: int
    output_gst_paise: int
    net_revenue_paise: int
    raw_material_cost_paise: int
    other_direct_costs_paise: int
    total_direct_costs_paise: int
    gross_profit_paise: int
    employee_benefit_expenses_paise: int
    admin_and_other_expenses_paise: int
    selling_and_distribution_expenses_paise: int
    total_operating_expenses_paise: int
    ebitda_paise: int
    depreciation_paise: int
    ebit_paise: int
    finance_costs_paise: int
    profit_before_tax_paise: int
    tax_provision_paise: int
    profit_after_tax_paise: int

    # 2. Cash Flow Statement (Indirect Method) (paise)
    cf_operating_profit_paise: int
    cf_working_capital_changes_paise: int
    cf_net_operating_cash_flow_paise: int
    cf_capital_expenditure_paise: int
    cf_net_investing_cash_flow_paise: int
    cf_equity_introduced_paise: int
    cf_loan_disbursements_paise: int
    cf_loan_repayments_paise: int
    cf_drawings_paise: int
    cf_net_financing_cash_flow_paise: int
    net_cash_flow_paise: int
    opening_cash_paise: int
    closing_cash_paise: int

    # 3. Balance Sheet (paise)
    bs_net_fixed_assets_paise: int
    bs_raw_materials_paise: int
    bs_wip_paise: int
    bs_finished_goods_paise: int
    bs_total_inventory_paise: int
    bs_trade_receivables_paise: int
    bs_cash_and_bank_paise: int
    bs_deposits_and_other_assets_paise: int
    bs_total_current_assets_paise: int
    bs_total_assets_paise: int

    bs_net_worth_paise: int
    bs_long_term_debt_paise: int
    bs_short_term_wc_debt_paise: int
    bs_trade_payables_paise: int
    bs_other_current_liabilities_paise: int
    bs_total_current_liabilities_paise: int
    bs_total_liabilities_and_equity_paise: int

    balance_difference_paise: int  # Must be strictly 0


class StatementPipeline:
    """Executes the complete integrated multi-year statement projection."""

    @classmethod
    def run_projection(
        cls,
        period_definitions: List[dict],  # list of dicts: {"id": UUID, "sequence": int, "label": str}
        constitution_code: ConstitutionCode,
        net_revenue_by_period: Dict[int, int],  # seq -> paise
        material_cost_by_period: Dict[int, int],
        other_direct_cost_by_period: Dict[int, int],
        employee_cost_by_period: Dict[int, int],
        admin_cost_by_period: Dict[int, int],
        selling_cost_by_period: Dict[int, int],
        total_capex_by_period: Dict[int, int],
        asset_useful_life_years: Decimal = Decimal("10"),
        promoter_equity_introduced_by_period: Dict[int, int] = None,
        term_loan_sanctioned_paise: int = 0,
        term_loan_interest_rate_pct: Decimal = Decimal("11.5"),
        term_loan_tenure_months: int = 84,  # 7 years
        term_loan_moratorium_months: int = 0,
        wc_assumptions: WorkingCapitalAssumptions = None,
        drawings_by_period: Dict[int, int] = None,
    ) -> List[PeriodFinancialStatements]:
        """Runs multi-year projections and enforces the zero-plug Balance Sheet invariant."""
        if wc_assumptions is None:
            wc_assumptions = WorkingCapitalAssumptions()
        if promoter_equity_introduced_by_period is None:
            promoter_equity_introduced_by_period = {}
        if drawings_by_period is None:
            drawings_by_period = {}

        # 1. Asset Schedule
        additions: List[AssetAdditionInput] = []
        for p in period_definitions:
            seq = p["sequence"]
            additions.append(
                AssetAdditionInput(
                    period_id=p["id"],
                    period_sequence=seq,
                    gross_addition_paise=total_capex_by_period.get(seq, 0),
                    useful_life_years=asset_useful_life_years,
                )
            )
        asset_results = AssetScheduleCalculator.calculate_schedule(additions)
        asset_by_seq = {r.period_sequence: r for r in asset_results}

        # 2. Term Loan Amortization Schedule
        monthly_sched = LoanAmortizationCalculator.calculate_monthly_schedule(
            sanctioned_amount_paise=term_loan_sanctioned_paise,
            annual_rate_pct=term_loan_interest_rate_pct,
            tenure_months=term_loan_tenure_months,
            moratorium_months=term_loan_moratorium_months,
        )
        periods_tuples = [(p["id"], p["sequence"], 12) for p in period_definitions]
        loan_summaries = LoanAmortizationCalculator.aggregate_to_annual_periods(monthly_sched, periods_tuples)
        loan_by_seq = {s.period_sequence: s for s in loan_summaries}

        # 3. Multi-year Pipeline Execution
        statements: List[PeriodFinancialStatements] = []
        curr_opening_cash_paise = 0
        curr_opening_equity_paise = 0

        prior_nwc_paise = 0
        prior_wc_debt_paise = 0

        for p in sorted(period_definitions, key=lambda x: x["sequence"]):
            seq = p["sequence"]
            p_id = p["id"]
            label = p["label"]

            # --- A. Profit & Loss ---
            net_rev = net_revenue_by_period.get(seq, 0)
            rm_cost = material_cost_by_period.get(seq, 0)
            other_dir = other_direct_cost_by_period.get(seq, 0)
            total_dir = rm_cost + other_dir
            gross_profit = net_rev - total_dir

            emp_cost = employee_cost_by_period.get(seq, 0)
            admin_cost = admin_cost_by_period.get(seq, 0)
            selling_cost = selling_cost_by_period.get(seq, 0)
            total_op_exp = emp_cost + admin_cost + selling_cost

            ebitda = gross_profit - total_op_exp

            # Depreciation
            dep_res = asset_by_seq.get(seq)
            book_dep = dep_res.book_depreciation_paise if dep_res else 0
            tax_dep = dep_res.tax_depreciation_paise if dep_res else 0
            ebit = ebitda - book_dep

            # Finance Costs
            loan_res = loan_by_seq.get(seq)
            term_loan_interest = loan_res.interest_expense_paise if loan_res else 0

            # Working capital calculation
            cost_of_production = total_dir + emp_cost + admin_cost
            wc_res = WorkingCapitalCalculator.calculate_period_working_capital(
                period_id=p_id,
                period_sequence=seq,
                annual_raw_material_cost_paise=rm_cost,
                annual_total_direct_cost_paise=total_dir,
                annual_cost_of_production_paise=cost_of_production,
                annual_net_sales_paise=net_rev,
                assumptions=wc_assumptions,
            )

            # Bank Working Capital interest (e.g. 10% on bank limit)
            wc_interest_dec = Decimal(wc_res.assessed_bank_limit_paise) * Decimal("0.10")
            wc_interest = int(wc_interest_dec.quantize(Decimal("1")))

            total_finance_costs = term_loan_interest + wc_interest
            pbt = ebit - total_finance_costs

            # Tax Provision
            tax_calc = TaxProvisionCalculator.calculate_tax(
                book_pbt_paise=pbt,
                book_depreciation_paise=book_dep,
                tax_depreciation_paise=tax_dep,
                constitution_code=constitution_code,
            )
            tax_prov = tax_calc.tax_provision_paise
            pat = tax_calc.pat_paise

            # Equity Roll-forward
            fresh_equity = promoter_equity_introduced_by_period.get(seq, 0)
            drawings = drawings_by_period.get(seq, 0)
            eq_mov = EquityRollForwardCalculator.calculate_movement(
                period_id=p_id,
                period_sequence=seq,
                constitution_code=constitution_code,
                opening_equity_paise=curr_opening_equity_paise,
                capital_introduced_paise=fresh_equity,
                profit_after_tax_paise=pat,
                drawings_or_dividends_paise=drawings,
            )
            curr_closing_equity_paise = eq_mov.closing_equity_paise

            # --- B. Cash Flow Statement (Indirect Method) ---
            # Operating cash flow before working capital = PAT + Depreciation
            # Direct taxes paid = tax_prov (assumed fully settled via advance tax / TDS)
            cf_op_profit = pat + book_dep

            # Change in Operating Working Capital (excluding cash)
            # Delta Operating Current Assets (Inventory + Receivables) - Delta Operating Current Liabilities (Payables)
            curr_nwc = (wc_res.total_inventory_paise + wc_res.trade_receivables_paise) - wc_res.trade_payables_paise
            delta_nwc = curr_nwc - prior_nwc_paise
            prior_nwc_paise = curr_nwc

            cf_net_operating = cf_op_profit - delta_nwc

            # Investing cash flow = - Capex
            capex = total_capex_by_period.get(seq, 0)
            cf_investing = -capex

            # Financing cash flow
            # Loan disbursement + fresh equity - loan repayment + delta WC limit - drawings
            term_disb = loan_res.disbursements_paise if loan_res else 0
            term_repaid = loan_res.principal_repaid_paise if loan_res else 0
            wc_debt = wc_res.assessed_bank_limit_paise
            delta_wc_debt = wc_debt - prior_wc_debt_paise
            prior_wc_debt_paise = wc_debt

            cf_financing = fresh_equity + term_disb - term_repaid + delta_wc_debt - drawings

            # Net Cash Flow
            net_cf = cf_net_operating + cf_investing + cf_financing

            closing_cash = curr_opening_cash_paise + net_cf

            # --- C. Balance Sheet & Invariant Check ---
            net_fixed_assets = dep_res.book_net_block_paise if dep_res else 0
            total_ca = wc_res.total_inventory_paise + wc_res.trade_receivables_paise + closing_cash
            total_assets = net_fixed_assets + total_ca

            long_term_debt = loan_res.closing_balance_paise if loan_res else 0
            total_cl = wc_res.trade_payables_paise  # Advance tax settled; trade payables are operating CL
            total_liab_and_equity = curr_closing_equity_paise + long_term_debt + wc_debt + total_cl

            # Fundamental Invariant: Assets == Liabilities + Equity
            # Difference calculation
            diff = total_assets - total_liab_and_equity
            if diff != 0:

                raise ValidationError(
                    f"Balance Sheet out of balance in Period {seq} by ₹{paise_to_rupees(diff)}. "
                    f"Total Assets: ₹{paise_to_rupees(total_assets)}, Total Liabilities & Equity: ₹{paise_to_rupees(total_liab_and_equity)}. "
                    "Unexplained balancing plug is strictly forbidden."
                )

            statements.append(
                PeriodFinancialStatements(
                    period_id=p_id,
                    period_sequence=seq,
                    period_label=label,
                    gross_billing_paise=net_rev,
                    output_gst_paise=0,
                    net_revenue_paise=net_rev,
                    raw_material_cost_paise=rm_cost,
                    other_direct_costs_paise=other_dir,
                    total_direct_costs_paise=total_dir,
                    gross_profit_paise=gross_profit,
                    employee_benefit_expenses_paise=emp_cost,
                    admin_and_other_expenses_paise=admin_cost,
                    selling_and_distribution_expenses_paise=selling_cost,
                    total_operating_expenses_paise=total_op_exp,
                    ebitda_paise=ebitda,
                    depreciation_paise=book_dep,
                    ebit_paise=ebit,
                    finance_costs_paise=total_finance_costs,
                    profit_before_tax_paise=pbt,
                    tax_provision_paise=tax_prov,
                    profit_after_tax_paise=pat,
                    cf_operating_profit_paise=cf_op_profit,
                    cf_working_capital_changes_paise=-delta_nwc,
                    cf_net_operating_cash_flow_paise=cf_net_operating,
                    cf_capital_expenditure_paise=capex,
                    cf_net_investing_cash_flow_paise=cf_investing,
                    cf_equity_introduced_paise=fresh_equity,
                    cf_loan_disbursements_paise=term_disb,
                    cf_loan_repayments_paise=term_repaid,
                    cf_drawings_paise=drawings,
                    cf_net_financing_cash_flow_paise=cf_financing,
                    net_cash_flow_paise=net_cf,
                    opening_cash_paise=curr_opening_cash_paise,
                    closing_cash_paise=closing_cash,
                    bs_net_fixed_assets_paise=net_fixed_assets,
                    bs_raw_materials_paise=wc_res.raw_material_paise,
                    bs_wip_paise=wc_res.wip_paise,
                    bs_finished_goods_paise=wc_res.finished_goods_paise,
                    bs_total_inventory_paise=wc_res.total_inventory_paise,
                    bs_trade_receivables_paise=wc_res.trade_receivables_paise,
                    bs_cash_and_bank_paise=closing_cash,
                    bs_deposits_and_other_assets_paise=0,
                    bs_total_current_assets_paise=total_ca,
                    bs_total_assets_paise=total_assets,
                    bs_net_worth_paise=curr_closing_equity_paise,
                    bs_long_term_debt_paise=long_term_debt,
                    bs_short_term_wc_debt_paise=wc_debt,
                    bs_trade_payables_paise=wc_res.trade_payables_paise,
                    bs_other_current_liabilities_paise=tax_prov,
                    bs_total_current_liabilities_paise=total_cl,
                    bs_total_liabilities_and_equity_paise=total_liab_and_equity,
                    balance_difference_paise=diff,
                )
            )

            # Roll forward for next period
            curr_opening_cash_paise = closing_cash
            curr_opening_equity_paise = curr_closing_equity_paise

        return statements
