"""Application service for Project Cost management."""

from decimal import Decimal
from typing import List, Optional
import uuid

from app.application.dtos.project_cost_dto import CostHeadDTO, CostItemDTO, CostSummaryDTO
from app.common.money import paise_to_rupees, rupees_to_paise
from app.domain.entities.project_cost import ProjectCostItem
from app.infrastructure.database.connection import DatabaseManager
from app.infrastructure.repositories.project_cost_repository import ProjectCostRepository


class ProjectCostService:
    def __init__(self, db_manager: DatabaseManager) -> None:
        self.db_manager = db_manager

    def list_cost_heads(self) -> List[CostHeadDTO]:
        with self.db_manager.session_scope() as session:
            repo = ProjectCostRepository(session)
            heads = repo.list_cost_heads(active_only=True)
            return [
                CostHeadDTO(
                    id=h.id,
                    head_code=h.head_code,
                    head_name=h.head_name,
                    category_code=h.category_code,
                    capitalisation_default=h.capitalisation_default,
                    sort_order=h.sort_order,
                )
                for h in heads
            ]

    def list_items(self, scenario_id: uuid.UUID) -> List[CostItemDTO]:
        with self.db_manager.session_scope() as session:
            repo = ProjectCostRepository(session)
            heads = {h.id: h for h in repo.list_cost_heads(active_only=False)}
            items = repo.list_items_for_scenario(scenario_id)
            return [
                CostItemDTO(
                    id=i.id,
                    scenario_id=i.scenario_id,
                    cost_head_id=i.cost_head_id,
                    cost_head_name=heads[i.cost_head_id].head_name if i.cost_head_id in heads else "Unknown",
                    description=i.description,
                    basic_amount_rupees=paise_to_rupees(i.basic_amount_paise),
                    gst_rate_pct=Decimal(i.gst_rate_pct_text) if i.gst_rate_pct_text else None,
                    gst_amount_rupees=paise_to_rupees(i.gst_amount_paise),
                    eligible_itc_rupees=paise_to_rupees(i.eligible_itc_paise),
                    non_creditable_tax_rupees=paise_to_rupees(i.non_creditable_tax_paise),
                    capitalised_amount_rupees=paise_to_rupees(i.capitalised_amount_paise),
                    project_cash_requirement_rupees=paise_to_rupees(i.project_cash_requirement_paise),
                    quantity_text=i.quantity_decimal_text,
                    unit_code=i.unit_code,
                    rate_text=i.rate_decimal_text,
                    supplier_name=i.supplier_name,
                    notes=i.notes,
                )
                for i in items
            ]

    def get_cost_summary(self, scenario_id: uuid.UUID) -> CostSummaryDTO:
        items = self.list_items(scenario_id)
        return CostSummaryDTO(
            total_basic_rupees=sum((i.basic_amount_rupees for i in items), Decimal("0")),
            total_gst_rupees=sum((i.gst_amount_rupees for i in items), Decimal("0")),
            total_eligible_itc_rupees=sum((i.eligible_itc_rupees for i in items), Decimal("0")),
            total_non_creditable_tax_rupees=sum((i.non_creditable_tax_rupees for i in items), Decimal("0")),
            total_capitalised_rupees=sum((i.capitalised_amount_rupees for i in items), Decimal("0")),
            total_cash_requirement_rupees=sum((i.project_cash_requirement_rupees for i in items), Decimal("0")),
        )

    def save_item(
        self,
        scenario_id: uuid.UUID,
        cost_head_id: uuid.UUID,
        description: str,
        basic_rupees: Decimal,
        gst_rate_pct: Optional[Decimal] = None,
        itc_eligibility_pct: Optional[Decimal] = None,
        quantity_text: Optional[str] = None,
        unit_code: Optional[str] = None,
        rate_text: Optional[str] = None,
        supplier_name: Optional[str] = None,
        notes: Optional[str] = None,
        item_id: Optional[uuid.UUID] = None,
    ) -> CostItemDTO:
        with self.db_manager.session_scope() as session:
            repo = ProjectCostRepository(session)
            head = repo.get_cost_head(cost_head_id)
            is_cap = head.capitalisation_default if head else True

            amounts = ProjectCostItem.calculate_item_amounts(
                basic_rupees=basic_rupees,
                gst_rate_pct=gst_rate_pct,
                itc_eligibility_pct=itc_eligibility_pct,
                is_capitalisable=is_cap,
            )

            item = ProjectCostItem(
                id=item_id or uuid.uuid4(),
                scenario_id=scenario_id,
                cost_head_id=cost_head_id,
                description=description.strip(),
                basic_amount_paise=amounts["basic_amount_paise"],
                gst_rate_pct_text=str(gst_rate_pct) if gst_rate_pct is not None else None,
                gst_amount_paise=amounts["gst_amount_paise"],
                eligible_itc_paise=amounts["eligible_itc_paise"],
                non_creditable_tax_paise=amounts["non_creditable_tax_paise"],
                capitalised_amount_paise=amounts["capitalised_amount_paise"],
                project_cash_requirement_paise=amounts["project_cash_requirement_paise"],
                quantity_decimal_text=quantity_text,
                unit_code=unit_code,
                rate_decimal_text=rate_text,
                supplier_name=supplier_name,
                notes=notes,
            )
            saved = repo.save_item(item)
            head_name = head.head_name if head else "Cost Head"
            return CostItemDTO(
                id=saved.id,
                scenario_id=saved.scenario_id,
                cost_head_id=saved.cost_head_id,
                cost_head_name=head_name,
                description=saved.description,
                basic_amount_rupees=paise_to_rupees(saved.basic_amount_paise),
                gst_rate_pct=Decimal(saved.gst_rate_pct_text) if saved.gst_rate_pct_text else None,
                gst_amount_rupees=paise_to_rupees(saved.gst_amount_paise),
                eligible_itc_rupees=paise_to_rupees(saved.eligible_itc_paise),
                non_creditable_tax_rupees=paise_to_rupees(saved.non_creditable_tax_paise),
                capitalised_amount_rupees=paise_to_rupees(saved.capitalised_amount_paise),
                project_cash_requirement_rupees=paise_to_rupees(saved.project_cash_requirement_paise),
                quantity_text=saved.quantity_decimal_text,
                unit_code=saved.unit_code,
                rate_text=saved.rate_decimal_text,
                supplier_name=saved.supplier_name,
                notes=saved.notes,
            )

    def delete_item(self, item_id: uuid.UUID) -> None:
        with self.db_manager.session_scope() as session:
            repo = ProjectCostRepository(session)
            repo.delete_item(item_id)
