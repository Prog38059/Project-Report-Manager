"""Expense domain entities and projection models."""

from dataclasses import dataclass
from decimal import Decimal
from typing import Optional
from uuid import UUID

from app.common.exceptions import ValidationError
from app.common.money import rupees_to_paise
from app.common.types import CostBehaviour, ExpenseGroup, ExpenseProjectionMethod


@dataclass
class ExpenseHead:
    """Operating expense head definition."""
    id: UUID
    expense_code: str
    expense_name: str
    expense_group: ExpenseGroup
    default_cost_behaviour: CostBehaviour
    default_projection_method: ExpenseProjectionMethod
    sort_order: int = 0
    active_flag: bool = True

    def __post_init__(self):
        if not self.expense_code or not self.expense_code.strip():
            raise ValidationError("Expense code cannot be empty.")
        if not self.expense_name or not self.expense_name.strip():
            raise ValidationError("Expense name cannot be empty.")


@dataclass
class ExpenseForecast:
    """Forecast record for an expense head and period."""
    id: UUID
    scenario_id: UUID
    expense_head_id: UUID
    period_id: UUID
    projection_method: ExpenseProjectionMethod
    base_amount_paise: Optional[int] = None
    growth_pct_text: Optional[str] = None
    revenue_pct_text: Optional[str] = None
    unit_cost_decimal_text: Optional[str] = None
    quantity_driver_code: Optional[str] = None
    manual_amount_paise: Optional[int] = None
    source_id: Optional[UUID] = None
    notes: Optional[str] = None

    @classmethod
    def calculate_expense_amount(
        cls,
        projection_method: ExpenseProjectionMethod,
        base_amount_paise: Optional[int] = None,
        prior_amount_paise: Optional[int] = None,
        growth_pct: Optional[Decimal] = None,
        revenue_pct: Optional[Decimal] = None,
        projected_net_revenue_paise: Optional[int] = None,
        unit_cost_rupees: Optional[Decimal] = None,
        driver_quantity: Optional[Decimal] = None,
        manual_amount_paise: Optional[int] = None,
    ) -> int:
        """
        Calculates projected expense in integer paise.
        """
        if projection_method == ExpenseProjectionMethod.MANUAL:
            if manual_amount_paise is None or manual_amount_paise < 0:
                raise ValidationError("Manual expense amount cannot be negative.")
            return manual_amount_paise

        if projection_method == ExpenseProjectionMethod.FIXED_AMOUNT:
            return base_amount_paise or 0

        if projection_method == ExpenseProjectionMethod.GROWTH:
            prior = Decimal(prior_amount_paise or base_amount_paise or 0)
            growth = (growth_pct or Decimal("0")) / Decimal("100")
            amount_dec = prior * (Decimal("1") + growth)
            return int(amount_dec.quantize(Decimal("1")))

        if projection_method == ExpenseProjectionMethod.PERCENT_REVENUE:
            rev_paise = projected_net_revenue_paise or 0
            pct = (revenue_pct or Decimal("0")) / Decimal("100")
            amount_dec = Decimal(rev_paise) * pct
            return int(amount_dec.quantize(Decimal("1")))

        if projection_method in (
            ExpenseProjectionMethod.PER_UNIT,
            ExpenseProjectionMethod.CAPACITY_BASED,
            ExpenseProjectionMethod.HEADCOUNT_BASED,
        ):
            cost = unit_cost_rupees or Decimal("0")
            qty = driver_quantity or Decimal("0")
            total_rupees = cost * qty
            return rupees_to_paise(total_rupees)

        return base_amount_paise or 0
