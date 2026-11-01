"""Domain engine for financial ratios, lender DSCR appraisal, break-even analysis, NPV, and IRR.

Implements pure Python Decimal calculations without dependencies on UI or ORM models.
All monetary inputs are in integer paise; all percentages and ratios are exact Decimals.
"""

from dataclasses import dataclass, field
from decimal import Decimal, ROUND_HALF_UP
from typing import Dict, List, Optional, Tuple

from app.common.exceptions import ValidationError
from app.common.money import paise_to_rupees, rupees_to_paise
from app.domain.financial.statement_pipeline import PeriodFinancialStatements


@dataclass
class PeriodRatioResult:
    """Calculated ratios and metrics for a single financial projection period."""
    period_sequence: int
    period_label: str

    # Liquidity
    current_ratio: Optional[Decimal]
    quick_ratio: Optional[Decimal]

    # Leverage & Solvency
    debt_equity_ratio: Optional[Decimal]
    term_debt_equity_ratio: Optional[Decimal]
    interest_coverage: Optional[Decimal]

    # Lender DSCR Variants
    gross_dscr: Optional[Decimal]  # (PAT + Dep + Term Interest) / (Principal + Term Interest)
    net_cfads_dscr: Optional[Decimal]  # CFADS / (Principal + Term Interest)
    scheduled_debt_service_paise: int
    cfads_paise: int

    # Profitability Margins (%)
    gross_profit_margin_pct: Decimal
    ebitda_margin_pct: Decimal
    ebit_margin_pct: Decimal
    pat_margin_pct: Decimal
    roce_pct: Optional[Decimal]
    ronw_pct: Optional[Decimal]

    # Break-Even Analysis
    fixed_costs_paise: int
    variable_costs_paise: int
    contribution_paise: int
    contribution_margin_pct: Decimal
    break_even_sales_paise: int
    break_even_capacity_pct: Decimal
    cash_break_even_sales_paise: int
    margin_of_safety_paise: int
    margin_of_safety_pct: Decimal


@dataclass
class ProjectAppraisalSummary:
    """Project-level lifetime investment appraisal metrics."""
    initial_investment_paise: int
    discount_rate_pct: Decimal

    # Returns
    npv_paise: int
    project_irr_pct: Optional[Decimal]
    simple_payback_years: Decimal
    profitability_index: Optional[Decimal]

    # Overall DSCR
    average_gross_dscr: Optional[Decimal]
    cumulative_gross_dscr: Optional[Decimal]
    average_net_cfads_dscr: Optional[Decimal]

    # Period-wise results
    period_ratios: List[PeriodRatioResult] = field(default_factory=list)


@dataclass
class SensitivityScenario:
    """Outcome of varying a single operational driver."""
    parameter_name: str
    variation_pct: Decimal  # e.g. -10, -5, +5, +10
    average_dscr: Optional[Decimal]
    project_irr_pct: Optional[Decimal]
    average_pat_paise: int
    first_year_break_even_pct: Decimal


class AppraisalEngine:
    """Calculates coverage, profitability, solvency, break-even, NPV, and IRR."""

    @classmethod
    def calculate_period_ratios(
        cls,
        statement: PeriodFinancialStatements,
        term_loan_principal_repaid_paise: int = 0,
        term_loan_interest_paise: int = 0,
    ) -> PeriodRatioResult:
        """Calculates comprehensive ratios for a single period."""
        # 1. Liquidity
        # Current Ratio = Total CA / Total CL
        cur_assets = Decimal(statement.bs_total_current_assets_paise)
        cur_liab = Decimal(statement.bs_total_current_liabilities_paise)
        current_ratio = (
            (cur_assets / cur_liab).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
            if cur_liab > 0 else None
        )

        # Quick Ratio = (Total CA - Total Inventory) / Total CL
        quick_assets = cur_assets - Decimal(statement.bs_total_inventory_paise)
        quick_ratio = (
            (quick_assets / cur_liab).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
            if cur_liab > 0 else None
        )

        # 2. Leverage
        # Debt-Equity = Total Debt / Net Worth
        net_worth = Decimal(statement.bs_net_worth_paise)
        total_debt = Decimal(statement.bs_long_term_debt_paise + statement.bs_short_term_wc_debt_paise)
        term_debt = Decimal(statement.bs_long_term_debt_paise)

        debt_equity = (
            (total_debt / net_worth).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
            if net_worth > 0 else None
        )
        term_debt_equity = (
            (term_debt / net_worth).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
            if net_worth > 0 else None
        )

        # Interest Coverage = EBIT / Finance Costs
        finance_costs = Decimal(statement.finance_costs_paise)
        ebit = Decimal(statement.ebit_paise)
        interest_coverage = (
            (ebit / finance_costs).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
            if finance_costs > 0 else None
        )

        # 3. Lender DSCR
        # Scheduled Debt Service = Principal Repayment + Term Loan Interest
        debt_service_paise = term_loan_principal_repaid_paise + term_loan_interest_paise
        debt_service_dec = Decimal(debt_service_paise)

        # Method A: Gross Cash Flow DSCR = (PAT + Depreciation + Term Interest) / Debt Service
        gross_cf_paise = statement.profit_after_tax_paise + statement.depreciation_paise + term_loan_interest_paise
        gross_dscr = (
            (Decimal(gross_cf_paise) / debt_service_dec).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
            if debt_service_dec > 0 else None
        )

        # Method B: Net CFADS DSCR = (EBITDA - Tax - Delta NWC) / Debt Service
        # CFADS = Operating Cash Flow before financing & capex
        cfads_paise = statement.cf_net_operating_cash_flow_paise + term_loan_interest_paise
        net_cfads_dscr = (
            (Decimal(cfads_paise) / debt_service_dec).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
            if debt_service_dec > 0 else None
        )

        # 4. Profitability Margins (%)
        net_rev = Decimal(statement.net_revenue_paise)
        gross_profit = Decimal(statement.gross_profit_paise)
        ebitda = Decimal(statement.ebitda_paise)
        pat = Decimal(statement.profit_after_tax_paise)

        gross_margin_pct = (
            ((gross_profit / net_rev) * Decimal("100")).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
            if net_rev > 0 else Decimal("0.00")
        )
        ebitda_margin_pct = (
            ((ebitda / net_rev) * Decimal("100")).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
            if net_rev > 0 else Decimal("0.00")
        )
        ebit_margin_pct = (
            ((ebit / net_rev) * Decimal("100")).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
            if net_rev > 0 else Decimal("0.00")
        )
        pat_margin_pct = (
            ((pat / net_rev) * Decimal("100")).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
            if net_rev > 0 else Decimal("0.00")
        )

        # Capital Returns
        # Capital Employed = Total Assets - Total Current Liabilities
        capital_employed = Decimal(statement.bs_total_assets_paise - statement.bs_total_current_liabilities_paise)
        roce_pct = (
            ((ebit / capital_employed) * Decimal("100")).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
            if capital_employed > 0 else None
        )
        ronw_pct = (
            ((pat / net_worth) * Decimal("100")).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
            if net_worth > 0 else None
        )

        # 5. Break-Even Analysis
        # Fixed Costs = Employee + Admin + Depreciation + Finance Costs
        fixed_costs = (
            statement.employee_benefit_expenses_paise
            + statement.admin_and_other_expenses_paise
            + statement.depreciation_paise
            + statement.finance_costs_paise
        )
        # Variable Costs = Raw Materials + Other Direct + Selling
        variable_costs = (
            statement.raw_material_cost_paise
            + statement.other_direct_costs_paise
            + statement.selling_and_distribution_expenses_paise
        )
        contribution = statement.net_revenue_paise - variable_costs
        contr_dec = Decimal(contribution)
        contr_margin_pct = (
            ((contr_dec / net_rev) * Decimal("100")).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
            if net_rev > 0 else Decimal("0.00")
        )

        # Break-Even Sales = Fixed Costs / Contribution Margin
        if contr_dec > 0 and net_rev > 0:
            margin_ratio = contr_dec / net_rev
            be_sales_dec = Decimal(fixed_costs) / margin_ratio
            be_sales_paise = int(be_sales_dec.quantize(Decimal("1"), rounding=ROUND_HALF_UP))
            be_capacity_pct = (
                ((be_sales_dec / net_rev) * Decimal("100")).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
            )

            # Cash Break-Even (Fixed costs without depreciation)
            cash_fixed_costs = max(0, fixed_costs - statement.depreciation_paise)
            cash_be_sales_dec = Decimal(cash_fixed_costs) / margin_ratio
            cash_be_sales_paise = int(cash_be_sales_dec.quantize(Decimal("1"), rounding=ROUND_HALF_UP))

            # Margin of Safety = Net Revenue - Break-Even Sales
            mos_paise = statement.net_revenue_paise - be_sales_paise
            mos_pct = (
                ((Decimal(mos_paise) / net_rev) * Decimal("100")).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
            )
        else:
            be_sales_paise = 0
            be_capacity_pct = Decimal("0.00")
            cash_be_sales_paise = 0
            mos_paise = 0
            mos_pct = Decimal("0.00")

        return PeriodRatioResult(
            period_sequence=statement.period_sequence,
            period_label=statement.period_label,
            current_ratio=current_ratio,
            quick_ratio=quick_ratio,
            debt_equity_ratio=debt_equity,
            term_debt_equity_ratio=term_debt_equity,
            interest_coverage=interest_coverage,
            gross_dscr=gross_dscr,
            net_cfads_dscr=net_cfads_dscr,
            scheduled_debt_service_paise=debt_service_paise,
            cfads_paise=cfads_paise,
            gross_profit_margin_pct=gross_margin_pct,
            ebitda_margin_pct=ebitda_margin_pct,
            ebit_margin_pct=ebit_margin_pct,
            pat_margin_pct=pat_margin_pct,
            roce_pct=roce_pct,
            ronw_pct=ronw_pct,
            fixed_costs_paise=fixed_costs,
            variable_costs_paise=variable_costs,
            contribution_paise=contribution,
            contribution_margin_pct=contr_margin_pct,
            break_even_sales_paise=be_sales_paise,
            break_even_capacity_pct=be_capacity_pct,
            cash_break_even_sales_paise=cash_be_sales_paise,
            margin_of_safety_paise=mos_paise,
            margin_of_safety_pct=mos_pct,
        )

    @classmethod
    def calculate_npv_and_irr(
        cls,
        cash_flows_paise: List[int],  # index 0 is Time 0 (Capex outflow, negative), 1..N are future inflows
        discount_rate_pct: Decimal = Decimal("10.0"),
    ) -> Tuple[int, Optional[Decimal]]:
        """Calculates Net Present Value in paise and Project IRR % using exact Decimal arithmetic."""
        if not cash_flows_paise:
            return 0, None

        r = discount_rate_pct / Decimal("100")
        npv_dec = Decimal("0")
        for t, cf in enumerate(cash_flows_paise):
            cf_dec = Decimal(cf)
            discount_factor = (Decimal("1") + r) ** t
            npv_dec += cf_dec / discount_factor

        npv_paise = int(npv_dec.quantize(Decimal("1"), rounding=ROUND_HALF_UP))

        # Check if IRR can exist (needs at least one negative and one positive cash flow)
        has_negative = any(cf < 0 for cf in cash_flows_paise)
        has_positive = any(cf > 0 for cf in cash_flows_paise)
        if not (has_negative and has_positive):
            return npv_paise, None

        # Solve for IRR using Bisection Method in range [-50%, 500%]
        def calc_npv_at(rate: Decimal) -> Decimal:
            val = Decimal("0")
            for t, cf in enumerate(cash_flows_paise):
                factor = (Decimal("1") + rate) ** t
                if factor == 0:
                    return Decimal("1e18")
                val += Decimal(cf) / factor
            return val

        low = Decimal("-0.50")
        high = Decimal("5.00")
        npv_low = calc_npv_at(low)
        npv_high = calc_npv_at(high)

        # Standard investment cash flows start negative then turn positive:
        # npv_at_rate decreases as rate increases.
        if (npv_low * npv_high) > 0:
            # Check if root lies outside normal range
            return npv_paise, None

        # Binary search
        for _ in range(60):  # 60 iterations yields > 18 decimal places of accuracy
            mid = (low + high) / Decimal("2")
            npv_mid = calc_npv_at(mid)
            if abs(npv_mid) < Decimal("1"):  # Within 1 paise
                break
            if (npv_low * npv_mid) <= 0:
                high = mid
                npv_high = npv_mid
            else:
                low = mid
                npv_low = npv_mid

        irr_pct = ((low + high) / Decimal("2") * Decimal("100")).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        return npv_paise, irr_pct

    @classmethod
    def calculate_simple_payback(
        cls,
        initial_investment_paise: int,
        annual_inflows_paise: List[int],
    ) -> Decimal:
        """Calculates simple payback period in years (e.g. 3.42 years)."""
        if initial_investment_paise <= 0 or not annual_inflows_paise:
            return Decimal("0.00")

        cumulative = 0
        target = initial_investment_paise

        for i, inflow in enumerate(annual_inflows_paise, start=1):
            if inflow <= 0:
                continue
            if cumulative + inflow >= target:
                # Fractional year
                needed = target - cumulative
                fraction = Decimal(needed) / Decimal(inflow)
                years = Decimal(i - 1) + fraction
                return years.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
            cumulative += inflow

        # If not recovered within projection period
        return Decimal(len(annual_inflows_paise)).quantize(Decimal("0.01"))

    @classmethod
    def calculate_project_appraisal(
        cls,
        statements: List[PeriodFinancialStatements],
        initial_investment_paise: int,
        discount_rate_pct: Decimal = Decimal("10.0"),
        term_loan_principal_repaid_by_seq: Dict[int, int] = None,
        term_loan_interest_by_seq: Dict[int, int] = None,
    ) -> ProjectAppraisalSummary:
        """Generates comprehensive appraisal metrics for the full projection lifecycle."""
        if term_loan_principal_repaid_by_seq is None:
            term_loan_principal_repaid_by_seq = {}
        if term_loan_interest_by_seq is None:
            term_loan_interest_by_seq = {}

        period_ratios: List[PeriodRatioResult] = []
        valid_gross_dscrs: List[Decimal] = []
        valid_net_dscrs: List[Decimal] = []
        total_cfads = 0
        total_debt_service = 0

        # Inflows for project returns (FCFF = Net Operating Cash Flow - Capex)
        # Time 0 outflow is -initial_investment_paise
        project_cash_flows = [-abs(initial_investment_paise)]

        annual_inflows: List[int] = []

        for stmt in sorted(statements, key=lambda s: s.period_sequence):
            seq = stmt.period_sequence
            prin = term_loan_principal_repaid_by_seq.get(seq, 0)
            intr = term_loan_interest_by_seq.get(seq, 0)

            ratio_res = cls.calculate_period_ratios(
                statement=stmt,
                term_loan_principal_repaid_paise=prin,
                term_loan_interest_paise=intr,
            )
            period_ratios.append(ratio_res)

            if ratio_res.gross_dscr is not None:
                valid_gross_dscrs.append(ratio_res.gross_dscr)
            if ratio_res.net_cfads_dscr is not None:
                valid_net_dscrs.append(ratio_res.net_cfads_dscr)

            total_cfads += ratio_res.cfads_paise
            total_debt_service += ratio_res.scheduled_debt_service_paise

            # Net operational cash generation
            inflow = stmt.cf_net_operating_cash_flow_paise
            project_cash_flows.append(inflow)
            annual_inflows.append(max(0, inflow))

        # Overall DSCRs
        avg_gross_dscr = (
            (sum(valid_gross_dscrs) / Decimal(len(valid_gross_dscrs))).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
            if valid_gross_dscrs else None
        )
        avg_net_dscr = (
            (sum(valid_net_dscrs) / Decimal(len(valid_net_dscrs))).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
            if valid_net_dscrs else None
        )
        cum_gross_dscr = (
            (Decimal(total_cfads) / Decimal(total_debt_service)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
            if total_debt_service > 0 else None
        )

        # NPV & IRR
        npv_paise, irr_pct = cls.calculate_npv_and_irr(project_cash_flows, discount_rate_pct)

        # Simple Payback
        payback = cls.calculate_simple_payback(initial_investment_paise, annual_inflows)

        # Profitability Index = (NPV + Outflow) / Outflow
        pi = None
        if initial_investment_paise > 0:
            pv_inflows = Decimal(npv_paise + initial_investment_paise)
            pi = (pv_inflows / Decimal(initial_investment_paise)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

        return ProjectAppraisalSummary(
            initial_investment_paise=initial_investment_paise,
            discount_rate_pct=discount_rate_pct,
            npv_paise=npv_paise,
            project_irr_pct=irr_pct,
            simple_payback_years=payback,
            profitability_index=pi,
            average_gross_dscr=avg_gross_dscr,
            cumulative_gross_dscr=cum_gross_dscr,
            average_net_cfads_dscr=avg_net_dscr,
            period_ratios=period_ratios,
        )
