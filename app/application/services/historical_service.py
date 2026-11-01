"""Application service for Historical Statements."""

from decimal import Decimal
from typing import List, Optional
import uuid

from app.application.dtos.historical_dto import HistoricalLineDTO
from app.common.money import paise_to_rupees, rupees_to_paise
from app.common.types import MappingStatus, StatementType
from app.domain.entities.historical_statement import HistoricalStatementLine
from app.infrastructure.database.connection import DatabaseManager
from app.infrastructure.repositories.historical_repository import HistoricalRepository
from app.infrastructure.repositories.project_repository import ProjectRepository


class HistoricalService:
    def __init__(self, db_manager: DatabaseManager) -> None:
        self.db_manager = db_manager

    def list_lines(self, project_id: uuid.UUID) -> List[HistoricalLineDTO]:
        with self.db_manager.session_scope() as session:
            hist_repo = HistoricalRepository(session)
            proj_repo = ProjectRepository(session)

            periods = {p.id: p for p in proj_repo.list_periods_for_project(project_id)}
            lines = hist_repo.list_lines_for_project(project_id)

            return [
                HistoricalLineDTO(
                    id=line.id,
                    project_id=line.project_id,
                    period_id=line.period_id,
                    period_label=periods[line.period_id].period_label if line.period_id in periods else "Period",
                    statement_type=line.statement_type,
                    line_code=line.line_code,
                    line_label=line.line_label,
                    amount_rupees=paise_to_rupees(line.amount_paise),
                    is_imported=line.is_imported,
                    mapping_status=line.mapping_status,
                    notes=line.notes,
                )
                for line in lines
            ]

    def save_line(
        self,
        project_id: uuid.UUID,
        period_id: uuid.UUID,
        statement_type: str,
        line_code: str,
        line_label: str,
        amount_rupees: Decimal,
        notes: Optional[str] = None,
        line_id: Optional[uuid.UUID] = None,
    ) -> HistoricalLineDTO:
        with self.db_manager.session_scope() as session:
            hist_repo = HistoricalRepository(session)
            entity = HistoricalStatementLine(
                id=line_id or uuid.uuid4(),
                project_id=project_id,
                period_id=period_id,
                statement_type=StatementType(statement_type),
                line_code=line_code.strip(),
                line_label=line_label.strip(),
                amount_paise=rupees_to_paise(amount_rupees),
                mapping_status=MappingStatus.UNREVIEWED,
                notes=notes,
            )
            saved = hist_repo.save_line(entity)
            return HistoricalLineDTO(
                id=saved.id,
                project_id=saved.project_id,
                period_id=saved.period_id,
                period_label="Period",
                statement_type=saved.statement_type,
                line_code=saved.line_code,
                line_label=saved.line_label,
                amount_rupees=paise_to_rupees(saved.amount_paise),
                is_imported=saved.is_imported,
                mapping_status=saved.mapping_status,
                notes=saved.notes,
            )
