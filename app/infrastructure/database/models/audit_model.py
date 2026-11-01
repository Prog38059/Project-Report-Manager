"""Audit, application settings, and backup history SQLAlchemy ORM models."""

import uuid
from datetime import datetime, timezone
from typing import Optional
from sqlalchemy import String, Text, BigInteger, DateTime, ForeignKey, Index
from sqlalchemy.orm import Mapped, mapped_column

from app.infrastructure.database.models.base import Base, GUID


class AuditEventModel(Base):
    """Audit log of material system events and changes."""
    __tablename__ = "audit_events"

    id: Mapped[uuid.UUID] = mapped_column(GUID, primary_key=True, default=uuid.uuid4)
    project_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        GUID,
        ForeignKey("projects.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    entity_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        GUID,
        ForeignKey("entities.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    event_type: Mapped[str] = mapped_column(String(40), nullable=False)
    record_type: Mapped[str] = mapped_column(String(60), nullable=False)
    record_id: Mapped[str] = mapped_column(String(36), nullable=False)
    before_json: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    after_json: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    event_timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    actor_label: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    change_reason: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    __table_args__ = (
        Index("idx_audit_events_rec", "record_type", "record_id"),
    )


class AppSettingModel(Base):
    """Application non-sensitive configuration settings."""
    __tablename__ = "app_settings"

    setting_key: Mapped[str] = mapped_column(String(100), primary_key=True)
    setting_value: Mapped[str] = mapped_column(Text, nullable=False)
    setting_group: Mapped[str] = mapped_column(String(50), default="GENERAL", nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )


class BackupHistoryModel(Base):
    """Log of manual and automated backups and their integrity status."""
    __tablename__ = "backup_history"

    id: Mapped[uuid.UUID] = mapped_column(GUID, primary_key=True, default=uuid.uuid4)
    backup_file_path: Mapped[str] = mapped_column(Text, nullable=False)
    backup_timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    file_size_bytes: Mapped[int] = mapped_column(BigInteger, nullable=False, default=0)
    sha256_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="SUCCESS")
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
