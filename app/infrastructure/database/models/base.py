"""Declarative base and portable custom column types for SQLAlchemy 2.0."""

from datetime import datetime, timezone
import uuid
from typing import Optional
from sqlalchemy import String, DateTime, Boolean, TypeDecorator, CHAR
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class GUID(TypeDecorator):
    """Platform-independent GUID type.

    Uses CHAR(36), storing as string in SQLite and native UUID when supported.
    """
    impl = CHAR(36)
    cache_ok = True

    def process_bind_param(self, value, dialect):
        if value is None:
            return None
        elif isinstance(value, uuid.UUID):
            return str(value)
        else:
            return str(uuid.UUID(str(value)))

    def process_result_value(self, value, dialect):
        if value is None:
            return None
        return uuid.UUID(str(value))


class Base(DeclarativeBase):
    """Base class for all SQLAlchemy 2.0 models."""
    pass


class TimestampMixin:
    """Standard timestamp and audit columns for mutable master/input tables."""
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    created_by_label: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    updated_by_label: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
