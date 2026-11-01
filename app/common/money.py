"""Monetary conversions and exact Decimal arithmetic utilities.

STRICT RULE: Never use Python binary float for money.
Always convert between exact Decimal rupees and integer paise (BIGINT).
"""

from decimal import Decimal, ROUND_HALF_UP
from typing import Union


PAISE_FACTOR = Decimal("100")
ROUNDING_CENTS = Decimal("1")


def rupees_to_paise(rupees: Union[Decimal, str, int]) -> int:
    """Convert rupee amount (Decimal, string or integer) to exact integer paise.

    Binary floats are explicitly forbidden to prevent floating-point contamination.
    """
    if isinstance(rupees, float):
        raise TypeError("Binary float is strictly prohibited for monetary values. Use Decimal, str, or int.")

    dec_val = Decimal(str(rupees)) if not isinstance(rupees, Decimal) else rupees
    paise_val = (dec_val * PAISE_FACTOR).quantize(ROUNDING_CENTS, rounding=ROUND_HALF_UP)
    return int(paise_val)


def paise_to_rupees(paise: int) -> Decimal:
    """Convert integer paise to exact Decimal rupees with two decimal places."""
    if not isinstance(paise, int):
        raise TypeError(f"Paise value must be an integer, got {type(paise).__name__}")
    return (Decimal(paise) / PAISE_FACTOR).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def format_inr(value: Union[Decimal, int, str], decimals: int = 2) -> str:
    """Formats a rupee amount into Indian currency format (e.g. 10,00,000.00).

    Negative values are formatted in standard financial notation with parentheses.
    """
    if isinstance(value, float):
        raise TypeError("Binary float is strictly prohibited. Pass Decimal, int, or str.")

    dec_val = Decimal(str(value)) if not isinstance(value, Decimal) else value
    is_negative = dec_val < 0
    dec_val = abs(dec_val)

    # Quantize to required decimals
    quant_format = "0." + "0" * decimals if decimals > 0 else "0"
    quantized = dec_val.quantize(Decimal(quant_format), rounding=ROUND_HALF_UP)

    parts = str(quantized).split(".")
    integer_part = parts[0]
    decimal_part = parts[1] if len(parts) > 1 else ""

    # Indian numbering comma grouping: last 3 digits, then groups of 2 digits
    if len(integer_part) > 3:
        last3 = integer_part[-3:]
        remaining = integer_part[:-3]
        groups = []
        while remaining:
            groups.insert(0, remaining[-2:])
            remaining = remaining[:-2]
        formatted_int = ",".join(groups) + "," + last3
    else:
        formatted_int = integer_part

    result = f"{formatted_int}.{decimal_part}" if decimals > 0 else formatted_int
    if is_negative:
        return f"({result})"
    return result
