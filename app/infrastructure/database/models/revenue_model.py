"""SQLAlchemy models for Revenue Methods, Streams, and Forecasts."""

from typing import Optional
import uuid

from sqlalchemy import BigInteger, Boolean, ForeignKey, Index, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.infrastructure.database.models.base import Base, GUID, TimestampMixin


class RevenueMethodModel(Base):
    __tablename__ = "revenue_methods"

    method_code: Mapped[str] = mapped_column(String(40), primary_key=True)
    method_name: Mapped[str] = mapped_column(String(120), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    active_flag: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)


class RevenueStreamModel(Base, TimestampMixin):
    __tablename__ = "revenue_streams"

    id: Mapped[uuid.UUID] = mapped_column(GUID(), primary_key=True, default=uuid.uuid4)
    scenario_id: Mapped[uuid.UUID] = mapped_column(
        GUID(),
        ForeignKey("project_scenarios.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    stream_code: Mapped[str] = mapped_column(String(40), nullable=False)
    stream_name: Mapped[str] = mapped_column(String(150), nullable=False)
    method_code: Mapped[str] = mapped_column(
        String(40),
        ForeignKey("revenue_methods.method_code", ondelete="RESTRICT"),
        nullable=False,
    )
    unit_code: Mapped[Optional[str]] = mapped_column(String(30), nullable=True)
    gst_treatment_code: Mapped[str] = mapped_column(String(30), nullable=False)
    gst_rate_pct_text: Mapped[Optional[str]] = mapped_column(String(40), nullable=True)
    active_flag: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Relationships
    scenario = relationship("ProjectScenarioModel", back_populates="revenue_streams")
    forecasts = relationship("RevenueForecastModel", back_populates="revenue_stream", cascade="all, delete-orphan")

    __table_args__ = (
        UniqueConstraint("scenario_id", "stream_code", name="uq_revenue_streams_code"),
        Index("ix_revenue_streams_scenario", "scenario_id"),
    )


class RevenueForecastModel(Base, TimestampMixin):
    __tablename__ = "revenue_forecasts"

    id: Mapped[uuid.UUID] = mapped_column(GUID(), primary_key=True, default=uuid.uuid4)
    revenue_stream_id: Mapped[uuid.UUID] = mapped_column(
        GUID(),
        ForeignKey("revenue_streams.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    period_id: Mapped[uuid.UUID] = mapped_column(
        GUID(),
        ForeignKey("project_periods.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    calculation_mode: Mapped[str] = mapped_column(String(20), default="DRIVER", nullable=False)
    capacity_decimal_text: Mapped[Optional[str]] = mapped_column(String(80), nullable=True)
    utilisation_pct_text: Mapped[Optional[str]] = mapped_column(String(40), nullable=True)
    units_decimal_text: Mapped[Optional[str]] = mapped_column(String(80), nullable=True)
    price_per_unit_decimal_text: Mapped[Optional[str]] = mapped_column(String(80), nullable=True)
    operating_days_decimal_text: Mapped[Optional[str]] = mapped_column(String(80), nullable=True)
    growth_pct_text: Mapped[Optional[str]] = mapped_column(String(40), nullable=True)
    gross_billing_override_paise: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    source_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        GUID(),
        ForeignKey("project_sources.id", ondelete="SET NULL"),
        nullable=True,
    )
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Relationships
    revenue_stream = relationship("RevenueStreamModel", back_populates="forecasts")
    period = relationship("ProjectPeriodModel")

    __table_args__ = (
        UniqueConstraint("revenue_stream_id", "period_id", name="uq_revenue_forecasts_stream_period"),
        Index("ix_revenue_forecasts_stream", "revenue_stream_id"),
        Index("ix_revenue_forecasts_period", "period_id"),
    )
