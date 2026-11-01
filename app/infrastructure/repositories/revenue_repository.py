"""Repository for Revenue Methods, Streams, and Forecasts."""

from datetime import datetime, timezone
from typing import List, Optional
import uuid
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.domain.entities.revenue import RevenueForecast, RevenueStream
from app.infrastructure.database.models.revenue_model import (
    RevenueForecastModel,
    RevenueMethodModel,
    RevenueStreamModel,
)


class RevenueRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    @staticmethod
    def _stream_to_entity(model: RevenueStreamModel) -> RevenueStream:
        return RevenueStream(
            id=model.id,
            scenario_id=model.scenario_id,
            stream_code=model.stream_code,
            stream_name=model.stream_name,
            method_code=model.method_code,
            unit_code=model.unit_code,
            gst_treatment_code=model.gst_treatment_code,
            gst_rate_pct_text=model.gst_rate_pct_text,
            active_flag=model.active_flag,
            notes=model.notes,
        )

    @staticmethod
    def _forecast_to_entity(model: RevenueForecastModel) -> RevenueForecast:
        return RevenueForecast(
            id=model.id,
            revenue_stream_id=model.revenue_stream_id,
            period_id=model.period_id,
            calculation_mode=model.calculation_mode,
            capacity_decimal_text=model.capacity_decimal_text,
            utilisation_pct_text=model.utilisation_pct_text,
            units_decimal_text=model.units_decimal_text,
            price_per_unit_decimal_text=model.price_per_unit_decimal_text,
            operating_days_decimal_text=model.operating_days_decimal_text,
            growth_pct_text=model.growth_pct_text,
            gross_billing_override_paise=model.gross_billing_override_paise,
            source_id=model.source_id,
            notes=model.notes,
        )

    def list_methods(self) -> List[dict]:
        stmt = select(RevenueMethodModel).where(RevenueMethodModel.active_flag.is_(True))
        models = self.session.execute(stmt).scalars().all()
        return [{"method_code": m.method_code, "method_name": m.method_name, "description": m.description} for m in models]

    def list_streams_for_scenario(self, scenario_id: uuid.UUID) -> List[RevenueStream]:
        stmt = (
            select(RevenueStreamModel)
            .where(RevenueStreamModel.scenario_id == scenario_id, RevenueStreamModel.is_active.is_(True))
            .order_by(RevenueStreamModel.stream_code)
        )
        models = self.session.execute(stmt).scalars().all()
        return [self._stream_to_entity(m) for m in models]

    def get_stream(self, stream_id: uuid.UUID) -> Optional[RevenueStream]:
        model = self.session.get(RevenueStreamModel, stream_id)
        return self._stream_to_entity(model) if model else None

    def save_stream(self, stream: RevenueStream) -> RevenueStream:
        model = self.session.get(RevenueStreamModel, stream.id)
        now = datetime.now(timezone.utc)
        if model is None:
            model = RevenueStreamModel(
                id=stream.id,
                scenario_id=stream.scenario_id,
                stream_code=stream.stream_code,
                stream_name=stream.stream_name,
                method_code=stream.method_code,
                unit_code=stream.unit_code,
                gst_treatment_code=stream.gst_treatment_code,
                gst_rate_pct_text=stream.gst_rate_pct_text,
                active_flag=stream.active_flag,
                notes=stream.notes,
                created_at=now,
                updated_at=now,
                is_active=True,
            )
            self.session.add(model)
        else:
            model.stream_code = stream.stream_code
            model.stream_name = stream.stream_name
            model.method_code = stream.method_code
            model.unit_code = stream.unit_code
            model.gst_treatment_code = stream.gst_treatment_code
            model.gst_rate_pct_text = stream.gst_rate_pct_text
            model.active_flag = stream.active_flag
            model.notes = stream.notes
            model.updated_at = now

        self.session.flush()
        return self._stream_to_entity(model)

    def delete_stream(self, stream_id: uuid.UUID) -> None:
        model = self.session.get(RevenueStreamModel, stream_id)
        if model:
            self.session.delete(model)
            self.session.flush()

    def list_forecasts_for_stream(self, stream_id: uuid.UUID) -> List[RevenueForecast]:
        stmt = (
            select(RevenueForecastModel)
            .where(RevenueForecastModel.revenue_stream_id == stream_id)
        )
        models = self.session.execute(stmt).scalars().all()
        return [self._forecast_to_entity(m) for m in models]

    def save_forecast(self, forecast: RevenueForecast) -> RevenueForecast:
        model = self.session.get(RevenueForecastModel, forecast.id)
        now = datetime.now(timezone.utc)
        if model is None:
            model = RevenueForecastModel(
                id=forecast.id,
                revenue_stream_id=forecast.revenue_stream_id,
                period_id=forecast.period_id,
                calculation_mode=forecast.calculation_mode,
                capacity_decimal_text=forecast.capacity_decimal_text,
                utilisation_pct_text=forecast.utilisation_pct_text,
                units_decimal_text=forecast.units_decimal_text,
                price_per_unit_decimal_text=forecast.price_per_unit_decimal_text,
                operating_days_decimal_text=forecast.operating_days_decimal_text,
                growth_pct_text=forecast.growth_pct_text,
                gross_billing_override_paise=forecast.gross_billing_override_paise,
                source_id=forecast.source_id,
                notes=forecast.notes,
                created_at=now,
                updated_at=now,
                is_active=True,
            )
            self.session.add(model)
        else:
            model.calculation_mode = forecast.calculation_mode
            model.capacity_decimal_text = forecast.capacity_decimal_text
            model.utilisation_pct_text = forecast.utilisation_pct_text
            model.units_decimal_text = forecast.units_decimal_text
            model.price_per_unit_decimal_text = forecast.price_per_unit_decimal_text
            model.operating_days_decimal_text = forecast.operating_days_decimal_text
            model.growth_pct_text = forecast.growth_pct_text
            model.gross_billing_override_paise = forecast.gross_billing_override_paise
            model.source_id = forecast.source_id
            model.notes = forecast.notes
            model.updated_at = now

        self.session.flush()
        return self._forecast_to_entity(model)
