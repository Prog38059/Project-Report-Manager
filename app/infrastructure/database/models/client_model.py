"""Client SQLAlchemy ORM model."""

import uuid
from typing import Optional, List
from sqlalchemy import String, Text, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.infrastructure.database.models.base import Base, GUID, TimestampMixin


class ClientModel(Base, TimestampMixin):
    """Client record."""
    __tablename__ = "clients"

    id: Mapped[uuid.UUID] = mapped_column(GUID, primary_key=True, default=uuid.uuid4)
    client_code: Mapped[str] = mapped_column(String(30), unique=True, nullable=False, index=True)
    display_name: Mapped[str] = mapped_column(String(200), nullable=False, index=True)
    client_category: Mapped[str] = mapped_column(String(30), nullable=False, default="PERSON")
    phone: Mapped[Optional[str]] = mapped_column(String(30), nullable=True)
    email: Mapped[Optional[str]] = mapped_column(String(254), nullable=True)
    address_text: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Relationships
    entities: Mapped[List["EntityModel"]] = relationship(
        "EntityModel",
        back_populates="client",
        cascade="all, delete-orphan",
    )

    __table_args__ = (
        Index("idx_clients_display_name", "display_name"),
    )
