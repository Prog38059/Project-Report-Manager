"""SQLAlchemy models for Project Cost Heads and Items."""

from datetime import date
from typing import Optional
import uuid

from sqlalchemy import BigInteger, Boolean, Date, ForeignKey, Index, Integer, SmallInteger, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.infrastructure.database.models.base import Base, GUID, TimestampMixin


class ProjectCostHeadModel(Base):
    __tablename__ = "project_cost_heads"

    id: Mapped[uuid.UUID] = mapped_column(GUID(), primary_key=True, default=uuid.uuid4)
    head_code: Mapped[str] = mapped_column(String(40), unique=True, nullable=False)
    head_name: Mapped[str] = mapped_column(String(150), nullable=False)
    category_code: Mapped[str] = mapped_column(String(30), nullable=False)
    capitalisation_default: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    sort_order: Mapped[int] = mapped_column(SmallInteger, default=0, nullable=False)
    active_flag: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    # Relationships
    items = relationship("ProjectCostItemModel", back_populates="cost_head")


class ProjectCostItemModel(Base, TimestampMixin):
    __tablename__ = "project_cost_items"

    id: Mapped[uuid.UUID] = mapped_column(GUID(), primary_key=True, default=uuid.uuid4)
    scenario_id: Mapped[uuid.UUID] = mapped_column(
        GUID(),
        ForeignKey("project_scenarios.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    cost_head_id: Mapped[uuid.UUID] = mapped_column(
        GUID(),
        ForeignKey("project_cost_heads.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    description: Mapped[str] = mapped_column(String(250), nullable=False)
    quantity_decimal_text: Mapped[Optional[str]] = mapped_column(String(80), nullable=True)
    unit_code: Mapped[Optional[str]] = mapped_column(String(30), nullable=True)
    rate_decimal_text: Mapped[Optional[str]] = mapped_column(String(80), nullable=True)
    basic_amount_paise: Mapped[int] = mapped_column(BigInteger, nullable=False)
    gst_rate_pct_text: Mapped[Optional[str]] = mapped_column(String(40), nullable=True)
    gst_amount_paise: Mapped[int] = mapped_column(BigInteger, default=0, nullable=False)
    eligible_itc_paise: Mapped[int] = mapped_column(BigInteger, default=0, nullable=False)
    non_creditable_tax_paise: Mapped[int] = mapped_column(BigInteger, default=0, nullable=False)
    capitalised_amount_paise: Mapped[int] = mapped_column(BigInteger, default=0, nullable=False)
    project_cash_requirement_paise: Mapped[int] = mapped_column(BigInteger, default=0, nullable=False)
    payment_due_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    supplier_name: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    source_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        GUID(),
        ForeignKey("project_sources.id", ondelete="SET NULL"),
        nullable=True,
    )
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Relationships
    cost_head = relationship("ProjectCostHeadModel", back_populates="items")
    scenario = relationship("ProjectScenarioModel", back_populates="cost_items")

    __table_args__ = (
        Index("ix_project_cost_items_scenario", "scenario_id"),
        Index("ix_project_cost_items_head", "cost_head_id"),
    )
