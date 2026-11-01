"""Unit tests for Financial Domain Engines and Invariant Verification."""

from decimal import Decimal
import uuid
import pytest

from app.common.types import ConstitutionCode
from app.domain.financial.depreciation import AssetAdditionInput, AssetScheduleCalculator
from app.domain.financial.equity_engine import EquityRollForwardCalculator
from app.domain.financial.loan_engine import LoanAmortizationCalculator
from app.domain.financial.statement_pipeline import StatementPipeline
from app.domain.financial.tax_engine import TaxProvisionCalculator
from app.domain.financial.working_capital import WorkingCapitalAssumptions, WorkingCapitalCalculator


def test_asset_schedule_slm_and_wdv():
    period_id = uuid.uuid4()
    additions = [
        AssetAdditionInput(
            period_id=period_id,
            period_sequence=1,
            gross_addition_paise=100000000,  # 10 Lakhs
            residual_value_paise=5000000,   # 5% residual value = 50,000
            useful_life_years=Decimal("10"),
            tax_rate_pct=Decimal("15.0"),
        )
    ]
    results = AssetScheduleCalculator.calculate_schedule(additions)
    assert len(results) == 1
    # Residual = 5% of 10L = 50,000. Depreciable = 9,50,000. Over 10 yrs = 95,000 / 9500000 paise
    assert results[0].book_depreciation_paise == 9500000
    assert results[0].book_net_block_paise == 100000000 - 9500000
    # Tax dep @ 15% on 10L = 1,50,000 / 15000000 paise
    assert results[0].tax_depreciation_paise == 15000000
    assert results[0].tax_closing_wdv_paise == 85000000


def test_loan_amortization_calculator():
    # 10 Lakh loan @ 12% for 60 months (5 years)
    sanctioned = 100000000  # 10 Lakhs in paise
    schedule = LoanAmortizationCalculator.calculate_monthly_schedule(
        sanctioned_amount_paise=sanctioned,
        annual_rate_pct=Decimal("12.0"),
        tenure_months=60,
        moratorium_months=0,
    )
    assert len(schedule) == 60
    # First month opening balance = 10 Lakhs
    assert schedule[0].opening_principal_paise == sanctioned
    # Closing balance after 60 months must be exactly 0
    assert schedule[-1].closing_principal_paise == 0

    # Aggregate to 5 annual periods
    annual_periods = [(uuid.uuid4(), i + 1, 12) for i in range(5)]
    annual_summaries = LoanAmortizationCalculator.aggregate_to_annual_periods(schedule, annual_periods)
    assert len(annual_summaries) == 5
    assert annual_summaries[-1].closing_balance_paise == 0
    # Total principal repaid must equal sanctioned amount
    total_principal = sum(s.principal_repaid_paise for s in annual_summaries)
    assert total_principal == sanctioned


def test_statement_pipeline_zero_plug_balance_invariant():
    # Set up 7-year projection periods
    periods = [
        {"id": uuid.uuid4(), "sequence": i + 1, "label": f"FY {2026 + i}-{27 + i}"}
        for i in range(7)
    ]

    # Revenue: 50 Lakhs growing to 1 Crore
    net_revenue = {
        1: 500000000,
        2: 600000000,
        3: 700000000,
        4: 800000000,
        5: 900000000,
        6: 950000000,
        7: 1000000000,
    }
    # Raw material cost: 40% of revenue
    material_cost = {seq: int(rev * 0.40) for seq, rev in net_revenue.items()}
    other_direct = {seq: int(rev * 0.05) for seq, rev in net_revenue.items()}
    employee_cost = {seq: int(rev * 0.15) for seq, rev in net_revenue.items()}
    admin_cost = {seq: int(rev * 0.05) for seq, rev in net_revenue.items()}
    selling_cost = {seq: int(rev * 0.03) for seq, rev in net_revenue.items()}

    # Total capex in Year 1: 50 Lakhs (500000000 paise)
    total_capex = {1: 500000000, 2: 0, 3: 0, 4: 0, 5: 0, 6: 0, 7: 0}

    # Funding: Term loan 35 Lakhs, Promoter Equity 15 Lakhs
    term_loan_sanctioned = 350000000
    equity_introduced = {1: 150000000, 2: 0, 3: 0, 4: 0, 5: 0, 6: 0, 7: 0}

    wc_assumptions = WorkingCapitalAssumptions(
        rm_holding_days=Decimal("30"),
        wip_holding_days=Decimal("7"),
        fg_holding_days=Decimal("15"),
        debtor_collection_days=Decimal("45"),
        creditor_payment_days=Decimal("30"),
        bank_margin_pct=Decimal("25.0"),
    )

    statements = StatementPipeline.run_projection(
        period_definitions=periods,
        constitution_code=ConstitutionCode.PRIVATE_LIMITED,
        net_revenue_by_period=net_revenue,
        material_cost_by_period=material_cost,
        other_direct_cost_by_period=other_direct,
        employee_cost_by_period=employee_cost,
        admin_cost_by_period=admin_cost,
        selling_cost_by_period=selling_cost,
        total_capex_by_period=total_capex,
        asset_useful_life_years=Decimal("10"),
        promoter_equity_introduced_by_period=equity_introduced,
        term_loan_sanctioned_paise=term_loan_sanctioned,
        term_loan_interest_rate_pct=Decimal("11.5"),
        term_loan_tenure_months=84,
        term_loan_moratorium_months=0,
        wc_assumptions=wc_assumptions,
    )

    assert len(statements) == 7
    for stmt in statements:
        assert stmt.balance_difference_paise == 0, (
            f"Period {stmt.period_sequence} out of balance: {stmt.balance_difference_paise} paise"
        )
        assert stmt.bs_total_assets_paise == stmt.bs_total_liabilities_and_equity_paise
        assert stmt.bs_net_worth_paise > 0
