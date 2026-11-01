"""Data transfer objects for Funding and Means of Finance."""

from dataclasses import dataclass
from decimal import Decimal
from typing import Optional
from uuid import UUID


@dataclass
class FundingHeadDTO:
    id: UUID
    funding_code: str
    funding_name: str
    funding_category: str
    sort_order: int


@dataclass
class FundingSourceDTO:
    id: UUID
    scenario_id: UUID
    funding_head_id: UUID
    funding_head_name: str
    source_name: str
    amount_rupees: Decimal
    status_code: str
    terms_note: Optional[str] = None
    notes: Optional[str] = None


@dataclass
class FundingReconciliationDTO:
    total_project_cost_rupees: Decimal
    total_funding_sources_rupees: Decimal
    funding_gap_rupees: Decimal
    is_balanced: bool
    promoter_contribution_rupees: Decimal
    term_debt_rupees: Decimal
    debt_equity_ratio: str
