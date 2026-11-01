"""Funding and Means of Finance domain entities and reconciliation."""

from dataclasses import dataclass
from datetime import date
from typing import Optional
from uuid import UUID

from app.common.exceptions import ValidationError
from app.common.types import FundingCategory, FundingStatus


@dataclass
class FundingHead:
    """Category / head of funding (promoter, term loan, subsidy, etc.)."""
    id: UUID
    funding_code: str
    funding_name: str
    funding_category: FundingCategory
    sort_order: int
    active_flag: bool = True

    def __post_init__(self):
        if not self.funding_code or not self.funding_code.strip():
            raise ValidationError("Funding code cannot be empty.")
        if not self.funding_name or not self.funding_name.strip():
            raise ValidationError("Funding name cannot be empty.")


@dataclass
class FundingSource:
    """Individual funding line item."""
    id: UUID
    scenario_id: UUID
    funding_head_id: UUID
    source_name: str
    amount_paise: int
    expected_date: Optional[date] = None
    status_code: FundingStatus = FundingStatus.PROPOSED
    loan_facility_id: Optional[UUID] = None
    source_id: Optional[UUID] = None
    terms_note: Optional[str] = None
    notes: Optional[str] = None

    def __post_init__(self):
        if not self.source_name or not self.source_name.strip():
            raise ValidationError("Funding source name cannot be empty.")
        if self.amount_paise < 0:
            raise ValidationError("Funding amount cannot be negative.")


@dataclass
class FundingReconciliation:
    """Reconciliation between Total Project Cost (Uses) and Total Means of Finance (Sources)."""
    total_project_cost_paise: int
    total_funding_sources_paise: int
    promoter_contribution_paise: int
    term_debt_paise: int
    other_funding_paise: int

    @property
    def funding_gap_paise(self) -> int:
        """Surplus if negative, deficit (unfunded gap) if positive."""
        return self.total_project_cost_paise - self.total_funding_sources_paise

    @property
    def is_balanced(self) -> bool:
        return self.funding_gap_paise == 0

    @property
    def debt_equity_ratio_text(self) -> str:
        """Term debt divided by promoter contribution."""
        if self.promoter_contribution_paise == 0:
            return "N/A" if self.term_debt_paise == 0 else "Infinity"
        ratio = self.term_debt_paise / self.promoter_contribution_paise
        return f"{ratio:.2f} : 1"
