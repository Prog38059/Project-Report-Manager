"""Application service for Revenue Streams and Forecasting."""

from decimal import Decimal
from typing import List, Optional
import uuid

from app.application.dtos.revenue_dto import RevenueForecastPeriodDTO, RevenueStreamDTO
from app.common.money import paise_to_rupees, rupees_to_paise
from app.common.types import GstTreatmentCode, RevenueCalculationMode, RevenueMethodCode
from app.domain.entities.revenue import RevenueForecast, RevenueStream
from app.infrastructure.database.connection import DatabaseManager
from app.infrastructure.repositories.project_repository import ProjectRepository
from app.infrastructure.repositories.revenue_repository import RevenueRepository


class RevenueService:
    def __init__(self, db_manager: DatabaseManager) -> None:
        self.db_manager = db_manager

    def list_methods(self) -> List[dict]:
        with self.db_manager.session_scope() as session:
            repo = RevenueRepository(session)
            return repo.list_methods()

    def list_streams(self, scenario_id: uuid.UUID) -> List[RevenueStreamDTO]:
        with self.db_manager.session_scope() as session:
            repo = RevenueRepository(session)
            streams = repo.list_streams_for_scenario(scenario_id)
            return [
                RevenueStreamDTO(
                    id=s.id,
                    scenario_id=s.scenario_id,
                    stream_code=s.stream_code,
                    stream_name=s.stream_name,
                    method_code=s.method_code,
                    gst_treatment_code=s.gst_treatment_code,
                    gst_rate_pct=Decimal(s.gst_rate_pct_text) if s.gst_rate_pct_text else None,
                    unit_code=s.unit_code,
                    notes=s.notes,
                )
                for s in streams
            ]

    def save_stream(
        self,
        scenario_id: uuid.UUID,
        stream_code: str,
        stream_name: str,
        method_code: str,
        gst_treatment_code: str,
        gst_rate_pct: Optional[Decimal] = None,
        unit_code: Optional[str] = None,
        notes: Optional[str] = None,
        stream_id: Optional[uuid.UUID] = None,
    ) -> RevenueStreamDTO:
        with self.db_manager.session_scope() as session:
            repo = RevenueRepository(session)
            entity = RevenueStream(
                id=stream_id or uuid.uuid4(),
                scenario_id=scenario_id,
                stream_code=stream_code.strip(),
                stream_name=stream_name.strip(),
                method_code=RevenueMethodCode(method_code),
                gst_treatment_code=GstTreatmentCode(gst_treatment_code),
                gst_rate_pct_text=str(gst_rate_pct) if gst_rate_pct is not None else None,
                unit_code=unit_code,
                notes=notes,
            )
            saved = repo.save_stream(entity)
            return RevenueStreamDTO(
                id=saved.id,
                scenario_id=saved.scenario_id,
                stream_code=saved.stream_code,
                stream_name=saved.stream_name,
                method_code=saved.method_code,
                gst_treatment_code=saved.gst_treatment_code,
                gst_rate_pct=Decimal(saved.gst_rate_pct_text) if saved.gst_rate_pct_text else None,
                unit_code=saved.unit_code,
                notes=saved.notes,
            )

    def delete_stream(self, stream_id: uuid.UUID) -> None:
        with self.db_manager.session_scope() as session:
            repo = RevenueRepository(session)
            repo.delete_stream(stream_id)

    def list_forecasts_for_stream(self, stream_id: uuid.UUID, project_id: uuid.UUID) -> List[RevenueForecastPeriodDTO]:
        with self.db_manager.session_scope() as session:
            rev_repo = RevenueRepository(session)
            proj_repo = ProjectRepository(session)

            stream = rev_repo.get_stream(stream_id)
            if not stream:
                return []

            periods = proj_repo.list_periods_for_project(project_id)
            forecasts = {f.period_id: f for f in rev_repo.list_forecasts_for_stream(stream_id)}

            results = []
            for p in sorted(periods, key=lambda x: x.display_sequence):
                f = forecasts.get(p.id)
                # Compute projection numbers
                calc_mode = RevenueCalculationMode(f.calculation_mode) if f else RevenueCalculationMode.DRIVER
                cap = Decimal(f.capacity_decimal_text) if f and f.capacity_decimal_text else None
                util = Decimal(f.utilisation_pct_text) if f and f.utilisation_pct_text else None
                units = Decimal(f.units_decimal_text) if f and f.units_decimal_text else None
                price = Decimal(f.price_per_unit_decimal_text) if f and f.price_per_unit_decimal_text else None
                days = Decimal(f.operating_days_decimal_text) if f and f.operating_days_decimal_text else None
                growth = Decimal(f.growth_pct_text) if f and f.growth_pct_text else None
                override = f.gross_billing_override_paise if f else None

                res = RevenueForecast.calculate_stream_period(
                    method_code=RevenueMethodCode(stream.method_code),
                    gst_treatment=GstTreatmentCode(stream.gst_treatment_code),
                    gst_rate_pct=Decimal(stream.gst_rate_pct_text) if stream.gst_rate_pct_text else None,
                    calculation_mode=calc_mode,
                    capacity=cap,
                    utilisation_pct=util,
                    units=units,
                    price_per_unit=price,
                    operating_days=days,
                    growth_pct=growth,
                    manual_override_paise=override,
                )

                results.append(
                    RevenueForecastPeriodDTO(
                        id=f.id if f else uuid.uuid4(),
                        revenue_stream_id=stream_id,
                        period_id=p.id,
                        period_label=p.period_label,
                        period_sequence=p.period_sequence,
                        calculation_mode=calc_mode.value,
                        capacity_text=f.capacity_decimal_text if f else None,
                        utilisation_pct_text=f.utilisation_pct_text if f else None,
                        units_text=f.units_decimal_text if f else None,
                        price_per_unit_text=f.price_per_unit_decimal_text if f else None,
                        operating_days_text=f.operating_days_decimal_text if f else None,
                        growth_pct_text=f.growth_pct_text if f else None,
                        gross_billing_rupees=paise_to_rupees(res["gross_billing_paise"]),
                        output_tax_rupees=paise_to_rupees(res["output_tax_paise"]),
                        net_revenue_rupees=paise_to_rupees(res["net_revenue_paise"]),
                    )
                )

            return results

    def save_forecast(
        self,
        revenue_stream_id: uuid.UUID,
        period_id: uuid.UUID,
        calculation_mode: str = RevenueCalculationMode.DRIVER.value,
        capacity_text: Optional[str] = None,
        utilisation_pct_text: Optional[str] = None,
        units_text: Optional[str] = None,
        price_per_unit_text: Optional[str] = None,
        operating_days_text: Optional[str] = None,
        growth_pct_text: Optional[str] = None,
        gross_billing_override_rupees: Optional[Decimal] = None,
        notes: Optional[str] = None,
        forecast_id: Optional[uuid.UUID] = None,
    ) -> None:
        with self.db_manager.session_scope() as session:
            repo = RevenueRepository(session)
            entity = RevenueForecast(
                id=forecast_id or uuid.uuid4(),
                revenue_stream_id=revenue_stream_id,
                period_id=period_id,
                calculation_mode=RevenueCalculationMode(calculation_mode),
                capacity_decimal_text=capacity_text,
                utilisation_pct_text=utilisation_pct_text,
                units_decimal_text=units_text,
                price_per_unit_decimal_text=price_per_unit_text,
                operating_days_decimal_text=operating_days_text,
                growth_pct_text=growth_pct_text,
                gross_billing_override_paise=rupees_to_paise(gross_billing_override_rupees) if gross_billing_override_rupees is not None else None,
                notes=notes,
            )
            repo.save_forecast(entity)
