"""Historical Financial Statement domain entity."""

from dataclasses import dataclass
from typing import Optional
from uuid import UUID

from app.common.exceptions import ValidationError
from app.common.types import MappingStatus, StatementType


@dataclass
class HistoricalStatementLine:
    """Historical financial line item (P&L, BS, or Cash Flow) for a historical year."""
    id: UUID
    project_id: UUID
    period_id: UUID
    statement_type: StatementType
    line_code: str
    line_label: str
    amount_paise: int
    source_id: Optional[UUID] = None
    is_imported: bool = False
    mapping_status: MappingStatus = MappingStatus.UNREVIEWED
    notes: Optional[str] = None

    def __post_init__(self):
        if not self.line_code or not self.line_code.strip():
            raise ValidationError("Line code cannot be empty.")
        if not self.line_label or not self.line_label.strip():
            raise ValidationError("Line label cannot be empty.")
