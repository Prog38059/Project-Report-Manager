"""Repository for Funding Heads and Sources."""

from datetime import datetime, timezone
from typing import List, Optional
import uuid
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.domain.entities.funding import FundingHead, FundingSource
from app.infrastructure.database.models.funding_model import FundingHeadModel, FundingSourceModel


class FundingRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    @staticmethod
    def _head_to_entity(model: FundingHeadModel) -> FundingHead:
        return FundingHead(
            id=model.id,
            funding_code=model.funding_code,
            funding_name=model.funding_name,
            funding_category=model.funding_category,
            sort_order=model.sort_order,
            active_flag=model.active_flag,
        )

    @staticmethod
    def _source_to_entity(model: FundingSourceModel) -> FundingSource:
        return FundingSource(
            id=model.id,
            scenario_id=model.scenario_id,
            funding_head_id=model.funding_head_id,
            source_name=model.source_name,
            amount_paise=model.amount_paise,
            expected_date=model.expected_date,
            status_code=model.status_code,
            loan_facility_id=model.loan_facility_id,
            source_id=model.source_id,
            terms_note=model.terms_note,
            notes=model.notes,
        )

    def list_funding_heads(self, active_only: bool = True) -> List[FundingHead]:
        stmt = select(FundingHeadModel)
        if active_only:
            stmt = stmt.where(FundingHeadModel.active_flag.is_(True))
        stmt = stmt.order_by(FundingHeadModel.sort_order)
        models = self.session.execute(stmt).scalars().all()
        return [self._head_to_entity(m) for m in models]

    def list_sources_for_scenario(self, scenario_id: uuid.UUID) -> List[FundingSource]:
        stmt = (
            select(FundingSourceModel)
            .where(FundingSourceModel.scenario_id == scenario_id, FundingSourceModel.is_active.is_(True))
            .join(FundingHeadModel, FundingSourceModel.funding_head_id == FundingHeadModel.id)
            .order_by(FundingHeadModel.sort_order, FundingSourceModel.created_at)
        )
        models = self.session.execute(stmt).scalars().all()
        return [self._source_to_entity(m) for m in models]

    def save_source(self, source: FundingSource) -> FundingSource:
        model = self.session.get(FundingSourceModel, source.id)
        now = datetime.now(timezone.utc)
        if model is None:
            model = FundingSourceModel(
                id=source.id,
                scenario_id=source.scenario_id,
                funding_head_id=source.funding_head_id,
                source_name=source.source_name,
                amount_paise=source.amount_paise,
                expected_date=source.expected_date,
                status_code=source.status_code,
                loan_facility_id=source.loan_facility_id,
                source_id=source.source_id,
                terms_note=source.terms_note,
                notes=source.notes,
                created_at=now,
                updated_at=now,
                is_active=True,
            )
            self.session.add(model)
        else:
            model.funding_head_id = source.funding_head_id
            model.source_name = source.source_name
            model.amount_paise = source.amount_paise
            model.expected_date = source.expected_date
            model.status_code = source.status_code
            model.loan_facility_id = source.loan_facility_id
            model.source_id = source.source_id
            model.terms_note = source.terms_note
            model.notes = source.notes
            model.updated_at = now

        self.session.flush()
        return self._source_to_entity(model)

    def delete_source(self, source_id: uuid.UUID) -> None:
        model = self.session.get(FundingSourceModel, source_id)
        if model:
            self.session.delete(model)
            self.session.flush()
