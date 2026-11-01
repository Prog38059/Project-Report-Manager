"""Unit tests for Phase 2 financial formulas, cost calculations, and revenue drivers."""

from decimal import Decimal
import pytest

from app.common.exceptions import ValidationError
from app.common.types import (
    CostCategory,
    GstTreatmentCode,
    RevenueCalculationMode,
    RevenueMethodCode,
    ExpenseProjectionMethod,
)
from app.domain.entities.funding import FundingReconciliation
from app.domain.entities.project_cost import ProjectCostItem
from app.domain.entities.revenue import RevenueForecast
from app.domain.entities.expense import ExpenseForecast


def test_project_cost_with_full_itc():
    """Capital asset with 100% eligible ITC should not capitalise GST into asset cost."""
    basic = Decimal("1000000.00")  # 10 Lakhs
    gst_rate = Decimal("18.00")
    itc_pct = Decimal("100.00")

    res = ProjectCostItem.calculate_item_amounts(
        basic_rupees=basic,
        gst_rate_pct=gst_rate,
        itc_eligibility_pct=itc_pct,
        is_capitalisable=True,
    )

    assert res["basic_amount_paise"] == 100000000
    assert res["gst_amount_paise"] == 18000000
    assert res["eligible_itc_paise"] == 18000000
    assert res["non_creditable_tax_paise"] == 0
    assert res["capitalised_amount_paise"] == 100000000  # Only basic cost
    assert res["project_cash_requirement_paise"] == 118000000  # Full gross invoice paid


def test_project_cost_with_zero_itc_non_creditable():
    """Asset with 0% ITC (blocked under Sec 17(5) or uncreditable) must capitalise GST into cost."""
    basic = Decimal("1000000.00")
    gst_rate = Decimal("18.00")
    itc_pct = Decimal("0.00")

    res = ProjectCostItem.calculate_item_amounts(
        basic_rupees=basic,
        gst_rate_pct=gst_rate,
        itc_eligibility_pct=itc_pct,
        is_capitalisable=True,
    )

    assert res["basic_amount_paise"] == 100000000
    assert res["gst_amount_paise"] == 18000000
    assert res["eligible_itc_paise"] == 0
    assert res["non_creditable_tax_paise"] == 18000000
    assert res["capitalised_amount_paise"] == 118000000  # Basic + Non-creditable tax
    assert res["project_cash_requirement_paise"] == 118000000


def test_project_cost_non_capitalisable_deposit():
    """Security deposit / pre-operative cost flagged non-capitalisable has capitalised amount 0."""
    basic = Decimal("250000.00")

    res = ProjectCostItem.calculate_item_amounts(
        basic_rupees=basic,
        gst_rate_pct=None,
        itc_eligibility_pct=None,
        is_capitalisable=False,
    )

    assert res["basic_amount_paise"] == 25000000
    assert res["gst_amount_paise"] == 0
    assert res["capitalised_amount_paise"] == 0
    assert res["project_cash_requirement_paise"] == 25000000


def test_project_cost_float_rejection():
    """Float must be strictly rejected per financial integrity rules."""
    with pytest.raises(TypeError):
        ProjectCostItem.calculate_item_amounts(
            basic_rupees=100000.0,  # float error!
            gst_rate_pct=Decimal("18.0"),
            itc_eligibility_pct=Decimal("100.0"),
            is_capitalisable=True,
        )


def test_funding_reconciliation_balanced_and_debt_equity():
    """Reconciliation verifies balanced sources/uses and correct D/E ratio."""
    recon = FundingReconciliation(
        total_project_cost_paise=500000000,      # ₹50 Lakhs
        total_funding_sources_paise=500000000,   # ₹50 Lakhs
        promoter_contribution_paise=200000000,   # ₹20 Lakhs
        term_debt_paise=300000000,               # ₹30 Lakhs
        other_funding_paise=0,
    )

    assert recon.is_balanced is True
    assert recon.funding_gap_paise == 0
    assert recon.debt_equity_ratio_text == "1.50 : 1"


def test_funding_reconciliation_gap_and_surplus():
    """Reconciliation detects deficit (gap) and surplus."""
    # Deficit
    recon_deficit = FundingReconciliation(
        total_project_cost_paise=500000000,
        total_funding_sources_paise=400000000,
        promoter_contribution_paise=100000000,
        term_debt_paise=300000000,
        other_funding_paise=0,
    )
    assert recon_deficit.is_balanced is False
    assert recon_deficit.funding_gap_paise == 100000000  # ₹10 Lakhs deficit

    # Surplus
    recon_surplus = FundingReconciliation(
        total_project_cost_paise=500000000,
        total_funding_sources_paise=550000000,
        promoter_contribution_paise=250000000,
        term_debt_paise=300000000,
        other_funding_paise=0,
    )
    assert recon_surplus.is_balanced is False
    assert recon_surplus.funding_gap_paise == -50000000  # ₹5 Lakhs surplus


def test_revenue_capacity_utilisation_formula():
    """Capacity x Utilisation x Operating Days x Rate."""
    res = RevenueForecast.calculate_stream_period(
        method_code=RevenueMethodCode.CAPACITY_UTILISATION_PRICE,
        gst_treatment=GstTreatmentCode.TAXABLE_EXCLUSIVE,
        gst_rate_pct=Decimal("18.00"),
        calculation_mode=RevenueCalculationMode.DRIVER,
        capacity=Decimal("100"),        # 100 units/day
        utilisation_pct=Decimal("80"),  # 80%
        operating_days=Decimal("300"),  # 300 days/year -> 24,000 units
        price_per_unit=Decimal("50.00"), # ₹50/unit -> Net ₹12,00,000
    )

    assert res["net_revenue_paise"] == 120000000      # ₹12,00,000
    assert res["output_tax_paise"] == 21600000        # ₹2,16,000 (18%)
    assert res["gross_billing_paise"] == 141600000    # ₹14,16,000


def test_revenue_inclusive_tax_formula():
    """Inclusive tax splits gross collection into net revenue and output GST without losing paise."""
    res = RevenueForecast.calculate_stream_period(
        method_code=RevenueMethodCode.MANUAL,
        gst_treatment=GstTreatmentCode.TAXABLE_INCLUSIVE,
        gst_rate_pct=Decimal("18.00"),
        calculation_mode=RevenueCalculationMode.MANUAL_OVERRIDE,
        manual_override_paise=11800000,  # ₹1,18,000
    )

    assert res["gross_billing_paise"] == 11800000
    assert res["net_revenue_paise"] == 10000000       # ₹1,00,000
    assert res["output_tax_paise"] == 1800000         # ₹18,000


def test_revenue_exempt_and_nil_rated():
    """Exempt revenue streams must have 0 output GST."""
    res = RevenueForecast.calculate_stream_period(
        method_code=RevenueMethodCode.UNITS_PRICE,
        gst_treatment=GstTreatmentCode.EXEMPT,
        gst_rate_pct=Decimal("18.00"),  # even if rate is present, exempt means 0 tax
        calculation_mode=RevenueCalculationMode.DRIVER,
        units=Decimal("1000"),
        price_per_unit=Decimal("250.00"),
    )

    assert res["gross_billing_paise"] == 25000000
    assert res["output_tax_paise"] == 0
    assert res["net_revenue_paise"] == 25000000


def test_expense_forecasting_methods():
    """Operating expense calculations for fixed, growth, and percent of revenue."""
    # Fixed
    fixed = ExpenseForecast.calculate_expense_amount(
        projection_method=ExpenseProjectionMethod.FIXED_AMOUNT,
        base_amount_paise=5000000,
    )
    assert fixed == 5000000

    # Growth
    growth = ExpenseForecast.calculate_expense_amount(
        projection_method=ExpenseProjectionMethod.GROWTH,
        prior_amount_paise=5000000,
        growth_pct=Decimal("10.0"),
    )
    assert growth == 5500000

    # Percent of revenue
    pct_rev = ExpenseForecast.calculate_expense_amount(
        projection_method=ExpenseProjectionMethod.PERCENT_REVENUE,
        projected_net_revenue_paise=100000000,  # ₹10 Lakhs
        revenue_pct=Decimal("5.0"),             # 5%
    )
    assert pct_rev == 5000000                   # ₹50,000
