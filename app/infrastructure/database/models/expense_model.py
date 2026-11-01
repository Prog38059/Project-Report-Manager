"""SQLAlchemy models for Expense Heads and Forecasts."""

from typing import Optional
import uuid

from sqlalchemy import BigInteger, Boolean, ForeignKey, Index, SmallInteger, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.infrastructure.database.models.base import Base, GUID, TimestampMixin


class ExpenseHeadModel(Base):
    __tablename__ = "expense_heads"

    id: Mapped[uuid.UUID] = mapped_column(GUID(), primary_key=True, default=uuid.uuid4)
    expense_code: Mapped[str] = mapped_column(String(40), unique=True, nullable=False)
    expense_name: Mapped[str] = mapped_column(String(150), nullable=False)
    expense_group: Mapped[str] = mapped_column(String(30), nullable=False)
    default_cost_behaviour: Mapped[str] = mapped_column(String(20), nullable=False)
    default_projection_method: Mapped[str] = mapped_column(String(30), nullable=False)
    sort_order: Mapped[int] = mapped_column(SmallInteger, default=0, nullable=False)
    active_flag: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    # Relationships
    forecasts = relationship("ExpenseForecastModel", back_populates="expense_head")


class ExpenseForecastModel(Base, TimestampMixin):
    __tablename__ = "expense_forecasts"

    id: Mapped[uuid.UUID] = mapped_column(GUID(), primary_key=True, default=uuid.uuid4)
    scenario_id: Mapped[uuid.UUID] = mapped_column(
        GUID(),
        ForeignKey("project_scenarios.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    expense_head_id: Mapped[uuid.UUID] = mapped_column(
        GUID(),
        ForeignKey("expense_heads.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    period_id: Mapped[uuid.UUID] = mapped_column(
        GUID(),
        ForeignKey("project_periods.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    projection_method: Mapped[str] = mapped_column(String(30), nullable=False)
    base_amount_paise: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    growth_pct_text: Mapped[Optional[str]] = mapped_column(String(40), nullable=True)
    revenue_pct_text: Mapped[Optional[str]] = mapped_column(String(40), nullable=True)
    unit_cost_decimal_text: Mapped[Optional[str]] = mapped_column(String(80), nullable=True)
    quantity_driver_code: Mapped[Optional[str]] = mapped_column(String(60), nullable=True)
    manual_amount_paise: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    source_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        GUID(),
        ForeignKey("project_sources.id", ondelete="SET NULL"),
        nullable=True,
    )
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Relationships
    scenario = relationship("ProjectScenarioModel", back_populates="expense_forecasts")
    expense_head = relationship("ExpenseHeadModel", back_populates="forecasts")
    period = relationship("ProjectPeriodModel")

    __table_args__ = (
        UniqueConstraint("scenario_id", "expense_head_id", "period_id", name="uq_expense_forecasts_scenario_head_period"),
        Index("ix_expense_forecasts_scenario", "scenario_id"),
        Index("ix_expense_forecasts_head", "expense_head_id"),
        Index("ix_expense_forecasts_period", "period_id"),
    )
