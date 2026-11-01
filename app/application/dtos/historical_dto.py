"""Data transfer objects for Historical Financial Statements."""

from dataclasses import dataclass
from decimal import Decimal
from typing import Optional
from uuid import UUID


@dataclass
class HistoricalLineDTO:
    id: UUID
    project_id: UUID
    period_id: UUID
    period_label: str
    statement_type: str
    line_code: str
    line_label: str
    amount_rupees: Decimal
    is_imported: bool
    mapping_status: str
    notes: Optional[str]
