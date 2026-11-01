"""Attachment and Source SQLAlchemy ORM models."""

import uuid
from datetime import datetime, timezone
from typing import Optional
from sqlalchemy import String, Text, BigInteger, DateTime, ForeignKey, Index, CheckConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.infrastructure.database.models.base import Base, GUID, TimestampMixin


class AttachmentModel(Base):
    """Document attachment record. Resolves Gap B-1."""
    __tablename__ = "attachments"

    id: Mapped[uuid.UUID] = mapped_column(GUID, primary_key=True, default=uuid.uuid4)
    project_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        GUID,
        ForeignKey("projects.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )
    entity_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        GUID,
        ForeignKey("entities.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )
    source_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        GUID,
        ForeignKey("project_sources.id", ondelete="SET NULL"),
        nullable=True,
    )
    file_category: Mapped[str] = mapped_column(String(35), nullable=False, default="GENERAL")
    original_filename: Mapped[str] = mapped_column(String(255), nullable=False)
    stored_relative_path: Mapped[str] = mapped_column(Text, nullable=False)
    mime_type: Mapped[Optional[str]] = mapped_column(String(120), nullable=True)
    file_size_bytes: Mapped[int] = mapped_column(BigInteger, nullable=False, default=0)
    sha256_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    uploaded_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    __table_args__ = (
        CheckConstraint(
            "project_id IS NOT NULL OR entity_id IS NOT NULL",
            name="chk_attachments_parent_present",
        ),
        Index("idx_attachments_sha256", "sha256_hash"),
    )


class ProjectSourceModel(Base, TimestampMixin):
    """Record of assumption sources, quotes, and documentation."""
    __tablename__ = "project_sources"

    id: Mapped[uuid.UUID] = mapped_column(GUID, primary_key=True, default=uuid.uuid4)
    project_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        GUID,
        ForeignKey("projects.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )
    source_type: Mapped[str] = mapped_column(String(30), nullable=False)
    source_title: Mapped[str] = mapped_column(String(250), nullable=False)
    source_party: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    source_date: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    source_reference: Mapped[Optional[str]] = mapped_column(String(120), nullable=True)
    verification_status: Mapped[str] = mapped_column(String(25), nullable=False, default="UNVERIFIED")
    review_note: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    project = relationship("ProjectModel", back_populates="sources")
