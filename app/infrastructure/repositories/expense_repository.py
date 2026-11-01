"""Repository for Expense Heads and Forecasts."""

from datetime import datetime, timezone
from typing import List, Optional
import uuid
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.domain.entities.expense import ExpenseForecast, ExpenseHead
from app.infrastructure.database.models.expense_model import (
    ExpenseForecastModel,
    ExpenseHeadModel,
)


class ExpenseRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    @staticmethod
    def _head_to_entity(model: ExpenseHeadModel) -> ExpenseHead:
        return ExpenseHead(
            id=model.id,
            expense_code=model.expense_code,
            expense_name=model.expense_name,
            expense_group=model.expense_group,
            default_cost_behaviour=model.default_cost_behaviour,
            default_projection_method=model.default_projection_method,
            sort_order=model.sort_order,
            active_flag=model.active_flag,
        )

    @staticmethod
    def _forecast_to_entity(model: ExpenseForecastModel) -> ExpenseForecast:
        return ExpenseForecast(
            id=model.id,
            scenario_id=model.scenario_id,
            expense_head_id=model.expense_head_id,
            period_id=model.period_id,
            projection_method=model.projection_method,
            base_amount_paise=model.base_amount_paise,
            growth_pct_text=model.growth_pct_text,
            revenue_pct_text=model.revenue_pct_text,
            unit_cost_decimal_text=model.unit_cost_decimal_text,
            quantity_driver_code=model.quantity_driver_code,
            manual_amount_paise=model.manual_amount_paise,
            source_id=model.source_id,
            notes=model.notes,
        )

    def list_expense_heads(self, active_only: bool = True) -> List[ExpenseHead]:
        stmt = select(ExpenseHeadModel)
        if active_only:
            stmt = stmt.where(ExpenseHeadModel.active_flag.is_(True))
        stmt = stmt.order_by(ExpenseHeadModel.sort_order)
        models = self.session.execute(stmt).scalars().all()
        return [self._head_to_entity(m) for m in models]

    def list_forecasts_for_scenario(self, scenario_id: uuid.UUID) -> List[ExpenseForecast]:
        stmt = (
            select(ExpenseForecastModel)
            .where(ExpenseForecastModel.scenario_id == scenario_id)
        )
        models = self.session.execute(stmt).scalars().all()
        return [self._forecast_to_entity(m) for m in models]

    def save_forecast(self, forecast: ExpenseForecast) -> ExpenseForecast:
        model = self.session.get(ExpenseForecastModel, forecast.id)
        now = datetime.now(timezone.utc)
        if model is None:
            model = ExpenseForecastModel(
                id=forecast.id,
                scenario_id=forecast.scenario_id,
                expense_head_id=forecast.expense_head_id,
                period_id=forecast.period_id,
                projection_method=forecast.projection_method,
                base_amount_paise=forecast.base_amount_paise,
                growth_pct_text=forecast.growth_pct_text,
                revenue_pct_text=forecast.revenue_pct_text,
                unit_cost_decimal_text=forecast.unit_cost_decimal_text,
                quantity_driver_code=forecast.quantity_driver_code,
                manual_amount_paise=forecast.manual_amount_paise,
                source_id=forecast.source_id,
                notes=forecast.notes,
                created_at=now,
                updated_at=now,
                is_active=True,
            )
            self.session.add(model)
        else:
            model.projection_method = forecast.projection_method
            model.base_amount_paise = forecast.base_amount_paise
            model.growth_pct_text = forecast.growth_pct_text
            model.revenue_pct_text = forecast.revenue_pct_text
            model.unit_cost_decimal_text = forecast.unit_cost_decimal_text
            model.quantity_driver_code = forecast.quantity_driver_code
            model.manual_amount_paise = forecast.manual_amount_paise
            model.source_id = forecast.source_id
            model.notes = forecast.notes
            model.updated_at = now

        self.session.flush()
        return self._forecast_to_entity(model)
