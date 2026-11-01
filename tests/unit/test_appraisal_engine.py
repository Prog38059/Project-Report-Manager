"""Unit tests for Appraisal Engine (Ratios, DSCR, Break-Even, NPV, IRR) and Validation Rules."""

from decimal import Decimal
import uuid
import pytest

from app.common.money import paise_to_rupees, rupees_to_paise
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


def _create_mock_statement(
    period_seq: int = 1,
    net_revenue_paise: int = 100000000,       # ₹10 Lakhs
    rm_cost_paise: int = 40000000,            # ₹4 Lakhs
    other_direct_paise: int = 10000000,       # ₹1 Lakh
    employee_cost_paise: int = 15000000,      # ₹1.5 Lakhs
    admin_cost_paise: int = 5000000,          # ₹0.5 Lakh
    selling_cost_paise: int = 5000000,        # ₹0.5 Lakh
    depreciation_paise: int = 5000000,        # ₹0.5 Lakh
    finance_costs_paise: int = 3000000,       # ₹0.3 Lakh
    tax_provision_paise: int = 4250000,       # ₹0.425 Lakh
    ca_paise: int = 30000000,                 # ₹3 Lakhs
    cl_paise: int = 15000000,                 # ₹1.5 Lakhs
    inventory_paise: int = 10000000,          # ₹1 Lakh
    debt_paise: int = 20000000,               # ₹2 Lakhs
    net_worth_paise: int = 25000000,          # ₹2.5 Lakhs
    closing_cash_paise: int = 5000000,        # ₹50,000
    balance_diff_paise: int = 0,
) -> PeriodFinancialStatements:
    """Helper creating a consistent PeriodFinancialStatements object for testing."""
    total_direct = rm_cost_paise + other_direct_paise
    gp = net_revenue_paise - total_direct
    opex = employee_cost_paise + admin_cost_paise + selling_cost_paise
    ebitda = gp - opex
    ebit = ebitda - depreciation_paise
    pbt = ebit - finance_costs_paise
    pat = pbt - tax_provision_paise
    net_op_cash = pat + depreciation_paise

    return PeriodFinancialStatements(
        period_id=uuid.uuid4(),
        period_sequence=period_seq,
        period_label=f"FY {2025 + period_seq}",
        gross_billing_paise=net_revenue_paise,
        output_gst_paise=0,
        net_revenue_paise=net_revenue_paise,
        raw_material_cost_paise=rm_cost_paise,
        other_direct_costs_paise=other_direct_paise,
        total_direct_costs_paise=total_direct,
        gross_profit_paise=gp,
        employee_benefit_expenses_paise=employee_cost_paise,
        admin_and_other_expenses_paise=admin_cost_paise,
        selling_and_distribution_expenses_paise=selling_cost_paise,
        total_operating_expenses_paise=opex,
        ebitda_paise=ebitda,
        depreciation_paise=depreciation_paise,
        ebit_paise=ebit,
        finance_costs_paise=finance_costs_paise,
        profit_before_tax_paise=pbt,
        tax_provision_paise=tax_provision_paise,
        profit_after_tax_paise=pat,
        cf_operating_profit_paise=pat + depreciation_paise,
        cf_working_capital_changes_paise=0,
        cf_net_operating_cash_flow_paise=net_op_cash,
        cf_capital_expenditure_paise=0,
        cf_net_investing_cash_flow_paise=0,
        cf_equity_introduced_paise=0,
        cf_loan_disbursements_paise=0,
        cf_loan_repayments_paise=0,
        cf_drawings_paise=0,
        cf_net_financing_cash_flow_paise=0,
        net_cash_flow_paise=net_op_cash,
        opening_cash_paise=0,
        closing_cash_paise=closing_cash_paise,
        bs_net_fixed_assets_paise=40000000,
        bs_raw_materials_paise=0,
        bs_wip_paise=0,
        bs_finished_goods_paise=0,
        bs_total_inventory_paise=inventory_paise,
        bs_trade_receivables_paise=15000000,
        bs_cash_and_bank_paise=closing_cash_paise,
        bs_deposits_and_other_assets_paise=0,
        bs_total_current_assets_paise=ca_paise,
        bs_total_assets_paise=40000000 + ca_paise,
        bs_net_worth_paise=net_worth_paise,
        bs_long_term_debt_paise=debt_paise,
        bs_short_term_wc_debt_paise=0,
        bs_trade_payables_paise=cl_paise,
        bs_other_current_liabilities_paise=0,
        bs_total_current_liabilities_paise=cl_paise,
        bs_total_liabilities_and_equity_paise=(40000000 + ca_paise) - balance_diff_paise,
        balance_difference_paise=balance_diff_paise,
    )


def test_period_ratios_calculation():
    stmt = _create_mock_statement(
        period_seq=1,
        net_revenue_paise=100000000,   # 10 Lakhs
        ca_paise=30000000,            # 3 Lakhs
        cl_paise=15000000,            # 1.5 Lakhs
        inventory_paise=5000000,      # 0.5 Lakh
        debt_paise=20000000,          # 2 Lakhs
        net_worth_paise=25000000,     # 2.5 Lakhs
    )
    # Principal repaid = 2 Lakhs, Interest = 30,000 (3000000 paise)
    prin = 20000000
    intr = 3000000

    ratios = AppraisalEngine.calculate_period_ratios(
        statement=stmt,
        term_loan_principal_repaid_paise=prin,
        term_loan_interest_paise=intr,
    )

    # 1. Current Ratio = 3L / 1.5L = 2.00x
    assert ratios.current_ratio == Decimal("2.00")
    # 2. Quick Ratio = (3L - 0.5L) / 1.5L = 2.5L / 1.5L = 1.67x
    assert ratios.quick_ratio == Decimal("1.67")
    # 3. Debt-Equity = 2L / 2.5L = 0.80x
    assert ratios.debt_equity_ratio == Decimal("0.80")
    # 4. Interest coverage = EBITDA (25L) / Finance Costs (30,000)
    assert ratios.interest_coverage is not None
    assert ratios.interest_coverage > Decimal("5.00")

    # 5. Gross DSCR = (PAT + Dep + Term Int) / (Principal + Term Int)
    # Debt service = 2L + 30,000 = 2.30 Lakhs
    expected_service = prin + intr
    assert ratios.scheduled_debt_service_paise == expected_service
    assert ratios.gross_dscr == Decimal("0.90")

    # 6. Break-Even Analysis
    # Variable costs = 4L (RM) + 1L (Other Direct) + 0.5L (Selling) = 5.5L
    assert ratios.variable_costs_paise == 55000000
    # Fixed costs = 1.5L (Emp) + 0.5L (Admin) + 0.5L (Dep) + 0.3L (Fin) = 2.8L
    assert ratios.fixed_costs_paise == 28000000
    # Contribution = 10L - 5.5L = 4.5L
    assert ratios.contribution_paise == 45000000
    # Contribution margin = 4.5L / 10L = 45.00%
    assert ratios.contribution_margin_pct == Decimal("45.00")
    # Break-Even Sales = 2.8L / 45% = 6.222... Lakhs = 62,22,222 paise
    assert ratios.break_even_sales_paise == 62222222
    assert ratios.break_even_capacity_pct == Decimal("62.22")
    # Cash Break-Even (Fixed costs without dep = 2.8L - 0.5L = 2.3L)
    # 2.3L / 45% = 5.111... Lakhs = 51,11,111 paise
    assert ratios.cash_break_even_sales_paise == 51111111
    # Margin of Safety = 10L - 6.222L = 3.777L (37.78%)
    assert ratios.margin_of_safety_pct == Decimal("37.78")


def test_npv_and_irr_exact_bisection():
    # Outflow: 10 Lakhs (Year 0)
    # Inflows: 3 Lakhs per year for 5 years
    cash_flows = [-100000000, 30000000, 30000000, 30000000, 30000000, 30000000]

    npv_paise, irr_pct = AppraisalEngine.calculate_npv_and_irr(
        cash_flows_paise=cash_flows,
        discount_rate_pct=Decimal("10.0"),
    )

    # PV of 3L for 5 years @ 10% = 300000 * 3.7907867 = 11,37,236 paise approx
    # NPV should be positive ~ 1.37 Lakhs = 13723603 paise
    assert npv_paise > 13000000
    assert npv_paise < 14500000

    # Project IRR for 3L annual on 10L for 5 yrs is ~ 15.24%
    assert irr_pct is not None
    assert Decimal("15.20") <= irr_pct <= Decimal("15.30")


def test_simple_payback_period():
    initial = 100000000  # 10 Lakhs
    # Inflows: 4L in Y1, 4L in Y2, 4L in Y3 -> Recovered at 2.50 years
    inflows = [40000000, 40000000, 40000000]
    payback = AppraisalEngine.calculate_simple_payback(initial, inflows)
    assert payback == Decimal("2.50")


def test_validation_engine_rules():
    # 1. Clean statement produces zero error issues
    clean_stmt = _create_mock_statement(period_seq=1, balance_diff_paise=0, closing_cash_paise=5000000)
    appraisal = AppraisalEngine.calculate_project_appraisal(
        statements=[clean_stmt],
        initial_investment_paise=100000000,
        discount_rate_pct=Decimal("10.0"),
    )
    clean_issues = FinancialValidationEngine.audit_projection(
        statements=[clean_stmt],
        appraisal=appraisal,
        funding_gap_paise=0,
    )
    # No ERROR severity issues
    errors = [i for i in clean_issues if i.severity == ValidationSeverity.ERROR]
    assert len(errors) == 0

    # 2. Balance sheet out of balance produces VAL-BS-001 ERROR
    unbalanced_stmt = _create_mock_statement(period_seq=1, balance_diff_paise=50000)
    issues_bs = FinancialValidationEngine.audit_projection(
        statements=[unbalanced_stmt],
        appraisal=appraisal,
        funding_gap_paise=0,
    )
    bs_errors = [i for i in issues_bs if i.rule_code == "VAL-BS-001"]
    assert len(bs_errors) == 1
    assert bs_errors[0].severity == ValidationSeverity.ERROR
    assert bs_errors[0].is_overridable is False

    # 3. Negative cash produces VAL-CASH-001 ERROR
    neg_cash_stmt = _create_mock_statement(period_seq=1, closing_cash_paise=-500000)
    issues_cash = FinancialValidationEngine.audit_projection(
        statements=[neg_cash_stmt],
        appraisal=appraisal,
        funding_gap_paise=0,
    )
    cash_errors = [i for i in issues_cash if i.rule_code == "VAL-CASH-001"]
    assert len(cash_errors) == 1
    assert cash_errors[0].severity == ValidationSeverity.ERROR
    assert cash_errors[0].is_overridable is False

    # 4. Funding Gap produces VAL-FUND-001
    issues_fund = FinancialValidationEngine.audit_projection(
        statements=[clean_stmt],
        appraisal=appraisal,
        funding_gap_paise=10000000,  # 1 Lakh shortfall
    )
    fund_issues = [i for i in issues_fund if i.rule_code == "VAL-FUND-001"]
    assert len(fund_issues) == 1
    assert fund_issues[0].severity == ValidationSeverity.ERROR
