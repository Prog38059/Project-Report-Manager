"""Project Cost domain entities and calculation rules."""

from dataclasses import dataclass
from decimal import Decimal
from typing import Optional
from uuid import UUID

from app.common.exceptions import ValidationError
from app.common.money import rupees_to_paise
from app.common.types import CostCategory


@dataclass
class ProjectCostHead:
    """Standard or custom project cost head."""
    id: UUID
    head_code: str
    head_name: str
    category_code: CostCategory
    capitalisation_default: bool
    sort_order: int
    active_flag: bool = True

    def __post_init__(self):
        if not self.head_code or not self.head_code.strip():
            raise ValidationError("Cost head code cannot be empty.")
        if not self.head_name or not self.head_name.strip():
            raise ValidationError("Cost head name cannot be empty.")


@dataclass
class ProjectCostItem:
    """Individual item within a project cost head."""
    id: UUID
    scenario_id: UUID
    cost_head_id: UUID
    description: str
    basic_amount_paise: int
    gst_rate_pct_text: Optional[str] = None
    gst_amount_paise: int = 0
    eligible_itc_paise: int = 0
    non_creditable_tax_paise: int = 0
    capitalised_amount_paise: int = 0
    project_cash_requirement_paise: int = 0
    quantity_decimal_text: Optional[str] = None
    unit_code: Optional[str] = None
    rate_decimal_text: Optional[str] = None
    supplier_name: Optional[str] = None
    source_id: Optional[UUID] = None
    notes: Optional[str] = None

    def __post_init__(self):
        if not self.description or not self.description.strip():
            raise ValidationError("Cost item description cannot be empty.")
        if self.basic_amount_paise < 0:
            raise ValidationError("Basic amount cannot be negative.")
        if self.gst_amount_paise < 0:
            raise ValidationError("GST amount cannot be negative.")
        if self.eligible_itc_paise < 0:
            raise ValidationError("Eligible ITC cannot be negative.")
        if self.eligible_itc_paise > self.gst_amount_paise:
            raise ValidationError("Eligible ITC cannot exceed total GST amount.")

    @classmethod
    def calculate_item_amounts(
        cls,
        basic_rupees: Decimal,
        gst_rate_pct: Optional[Decimal],
        itc_eligibility_pct: Optional[Decimal],
        is_capitalisable: bool,
    ) -> dict[str, int]:
        """
        Calculates exact paise amounts for basic, gst, itc, non-creditable, capitalised, and cash requirement.
        """
        if not isinstance(basic_rupees, Decimal):
            raise TypeError("basic_rupees must be Decimal")
        if basic_rupees < Decimal("0"):
            raise ValidationError("Basic amount cannot be negative.")

        basic_paise = rupees_to_paise(basic_rupees)

        gst_paise = 0
        if gst_rate_pct is not None and gst_rate_pct > Decimal("0"):
            if not isinstance(gst_rate_pct, Decimal):
                raise TypeError("gst_rate_pct must be Decimal")
            gst_rupees = basic_rupees * (gst_rate_pct / Decimal("100"))
            gst_paise = rupees_to_paise(gst_rupees)

        itc_paise = 0
        if itc_eligibility_pct is not None and itc_eligibility_pct > Decimal("0") and gst_paise > 0:
            if not isinstance(itc_eligibility_pct, Decimal):
                raise TypeError("itc_eligibility_pct must be Decimal")
            # Calculate eligible ITC proportional to eligibility percentage
            itc_rupees = (Decimal(gst_paise) / Decimal("100")) * (itc_eligibility_pct / Decimal("100"))
            itc_paise = rupees_to_paise(itc_rupees)
            if itc_paise > gst_paise:
                itc_paise = gst_paise

        non_creditable_paise = gst_paise - itc_paise

        # Capitalised amount includes non-creditable taxes if capitalisable
        capitalised_paise = (basic_paise + non_creditable_paise) if is_capitalisable else 0

        # Project cash requirement is the total gross invoice/estimate outflow
        cash_req_paise = basic_paise + gst_paise

        return {
            "basic_amount_paise": basic_paise,
            "gst_amount_paise": gst_paise,
            "eligible_itc_paise": itc_paise,
            "non_creditable_tax_paise": non_creditable_paise,
            "capitalised_amount_paise": capitalised_paise,
            "project_cash_requirement_paise": cash_req_paise,
        }
