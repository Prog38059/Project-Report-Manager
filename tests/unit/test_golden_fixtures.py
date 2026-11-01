"""Unit tests verifying external Golden Fixtures A, B, C, D, E."""

from decimal import Decimal
import json
from pathlib import Path

from app.common.money import rupees_to_paise
from app.domain.financial.depreciation import calculate_slm_depreciation
from app.domain.financial.loan_engine import calculate_monthly_interest_paise
from app.domain.financial.working_capital import calculate_net_working_capital_identity


FIXTURES_DIR = Path(__file__).resolve().parent.parent / "financial_test_cases"


def test_fixture_a_quantity_price_revenue():
    fixture_path = FIXTURES_DIR / "fixture_A_quantity_price_revenue.json"
    with open(fixture_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    quantity = Decimal(data["inputs"]["quantity"])
    price_rupees = Decimal(data["inputs"]["price_per_unit_rupees"])
    expected_paise = data["expected"]["net_revenue_paise"]

    # Basic calculation
    revenue_rupees = quantity * price_rupees
    revenue_paise = rupees_to_paise(revenue_rupees)

    assert revenue_paise == expected_paise


def test_fixture_b_inclusive_tax():
    fixture_path = FIXTURES_DIR / "fixture_B_inclusive_tax.json"
    with open(fixture_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    gross_rupees = Decimal(data["inputs"]["gross_inclusive_rupees"])
    rate_pct = Decimal(data["inputs"]["assumed_rate_percent"])
    expected_net_paise = data["expected"]["net_amount_paise"]
    expected_tax_paise = data["expected"]["tax_amount_paise"]

    # Decompose tax inclusive: Net = Gross / (1 + r/100)
    gross_paise = rupees_to_paise(gross_rupees)
    divisor = Decimal("1") + (rate_pct / Decimal("100"))
    net_paise = int((Decimal(gross_paise) / divisor).quantize(Decimal("1")))
    tax_paise = gross_paise - net_paise

    assert net_paise == expected_net_paise
    assert tax_paise == expected_tax_paise


def test_fixture_c_slm_depreciation():
    fixture_path = FIXTURES_DIR / "fixture_C_slm_depreciation.json"
    with open(fixture_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    cost_rupees = Decimal(data["inputs"]["capitalised_cost_rupees"])
    residual_rupees = Decimal(data["inputs"]["residual_value_rupees"])
    useful_life = Decimal(data["inputs"]["useful_life_years"])
    time_fraction = Decimal(data["inputs"]["time_fraction"])
    expected_dep_paise = data["expected"]["annual_depreciation_paise"]

    dep_paise = calculate_slm_depreciation(
        capitalised_cost_paise=rupees_to_paise(cost_rupees),
        residual_value_paise=rupees_to_paise(residual_rupees),
        useful_life_years=useful_life,
        time_proportion=time_fraction,
    )

    assert dep_paise == expected_dep_paise


def test_fixture_d_working_capital_identity():
    fixture_path = FIXTURES_DIR / "fixture_D_working_capital.json"
    with open(fixture_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    ca_rupees = Decimal(data["inputs"]["current_operating_assets_rupees"])
    cl_rupees = Decimal(data["inputs"]["current_operating_liabilities_rupees"])
    expected_nwc_paise = data["expected"]["net_working_capital_paise"]

    nwc_paise = calculate_net_working_capital_identity(
        current_assets_paise=rupees_to_paise(ca_rupees),
        current_liabilities_paise=rupees_to_paise(cl_rupees),
    )

    assert nwc_paise == expected_nwc_paise


def test_fixture_e_monthly_interest():
    fixture_path = FIXTURES_DIR / "fixture_E_monthly_interest.json"
    with open(fixture_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    principal_rupees = Decimal(data["inputs"]["opening_principal_rupees"])
    rate_pct = Decimal(data["inputs"]["annual_nominal_rate_percent"])
    expected_rate = Decimal(data["expected"]["periodic_rate"])
    expected_interest_paise = data["expected"]["interest_paise"]

    periodic_rate = (rate_pct / Decimal("100")) / Decimal("12")
    assert periodic_rate == expected_rate

    interest_paise = calculate_monthly_interest_paise(
        opening_principal_paise=rupees_to_paise(principal_rupees),
        annual_rate_pct=rate_pct,
    )

    assert interest_paise == expected_interest_paise
