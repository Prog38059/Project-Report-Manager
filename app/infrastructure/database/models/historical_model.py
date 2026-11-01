"""SQLAlchemy models for Historical Financial Statement Lines."""

from typing import Optional
import uuid

from sqlalchemy import BigInteger, Boolean, ForeignKey, Index, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.infrastructure.database.models.base import Base, GUID, TimestampMixin


class HistoricalStatementLineModel(Base, TimestampMixin):
    __tablename__ = "historical_statement_lines"

    id: Mapped[uuid.UUID] = mapped_column(GUID(), primary_key=True, default=uuid.uuid4)
    project_id: Mapped[uuid.UUID] = mapped_column(
        GUID(),
        ForeignKey("projects.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    period_id: Mapped[uuid.UUID] = mapped_column(
        GUID(),
        ForeignKey("project_periods.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    statement_type: Mapped[str] = mapped_column(String(20), nullable=False)
    line_code: Mapped[str] = mapped_column(String(60), nullable=False)
    line_label: Mapped[str] = mapped_column(String(180), nullable=False)
    amount_paise: Mapped[int] = mapped_column(BigInteger, default=0, nullable=False)
    source_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        GUID(),
        ForeignKey("project_sources.id", ondelete="SET NULL"),
        nullable=True,
    )
    is_imported: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    mapping_status: Mapped[str] = mapped_column(String(20), default="UNREVIEWED", nullable=False)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Relationships
    project = relationship("ProjectModel", back_populates="historical_lines")
    period = relationship("ProjectPeriodModel")

    __table_args__ = (
        UniqueConstraint(
            "project_id",
            "period_id",
            "statement_type",
            "line_code",
            name="uq_historical_statement_lines_item",
        ),
        Index("ix_historical_statement_lines_project", "project_id"),
        Index("ix_historical_statement_lines_period", "period_id"),
    )
