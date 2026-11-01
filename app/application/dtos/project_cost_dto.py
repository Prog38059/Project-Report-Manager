"""Data transfer objects for Project Cost."""

from dataclasses import dataclass
from decimal import Decimal
from typing import Optional
from uuid import UUID


@dataclass
class CostHeadDTO:
    id: UUID
    head_code: str
    head_name: str
    category_code: str
    capitalisation_default: bool
    sort_order: int


@dataclass
class CostItemDTO:
    id: UUID
    scenario_id: UUID
    cost_head_id: UUID
    cost_head_name: str
    description: str
    basic_amount_rupees: Decimal
    gst_rate_pct: Optional[Decimal]
    gst_amount_rupees: Decimal
    eligible_itc_rupees: Decimal
    non_creditable_tax_rupees: Decimal
    capitalised_amount_rupees: Decimal
    project_cash_requirement_rupees: Decimal
    quantity_text: Optional[str] = None
    unit_code: Optional[str] = None
    rate_text: Optional[str] = None
    supplier_name: Optional[str] = None
    notes: Optional[str] = None


@dataclass
class CostSummaryDTO:
    total_basic_rupees: Decimal
    total_gst_rupees: Decimal
    total_eligible_itc_rupees: Decimal
    total_non_creditable_tax_rupees: Decimal
    total_capitalised_rupees: Decimal
    total_cash_requirement_rupees: Decimal
