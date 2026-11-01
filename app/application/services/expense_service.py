"""Application service for Operating Expense forecasting."""

from decimal import Decimal
from typing import List, Optional
import uuid

from app.application.dtos.expense_dto import ExpenseForecastPeriodDTO, ExpenseHeadDTO
from app.common.money import paise_to_rupees, rupees_to_paise
from app.common.types import ExpenseProjectionMethod
from app.domain.entities.expense import ExpenseForecast
from app.infrastructure.database.connection import DatabaseManager
from app.infrastructure.repositories.expense_repository import ExpenseRepository
from app.infrastructure.repositories.project_repository import ProjectRepository


class ExpenseService:
    def __init__(self, db_manager: DatabaseManager) -> None:
        self.db_manager = db_manager

    def list_expense_heads(self) -> List[ExpenseHeadDTO]:
        with self.db_manager.session_scope() as session:
            repo = ExpenseRepository(session)
            heads = repo.list_expense_heads(active_only=True)
            return [
                ExpenseHeadDTO(
                    id=h.id,
                    expense_code=h.expense_code,
                    expense_name=h.expense_name,
                    expense_group=h.expense_group,
                    default_cost_behaviour=h.default_cost_behaviour,
                    default_projection_method=h.default_projection_method,
                    sort_order=h.sort_order,
                )
                for h in heads
            ]

    def list_forecasts(self, scenario_id: uuid.UUID, project_id: uuid.UUID) -> List[ExpenseForecastPeriodDTO]:
        with self.db_manager.session_scope() as session:
            exp_repo = ExpenseRepository(session)
            proj_repo = ProjectRepository(session)

            heads = {h.id: h for h in exp_repo.list_expense_heads(active_only=False)}
            periods = {p.id: p for p in proj_repo.list_periods_for_project(project_id)}
            forecasts = exp_repo.list_forecasts_for_scenario(scenario_id)

            results = []
            for f in forecasts:
                head = heads.get(f.expense_head_id)
                period = periods.get(f.period_id)
                if not head or not period:
                    continue

                # Projected amount
                amt_paise = ExpenseForecast.calculate_expense_amount(
                    projection_method=ExpenseProjectionMethod(f.projection_method),
                    base_amount_paise=f.base_amount_paise,
                    growth_pct=Decimal(f.growth_pct_text) if f.growth_pct_text else None,
                    revenue_pct=Decimal(f.revenue_pct_text) if f.revenue_pct_text else None,
                    manual_amount_paise=f.manual_amount_paise,
                )

                results.append(
                    ExpenseForecastPeriodDTO(
                        id=f.id,
                        scenario_id=f.scenario_id,
                        expense_head_id=f.expense_head_id,
                        expense_head_name=head.expense_name,
                        expense_group=head.expense_group,
                        period_id=f.period_id,
                        period_label=period.period_label,
                        period_sequence=period.period_sequence,
                        projection_method=f.projection_method,
                        projected_amount_rupees=paise_to_rupees(amt_paise),
                        growth_pct_text=f.growth_pct_text,
                        revenue_pct_text=f.revenue_pct_text,
                        unit_cost_text=f.unit_cost_decimal_text,
                        notes=f.notes,
                    )
                )

            return sorted(results, key=lambda x: (x.period_sequence, x.expense_head_name))

    def save_forecast(
        self,
        scenario_id: uuid.UUID,
        expense_head_id: uuid.UUID,
        period_id: uuid.UUID,
        projection_method: str,
        base_amount_rupees: Optional[Decimal] = None,
        growth_pct_text: Optional[str] = None,
        revenue_pct_text: Optional[str] = None,
        unit_cost_decimal_text: Optional[str] = None,
        quantity_driver_code: Optional[str] = None,
        manual_amount_rupees: Optional[Decimal] = None,
        notes: Optional[str] = None,
        forecast_id: Optional[uuid.UUID] = None,
    ) -> None:
        with self.db_manager.session_scope() as session:
            repo = ExpenseRepository(session)
            entity = ExpenseForecast(
                id=forecast_id or uuid.uuid4(),
                scenario_id=scenario_id,
                expense_head_id=expense_head_id,
                period_id=period_id,
                projection_method=ExpenseProjectionMethod(projection_method),
                base_amount_paise=rupees_to_paise(base_amount_rupees) if base_amount_rupees is not None else None,
                growth_pct_text=growth_pct_text,
                revenue_pct_text=revenue_pct_text,
                unit_cost_decimal_text=unit_cost_decimal_text,
                quantity_driver_code=quantity_driver_code,
                manual_amount_paise=rupees_to_paise(manual_amount_rupees) if manual_amount_rupees is not None else None,
                notes=notes,
            )
            repo.save_forecast(entity)
