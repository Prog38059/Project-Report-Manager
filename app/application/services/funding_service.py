"""Application service for Funding and Means of Finance."""

from decimal import Decimal
from typing import List, Optional
import uuid

from app.application.dtos.funding_dto import (
    FundingHeadDTO,
    FundingReconciliationDTO,
    FundingSourceDTO,
)
from app.common.money import paise_to_rupees, rupees_to_paise
from app.common.types import FundingCategory, FundingStatus
from app.domain.entities.funding import FundingReconciliation, FundingSource
from app.infrastructure.database.connection import DatabaseManager
from app.infrastructure.repositories.funding_repository import FundingRepository


class FundingService:
    def __init__(self, db_manager: DatabaseManager) -> None:
        self.db_manager = db_manager

    def list_funding_heads(self) -> List[FundingHeadDTO]:
        with self.db_manager.session_scope() as session:
            repo = FundingRepository(session)
            heads = repo.list_funding_heads(active_only=True)
            return [
                FundingHeadDTO(
                    id=h.id,
                    funding_code=h.funding_code,
                    funding_name=h.funding_name,
                    funding_category=h.funding_category,
                    sort_order=h.sort_order,
                )
                for h in heads
            ]

    def list_sources(self, scenario_id: uuid.UUID) -> List[FundingSourceDTO]:
        with self.db_manager.session_scope() as session:
            repo = FundingRepository(session)
            heads = {h.id: h for h in repo.list_funding_heads(active_only=False)}
            sources = repo.list_sources_for_scenario(scenario_id)
            return [
                FundingSourceDTO(
                    id=s.id,
                    scenario_id=s.scenario_id,
                    funding_head_id=s.funding_head_id,
                    funding_head_name=heads[s.funding_head_id].funding_name if s.funding_head_id in heads else "Unknown",
                    source_name=s.source_name,
                    amount_rupees=paise_to_rupees(s.amount_paise),
                    status_code=s.status_code,
                    terms_note=s.terms_note,
                    notes=s.notes,
                )
                for s in sources
            ]

    def save_source(
        self,
        scenario_id: uuid.UUID,
        funding_head_id: uuid.UUID,
        source_name: str,
        amount_rupees: Decimal,
        status_code: str = FundingStatus.PROPOSED.value,
        terms_note: Optional[str] = None,
        notes: Optional[str] = None,
        source_id: Optional[uuid.UUID] = None,
    ) -> FundingSourceDTO:
        with self.db_manager.session_scope() as session:
            repo = FundingRepository(session)
            heads = {h.id: h for h in repo.list_funding_heads(active_only=False)}
            amount_paise = rupees_to_paise(amount_rupees)
            entity = FundingSource(
                id=source_id or uuid.uuid4(),
                scenario_id=scenario_id,
                funding_head_id=funding_head_id,
                source_name=source_name.strip(),
                amount_paise=amount_paise,
                status_code=FundingStatus(status_code),
                terms_note=terms_note,
                notes=notes,
            )
            saved = repo.save_source(entity)
            head_name = heads[saved.funding_head_id].funding_name if saved.funding_head_id in heads else "Funding Head"
            return FundingSourceDTO(
                id=saved.id,
                scenario_id=saved.scenario_id,
                funding_head_id=saved.funding_head_id,
                funding_head_name=head_name,
                source_name=saved.source_name,
                amount_rupees=paise_to_rupees(saved.amount_paise),
                status_code=saved.status_code.value,
                terms_note=saved.terms_note,
                notes=saved.notes,
            )

    def delete_source(self, source_id: uuid.UUID) -> None:
        with self.db_manager.session_scope() as session:
            repo = FundingRepository(session)
            repo.delete_source(source_id)

    def get_reconciliation(
        self,
        scenario_id: uuid.UUID,
        total_project_cost_rupees: Decimal,
    ) -> FundingReconciliationDTO:
        with self.db_manager.session_scope() as session:
            repo = FundingRepository(session)
            heads = {h.id: h for h in repo.list_funding_heads(active_only=False)}
            sources = repo.list_sources_for_scenario(scenario_id)

            total_cost_paise = rupees_to_paise(total_project_cost_rupees)
            total_sources_paise = sum((s.amount_paise for s in sources), 0)

            promoter_paise = 0
            term_debt_paise = 0
            other_paise = 0

            for s in sources:
                head = heads.get(s.funding_head_id)
                cat = head.funding_category if head else FundingCategory.OTHER.value
                if cat in (FundingCategory.PROMOTER.value, FundingCategory.PARTNER.value, FundingCategory.SHARE_CAPITAL.value):
                    promoter_paise += s.amount_paise
                elif cat == FundingCategory.TERM_LOAN.value:
                    term_debt_paise += s.amount_paise
                else:
                    other_paise += s.amount_paise

            recon = FundingReconciliation(
                total_project_cost_paise=total_cost_paise,
                total_funding_sources_paise=total_sources_paise,
                promoter_contribution_paise=promoter_paise,
                term_debt_paise=term_debt_paise,
                other_funding_paise=other_paise,
            )

            return FundingReconciliationDTO(
                total_project_cost_rupees=paise_to_rupees(recon.total_project_cost_paise),
                total_funding_sources_rupees=paise_to_rupees(recon.total_funding_sources_paise),
                funding_gap_rupees=paise_to_rupees(recon.funding_gap_paise),
                is_balanced=recon.is_balanced,
                promoter_contribution_rupees=paise_to_rupees(recon.promoter_contribution_paise),
                term_debt_rupees=paise_to_rupees(recon.term_debt_paise),
                debt_equity_ratio=recon.debt_equity_ratio_text,
            )
