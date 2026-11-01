"""Unit tests for exact monetary conversions and arithmetic."""

from decimal import Decimal
import pytest

from app.common.money import rupees_to_paise, paise_to_rupees, format_inr


def test_rupees_to_paise_exact():
    assert rupees_to_paise(Decimal("100.00")) == 10000
    assert rupees_to_paise(Decimal("0.50")) == 50
    assert rupees_to_paise("1250.75") == 125075
    assert rupees_to_paise(500) == 50000


def test_rupees_to_paise_half_up_rounding():
    # 0.005 should round to 0.01 (1 paisa)
    assert rupees_to_paise(Decimal("0.005")) == 1
    assert rupees_to_paise(Decimal("0.004")) == 0


def test_float_rejection():
    # STRICT RULE: Binary float must be rejected
    with pytest.raises(TypeError, match="Binary float is strictly prohibited"):
        rupees_to_paise(125.50)  # type: ignore

    with pytest.raises(TypeError, match="Binary float is strictly prohibited"):
        format_inr(125.50)  # type: ignore


def test_paise_to_rupees():
    assert paise_to_rupees(10000) == Decimal("100.00")
    assert paise_to_rupees(50) == Decimal("0.50")
    assert paise_to_rupees(0) == Decimal("0.00")


def test_format_inr_indian_grouping():
    # Standard Indian comma grouping
    assert format_inr(Decimal("100000.00")) == "1,00,000.00"
    assert format_inr(Decimal("10000000.00")) == "1,00,00,000.00"
    assert format_inr(Decimal("1234567.89")) == "12,34,567.89"
    assert format_inr(Decimal("500")) == "500.00"


def test_format_inr_negative():
    # Standard accounting parentheses for negative values
    assert format_inr(Decimal("-50000.00")) == "(50,000.00)"
    assert format_inr(Decimal("-1234567.89")) == "(12,34,567.89)"
