"""Equity, Partner Capital, and Net Worth roll-forward engine by constitution."""

from dataclasses import dataclass
from decimal import Decimal
from typing import Optional
from uuid import UUID

from app.common.types import ConstitutionCode


@dataclass
class PeriodEquityMovement:
    """Calculated net worth / capital roll-forward for a period."""
    period_id: UUID
    period_sequence: int
    constitution_code: ConstitutionCode

    # Common roll-forward components
    opening_equity_paise: int
    capital_introduced_paise: int
    profit_after_tax_paise: int
    drawings_or_dividends_paise: int
    closing_equity_paise: int

    # Corporate specific breakdown (if Company)
    share_capital_paise: int = 0
    reserves_and_surplus_paise: int = 0


class EquityRollForwardCalculator:
    """Maintains exact capital roll-forwards for all 6 Indian legal constitutions."""

    @staticmethod
    def calculate_movement(
        period_id: UUID,
        period_sequence: int,
        constitution_code: ConstitutionCode,
        opening_equity_paise: int,
        capital_introduced_paise: int,
        profit_after_tax_paise: int,
        drawings_or_dividends_paise: int = 0,
        initial_share_capital_paise: int = 0,
    ) -> PeriodEquityMovement:
        """Rolls forward equity preserving fundamental balance sheet integrity."""
        # Closing Equity = Opening + Fresh Capital + PAT - Drawings/Dividends
        closing_equity = (
            opening_equity_paise
            + capital_introduced_paise
            + profit_after_tax_paise
            - drawings_or_dividends_paise
        )

        share_cap = 0
        reserves = 0

        if constitution_code == ConstitutionCode.PRIVATE_LIMITED:
            # Share capital = Initial + fresh issues
            share_cap = initial_share_capital_paise + capital_introduced_paise
            # Reserves & Surplus is the retained earnings portion
            reserves = closing_equity - share_cap
        else:
            # Sole proprietorship, partnership, LLP, HUF, Individual
            share_cap = closing_equity
            reserves = 0

        return PeriodEquityMovement(
            period_id=period_id,
            period_sequence=period_sequence,
            constitution_code=constitution_code,
            opening_equity_paise=opening_equity_paise,
            capital_introduced_paise=capital_introduced_paise,
            profit_after_tax_paise=profit_after_tax_paise,
            drawings_or_dividends_paise=drawings_or_dividends_paise,
            closing_equity_paise=closing_equity,
            share_capital_paise=share_cap,
            reserves_and_surplus_paise=reserves,
        )
