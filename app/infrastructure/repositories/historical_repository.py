"""Repository for Historical Financial Statement Lines."""

from datetime import datetime, timezone
from typing import List
import uuid
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.domain.entities.historical_statement import HistoricalStatementLine
from app.infrastructure.database.models.historical_model import HistoricalStatementLineModel


class HistoricalRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    @staticmethod
    def _to_entity(model: HistoricalStatementLineModel) -> HistoricalStatementLine:
        return HistoricalStatementLine(
            id=model.id,
            project_id=model.project_id,
            period_id=model.period_id,
            statement_type=model.statement_type,
            line_code=model.line_code,
            line_label=model.line_label,
            amount_paise=model.amount_paise,
            source_id=model.source_id,
            is_imported=model.is_imported,
            mapping_status=model.mapping_status,
            notes=model.notes,
        )

    def list_lines_for_project(self, project_id: uuid.UUID) -> List[HistoricalStatementLine]:
        stmt = (
            select(HistoricalStatementLineModel)
            .where(HistoricalStatementLineModel.project_id == project_id)
            .order_by(HistoricalStatementLineModel.statement_type, HistoricalStatementLineModel.line_code)
        )
        models = self.session.execute(stmt).scalars().all()
        return [self._to_entity(m) for m in models]

    def save_line(self, line: HistoricalStatementLine) -> HistoricalStatementLine:
        model = self.session.get(HistoricalStatementLineModel, line.id)
        now = datetime.now(timezone.utc)
        if model is None:
            model = HistoricalStatementLineModel(
                id=line.id,
                project_id=line.project_id,
                period_id=line.period_id,
                statement_type=line.statement_type,
                line_code=line.line_code,
                line_label=line.line_label,
                amount_paise=line.amount_paise,
                source_id=line.source_id,
                is_imported=line.is_imported,
                mapping_status=line.mapping_status,
                notes=line.notes,
                created_at=now,
                updated_at=now,
                is_active=True,
            )
            self.session.add(model)
        else:
            model.line_label = line.line_label
            model.amount_paise = line.amount_paise
            model.source_id = line.source_id
            model.is_imported = line.is_imported
            model.mapping_status = line.mapping_status
            model.notes = line.notes
            model.updated_at = now

        self.session.flush()
        return self._to_entity(model)
