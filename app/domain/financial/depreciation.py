"""Asset and depreciation calculation engine.

Implements pure domain calculations for book depreciation (SLM, WDV)
and Income Tax Act 1961 block depreciation.
"""

from dataclasses import dataclass
from decimal import Decimal
from typing import List, Optional
from uuid import UUID

from app.common.exceptions import ValidationError
from app.common.money import paise_to_rupees, rupees_to_paise


@dataclass
class AssetAdditionInput:
    """Asset addition parameters for a reporting period."""
    period_id: UUID
    period_sequence: int
    gross_addition_paise: int
    eligible_itc_paise: int = 0
    non_creditable_tax_paise: int = 0
    residual_value_paise: int = 0
    useful_life_years: Decimal = Decimal("10")
    book_method: str = "SLM"  # SLM or WDV
    wdv_rate_pct: Optional[Decimal] = None
    tax_rate_pct: Decimal = Decimal("15.0")  # Income tax block rate e.g. 15% for plant, 10% for building
    put_to_use_days_in_period: Optional[int] = None
    days_in_period: int = 365
    is_used_less_than_180_days: bool = False  # Income Tax Sec 32 half-rate rule


@dataclass
class PeriodDepreciationResult:
    """Calculated depreciation results for an asset in one period."""
    period_id: UUID
    period_sequence: int
    # Book depreciation (Companies Act / Financial Reporting)
    book_opening_gross_paise: int
    book_additions_paise: int
    book_closing_gross_paise: int
    book_opening_accum_dep_paise: int
    book_depreciation_paise: int
    book_closing_accum_dep_paise: int
    book_net_block_paise: int

    # Tax depreciation (Income Tax Act 1961)
    tax_opening_wdv_paise: int
    tax_additions_full_rate_paise: int
    tax_additions_half_rate_paise: int
    tax_depreciation_paise: int
    tax_closing_wdv_paise: int


def calculate_slm_depreciation(
    capitalised_cost_paise: int,
    residual_value_paise: int,
    useful_life_years: Decimal,
    time_proportion: Decimal = Decimal("1"),
) -> int:
    """
    Straight-Line Method (SLM) book depreciation in integer paise.
    Depreciation = ((Cost - Residual) / Life) * time_proportion
    """
    if not isinstance(useful_life_years, Decimal):
        raise TypeError("useful_life_years must be Decimal")
    if not isinstance(time_proportion, Decimal):
        raise TypeError("time_proportion must be Decimal")
    if useful_life_years <= Decimal("0"):
        raise ValidationError("useful_life_years must be positive.")
    if time_proportion < Decimal("0"):
        raise ValidationError("time_proportion cannot be negative.")

    depreciable_paise = Decimal(max(0, capitalised_cost_paise - residual_value_paise))
    annual_dep = depreciable_paise / useful_life_years
    period_dep = annual_dep * time_proportion
    return int(period_dep.quantize(Decimal("1")))


def calculate_wdv_depreciation(
    opening_carrying_paise: int,
    rate_pct: Decimal,
    time_proportion: Decimal = Decimal("1"),
) -> int:
    """
    Written Down Value (WDV) depreciation in integer paise.
    Depreciation = Opening Carrying Amount * (Rate / 100) * time_proportion
    """
    if not isinstance(rate_pct, Decimal):
        raise TypeError("rate_pct must be Decimal")
    if not isinstance(time_proportion, Decimal):
        raise TypeError("time_proportion must be Decimal")

    opening_dec = Decimal(max(0, opening_carrying_paise))
    dep = opening_dec * (rate_pct / Decimal("100")) * time_proportion
    dep_paise = int(dep.quantize(Decimal("1")))
    return min(opening_carrying_paise, dep_paise)


class AssetScheduleCalculator:
    """Calculates multi-year asset roll-forward for book and tax schedules."""

    @staticmethod
    def calculate_schedule(
        additions: List[AssetAdditionInput],
        initial_book_gross_paise: int = 0,
        initial_book_accum_dep_paise: int = 0,
        initial_tax_wdv_paise: int = 0,
    ) -> List[PeriodDepreciationResult]:
        """Calculates multi-period asset schedule preserving exact balances."""
        results: List[PeriodDepreciationResult] = []

        curr_book_gross = initial_book_gross_paise
        curr_book_accum = initial_book_accum_dep_paise
        curr_tax_wdv = initial_tax_wdv_paise

        # Sort chronologically by period sequence
        sorted_inputs = sorted(additions, key=lambda a: a.period_sequence)

        for inp in sorted_inputs:
            # Capitalised cost = Basic cost + Non-creditable taxes (ITC is excluded)
            new_capitalised = inp.gross_addition_paise + inp.non_creditable_tax_paise - inp.eligible_itc_paise
            new_capitalised = max(0, new_capitalised)

            # --- 1. Book Depreciation ---
            opening_gross = curr_book_gross
            closing_gross = opening_gross + new_capitalised
            opening_accum = curr_book_accum

            # Time proportion
            if inp.put_to_use_days_in_period is not None and inp.days_in_period > 0:
                time_prop = Decimal(inp.put_to_use_days_in_period) / Decimal(inp.days_in_period)
            else:
                time_prop = Decimal("1")

            if inp.book_method == "WDV" and inp.wdv_rate_pct is not None:
                opening_net = max(0, opening_gross - opening_accum)
                book_dep = calculate_wdv_depreciation(opening_net + new_capitalised, inp.wdv_rate_pct, time_prop)
            else:
                # Default SLM
                book_dep = calculate_slm_depreciation(
                    capitalised_cost_paise=closing_gross,
                    residual_value_paise=inp.residual_value_paise,
                    useful_life_years=inp.useful_life_years,
                    time_proportion=time_prop,
                )

            # Cap book depreciation so net block does not go below residual
            current_net_before_dep = closing_gross - opening_accum
            max_dep_allowed = max(0, current_net_before_dep - inp.residual_value_paise)
            book_dep = min(book_dep, max_dep_allowed)

            closing_accum = opening_accum + book_dep
            closing_net_block = closing_gross - closing_accum

            # Update book carry forward
            curr_book_gross = closing_gross
            curr_book_accum = closing_accum

            # --- 2. Income Tax Act 1961 Block Depreciation ---
            tax_opening = curr_tax_wdv
            tax_rate = inp.tax_rate_pct / Decimal("100")

            if inp.is_used_less_than_180_days:
                add_half = new_capitalised
                add_full = 0
                tax_dep_from_add = Decimal(add_half) * (tax_rate / Decimal("2"))
            else:
                add_full = new_capitalised
                add_half = 0
                tax_dep_from_add = Decimal(add_full) * tax_rate

            tax_dep_from_opening = Decimal(tax_opening) * tax_rate
            total_tax_dep_dec = tax_dep_from_opening + tax_dep_from_add
            tax_dep = int(total_tax_dep_dec.quantize(Decimal("1")))

            total_block = tax_opening + new_capitalised
            tax_dep = min(tax_dep, total_block)
            tax_closing = total_block - tax_dep

            curr_tax_wdv = tax_closing

            results.append(
                PeriodDepreciationResult(
                    period_id=inp.period_id,
                    period_sequence=inp.period_sequence,
                    book_opening_gross_paise=opening_gross,
                    book_additions_paise=new_capitalised,
                    book_closing_gross_paise=closing_gross,
                    book_opening_accum_dep_paise=opening_accum,
                    book_depreciation_paise=book_dep,
                    book_closing_accum_dep_paise=closing_accum,
                    book_net_block_paise=closing_net_block,
                    tax_opening_wdv_paise=tax_opening,
                    tax_additions_full_rate_paise=add_full,
                    tax_additions_half_rate_paise=add_half,
                    tax_depreciation_paise=tax_dep,
                    tax_closing_wdv_paise=tax_closing,
                )
            )

        return results
