"""SQLAlchemy models for Industry Templates and Template Fields."""

from typing import Optional
import uuid

from sqlalchemy import Boolean, ForeignKey, Index, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.infrastructure.database.models.base import Base, GUID


class IndustryTemplateModel(Base):
    __tablename__ = "industry_templates"

    id: Mapped[uuid.UUID] = mapped_column(GUID(), primary_key=True, default=uuid.uuid4)
    industry_code: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    industry_name: Mapped[str] = mapped_column(String(150), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    template_version: Mapped[str] = mapped_column(String(30), default="1.0", nullable=False)
    active_flag: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    # Relationships
    fields = relationship(
        "IndustryTemplateFieldModel",
        back_populates="template",
        cascade="all, delete-orphan",
        order_by="IndustryTemplateFieldModel.sort_order",
    )


class IndustryTemplateFieldModel(Base):
    __tablename__ = "industry_template_fields"

    id: Mapped[uuid.UUID] = mapped_column(GUID(), primary_key=True, default=uuid.uuid4)
    industry_template_id: Mapped[uuid.UUID] = mapped_column(
        GUID(),
        ForeignKey("industry_templates.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    module_code: Mapped[str] = mapped_column(String(40), nullable=False)
    field_code: Mapped[str] = mapped_column(String(60), nullable=False)
    field_label: Mapped[str] = mapped_column(String(150), nullable=False)
    input_type: Mapped[str] = mapped_column(String(25), nullable=False)
    unit_code: Mapped[Optional[str]] = mapped_column(String(30), nullable=True)
    required_flag: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    default_value_text: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    help_text: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    sort_order: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    # Relationships
    template = relationship("IndustryTemplateModel", back_populates="fields")

    __table_args__ = (
        Index("ix_template_fields_template", "industry_template_id"),
        Index("ix_template_fields_code", "industry_template_id", "field_code"),
    )
