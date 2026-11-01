"""Project, Scenario, and Period SQLAlchemy ORM models."""

import uuid
from datetime import date
from typing import Optional, List
from sqlalchemy import (
    String,
    Text,
    Date,
    Boolean,
    SmallInteger,
    ForeignKey,
    Index,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.infrastructure.database.models.base import Base, GUID, TimestampMixin


class ProjectModel(Base, TimestampMixin):
    """Core investment/projection project."""
    __tablename__ = "projects"

    id: Mapped[uuid.UUID] = mapped_column(GUID, primary_key=True, default=uuid.uuid4)
    entity_id: Mapped[uuid.UUID] = mapped_column(
        GUID,
        ForeignKey("entities.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    # Global uniqueness per Gap B-3 to avoid filesystem collisions
    project_code: Mapped[str] = mapped_column(String(30), unique=True, nullable=False, index=True)
    project_name: Mapped[str] = mapped_column(String(250), nullable=False)
    industry_code: Mapped[Optional[str]] = mapped_column(String(40), nullable=True)
    business_model_code: Mapped[Optional[str]] = mapped_column(String(40), nullable=True)
    project_nature_code: Mapped[str] = mapped_column(String(30), nullable=False, default="NEW")
    location_address: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    district: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    state: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    pin_code: Mapped[Optional[str]] = mapped_column(String(12), nullable=True)
    project_description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    implementation_start: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    commercial_operation_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)

    # Conventions per ADR-001, ADR-002, ADR-003, ADR-004
    financial_year_start_month: Mapped[int] = mapped_column(SmallInteger, default=4, nullable=False)
    currency_code: Mapped[str] = mapped_column(String(3), default="INR", nullable=False)
    projection_granularity: Mapped[str] = mapped_column(String(15), default="ANNUAL", nullable=False)
    projection_year_count: Mapped[int] = mapped_column(SmallInteger, default=7, nullable=False)
    projection_start_financial_year: Mapped[int] = mapped_column(SmallInteger, default=2026, nullable=False)
    historical_data_enabled: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    historical_year_count: Mapped[Optional[int]] = mapped_column(SmallInteger, nullable=True)
    statement_layout_code: Mapped[str] = mapped_column(
        String(40),
        default="HORIZONTAL_YEAR_COLUMNS",
        nullable=False,
    )
    status_code: Mapped[str] = mapped_column(String(30), default="DRAFT", nullable=False)

    # Relationships
    entity: Mapped["EntityModel"] = relationship("EntityModel", back_populates="projects")
    scenarios: Mapped[List["ProjectScenarioModel"]] = relationship(
        "ProjectScenarioModel",
        back_populates="project",
        cascade="all, delete-orphan",
    )
    periods: Mapped[List["ProjectPeriodModel"]] = relationship(
        "ProjectPeriodModel",
        back_populates="project",
        cascade="all, delete-orphan",
        order_by="ProjectPeriodModel.display_sequence",
    )
    sources = relationship(
        "ProjectSourceModel",
        back_populates="project",
        cascade="all, delete-orphan",
    )
    historical_lines = relationship(
        "HistoricalStatementLineModel",
        back_populates="project",
        cascade="all, delete-orphan",
    )


class ProjectScenarioModel(Base, TimestampMixin):
    """Projection scenario variant."""
    __tablename__ = "project_scenarios"

    id: Mapped[uuid.UUID] = mapped_column(GUID, primary_key=True, default=uuid.uuid4)
    project_id: Mapped[uuid.UUID] = mapped_column(
        GUID,
        ForeignKey("projects.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    scenario_code: Mapped[str] = mapped_column(String(30), nullable=False)
    scenario_name: Mapped[str] = mapped_column(String(100), nullable=False)
    scenario_type: Mapped[str] = mapped_column(String(25), nullable=False, default="BASE")
    parent_scenario_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        GUID,
        ForeignKey("project_scenarios.id", ondelete="SET NULL"),
        nullable=True,
    )
    probability_pct: Mapped[Optional[str]] = mapped_column(String(40), nullable=True)
    is_default: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    project: Mapped["ProjectModel"] = relationship("ProjectModel", back_populates="scenarios")
    cost_items = relationship(
        "ProjectCostItemModel",
        back_populates="scenario",
        cascade="all, delete-orphan",
    )
    funding_sources = relationship(
        "FundingSourceModel",
        back_populates="scenario",
        cascade="all, delete-orphan",
    )
    revenue_streams = relationship(
        "RevenueStreamModel",
        back_populates="scenario",
        cascade="all, delete-orphan",
    )
    expense_forecasts = relationship(
        "ExpenseForecastModel",
        back_populates="scenario",
        cascade="all, delete-orphan",
    )

    __table_args__ = (
        UniqueConstraint("project_id", "scenario_code", name="uq_project_scenarios_code"),
    )


class ProjectPeriodModel(Base):
    """Normalized reporting period."""
    __tablename__ = "project_periods"

    id: Mapped[uuid.UUID] = mapped_column(GUID, primary_key=True, default=uuid.uuid4)
    project_id: Mapped[uuid.UUID] = mapped_column(
        GUID,
        ForeignKey("projects.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    period_sequence: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    period_role: Mapped[str] = mapped_column(String(20), nullable=False, default="PROJECTION")
    period_granularity: Mapped[str] = mapped_column(String(15), nullable=False, default="ANNUAL")
    period_label: Mapped[str] = mapped_column(String(50), nullable=False)
    period_type: Mapped[str] = mapped_column(String(20), nullable=False, default="FULL_YEAR")
    start_date: Mapped[date] = mapped_column(Date, nullable=False)
    end_date: Mapped[date] = mapped_column(Date, nullable=False)
    financial_year_label: Mapped[Optional[str]] = mapped_column(String(30), nullable=True)
    display_sequence: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    is_report_column: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    project: Mapped["ProjectModel"] = relationship("ProjectModel", back_populates="periods")

    __table_args__ = (
        UniqueConstraint(
            "project_id",
            "period_role",
            "period_granularity",
            "period_sequence",
            name="uq_project_periods_seq",
        ),
        Index("idx_project_periods_display", "project_id", "display_sequence"),
    )
