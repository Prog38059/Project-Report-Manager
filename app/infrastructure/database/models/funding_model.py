"""SQLAlchemy models for Funding Heads and Sources."""

from datetime import date
from typing import Optional
import uuid

from sqlalchemy import BigInteger, Boolean, Date, ForeignKey, Index, SmallInteger, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.infrastructure.database.models.base import Base, GUID, TimestampMixin


class FundingHeadModel(Base):
    __tablename__ = "funding_heads"

    id: Mapped[uuid.UUID] = mapped_column(GUID(), primary_key=True, default=uuid.uuid4)
    funding_code: Mapped[str] = mapped_column(String(40), unique=True, nullable=False)
    funding_name: Mapped[str] = mapped_column(String(150), nullable=False)
    funding_category: Mapped[str] = mapped_column(String(30), nullable=False)
    sort_order: Mapped[int] = mapped_column(SmallInteger, default=0, nullable=False)
    active_flag: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    # Relationships
    sources = relationship("FundingSourceModel", back_populates="funding_head")


class FundingSourceModel(Base, TimestampMixin):
    __tablename__ = "funding_sources"

    id: Mapped[uuid.UUID] = mapped_column(GUID(), primary_key=True, default=uuid.uuid4)
    scenario_id: Mapped[uuid.UUID] = mapped_column(
        GUID(),
        ForeignKey("project_scenarios.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    funding_head_id: Mapped[uuid.UUID] = mapped_column(
        GUID(),
        ForeignKey("funding_heads.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    source_name: Mapped[str] = mapped_column(String(200), nullable=False)
    amount_paise: Mapped[int] = mapped_column(BigInteger, nullable=False)
    expected_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    status_code: Mapped[str] = mapped_column(String(20), default="PROPOSED", nullable=False)
    loan_facility_id: Mapped[Optional[uuid.UUID]] = mapped_column(GUID(), nullable=True)
    source_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        GUID(),
        ForeignKey("project_sources.id", ondelete="SET NULL"),
        nullable=True,
    )
    terms_note: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Relationships
    funding_head = relationship("FundingHeadModel", back_populates="sources")
    scenario = relationship("ProjectScenarioModel", back_populates="funding_sources")

    __table_args__ = (
        Index("ix_funding_sources_scenario", "scenario_id"),
        Index("ix_funding_sources_head", "funding_head_id"),
    )
