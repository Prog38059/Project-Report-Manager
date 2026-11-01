"""Repository for Project Cost Heads and Items."""

from datetime import datetime, timezone
from typing import List, Optional
import uuid
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.domain.entities.project_cost import ProjectCostHead, ProjectCostItem
from app.infrastructure.database.models.project_cost_model import ProjectCostHeadModel, ProjectCostItemModel


class ProjectCostRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    @staticmethod
    def _head_to_entity(model: ProjectCostHeadModel) -> ProjectCostHead:
        return ProjectCostHead(
            id=model.id,
            head_code=model.head_code,
            head_name=model.head_name,
            category_code=model.category_code,
            capitalisation_default=model.capitalisation_default,
            sort_order=model.sort_order,
            active_flag=model.active_flag,
        )

    @staticmethod
    def _item_to_entity(model: ProjectCostItemModel) -> ProjectCostItem:
        return ProjectCostItem(
            id=model.id,
            scenario_id=model.scenario_id,
            cost_head_id=model.cost_head_id,
            description=model.description,
            basic_amount_paise=model.basic_amount_paise,
            gst_rate_pct_text=model.gst_rate_pct_text,
            gst_amount_paise=model.gst_amount_paise,
            eligible_itc_paise=model.eligible_itc_paise,
            non_creditable_tax_paise=model.non_creditable_tax_paise,
            capitalised_amount_paise=model.capitalised_amount_paise,
            project_cash_requirement_paise=model.project_cash_requirement_paise,
            quantity_decimal_text=model.quantity_decimal_text,
            unit_code=model.unit_code,
            rate_decimal_text=model.rate_decimal_text,
            supplier_name=model.supplier_name,
            source_id=model.source_id,
            notes=model.notes,
        )

    def list_cost_heads(self, active_only: bool = True) -> List[ProjectCostHead]:
        stmt = select(ProjectCostHeadModel)
        if active_only:
            stmt = stmt.where(ProjectCostHeadModel.active_flag.is_(True))
        stmt = stmt.order_by(ProjectCostHeadModel.sort_order)
        models = self.session.execute(stmt).scalars().all()
        return [self._head_to_entity(m) for m in models]

    def get_cost_head(self, head_id: uuid.UUID) -> Optional[ProjectCostHead]:
        model = self.session.get(ProjectCostHeadModel, head_id)
        return self._head_to_entity(model) if model else None

    def list_items_for_scenario(self, scenario_id: uuid.UUID) -> List[ProjectCostItem]:
        stmt = (
            select(ProjectCostItemModel)
            .where(ProjectCostItemModel.scenario_id == scenario_id, ProjectCostItemModel.is_active.is_(True))
            .join(ProjectCostHeadModel, ProjectCostItemModel.cost_head_id == ProjectCostHeadModel.id)
            .order_by(ProjectCostHeadModel.sort_order, ProjectCostItemModel.created_at)
        )
        models = self.session.execute(stmt).scalars().all()
        return [self._item_to_entity(m) for m in models]

    def save_item(self, item: ProjectCostItem) -> ProjectCostItem:
        model = self.session.get(ProjectCostItemModel, item.id)
        now = datetime.now(timezone.utc)
        if model is None:
            model = ProjectCostItemModel(
                id=item.id,
                scenario_id=item.scenario_id,
                cost_head_id=item.cost_head_id,
                description=item.description,
                quantity_decimal_text=item.quantity_decimal_text,
                unit_code=item.unit_code,
                rate_decimal_text=item.rate_decimal_text,
                basic_amount_paise=item.basic_amount_paise,
                gst_rate_pct_text=item.gst_rate_pct_text,
                gst_amount_paise=item.gst_amount_paise,
                eligible_itc_paise=item.eligible_itc_paise,
                non_creditable_tax_paise=item.non_creditable_tax_paise,
                capitalised_amount_paise=item.capitalised_amount_paise,
                project_cash_requirement_paise=item.project_cash_requirement_paise,
                supplier_name=item.supplier_name,
                source_id=item.source_id,
                notes=item.notes,
                created_at=now,
                updated_at=now,
                is_active=True,
            )
            self.session.add(model)
        else:
            model.cost_head_id = item.cost_head_id
            model.description = item.description
            model.quantity_decimal_text = item.quantity_decimal_text
            model.unit_code = item.unit_code
            model.rate_decimal_text = item.rate_decimal_text
            model.basic_amount_paise = item.basic_amount_paise
            model.gst_rate_pct_text = item.gst_rate_pct_text
            model.gst_amount_paise = item.gst_amount_paise
            model.eligible_itc_paise = item.eligible_itc_paise
            model.non_creditable_tax_paise = item.non_creditable_tax_paise
            model.capitalised_amount_paise = item.capitalised_amount_paise
            model.project_cash_requirement_paise = item.project_cash_requirement_paise
            model.supplier_name = item.supplier_name
            model.source_id = item.source_id
            model.notes = item.notes
            model.updated_at = now

        self.session.flush()
        return self._item_to_entity(model)

    def delete_item(self, item_id: uuid.UUID) -> None:
        model = self.session.get(ProjectCostItemModel, item_id)
        if model:
            self.session.delete(model)
            self.session.flush()
