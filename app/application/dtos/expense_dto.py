"""Data transfer objects for Operating Expenses."""

from dataclasses import dataclass
from decimal import Decimal
from typing import Optional
from uuid import UUID


@dataclass
class ExpenseHeadDTO:
    id: UUID
    expense_code: str
    expense_name: str
    expense_group: str
    default_cost_behaviour: str
    default_projection_method: str
    sort_order: int


@dataclass
class ExpenseForecastPeriodDTO:
    id: UUID
    scenario_id: UUID
    expense_head_id: UUID
    expense_head_name: str
    expense_group: str
    period_id: UUID
    period_label: str
    period_sequence: int
    projection_method: str
    projected_amount_rupees: Decimal
    growth_pct_text: Optional[str]
    revenue_pct_text: Optional[str]
    unit_cost_text: Optional[str]
    notes: Optional[str]
