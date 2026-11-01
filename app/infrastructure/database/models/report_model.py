"""Database models for Report Templates, Template Sections, and Generated Reports."""

from datetime import datetime, timezone
from typing import List, Optional
import uuid

from sqlalchemy import Boolean, CHAR, DateTime, ForeignKey, Index, Integer, SmallInteger, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.infrastructure.database.models.base import Base, GUID


class ReportTemplateModel(Base):
    __tablename__ = "report_templates"

    id: Mapped[uuid.UUID] = mapped_column(GUID(), primary_key=True, default=uuid.uuid4)
    template_code: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    template_name: Mapped[str] = mapped_column(String(160), nullable=False)
    output_type: Mapped[str] = mapped_column(String(15), nullable=False)  # MULTI, PDF, DOCX, XLSX
    constitution_code: Mapped[Optional[str]] = mapped_column(String(30), nullable=True)
    bank_name: Mapped[Optional[str]] = mapped_column(String(160), nullable=True)
    template_version: Mapped[str] = mapped_column(String(30), default="1.0", nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    active_flag: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    sections = relationship(
        "ReportTemplateSectionModel",
        back_populates="template",
        cascade="all, delete-orphan",
        order_by="ReportTemplateSectionModel.sort_order",
    )
    generated_reports = relationship("GeneratedReportModel", back_populates="template")


class ReportTemplateSectionModel(Base):
    __tablename__ = "report_template_sections"

    id: Mapped[uuid.UUID] = mapped_column(GUID(), primary_key=True, default=uuid.uuid4)
    report_template_id: Mapped[uuid.UUID] = mapped_column(
        GUID(),
        ForeignKey("report_templates.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    section_code: Mapped[str] = mapped_column(String(60), nullable=False)
    section_title: Mapped[str] = mapped_column(String(180), nullable=False)
    sort_order: Mapped[int] = mapped_column(Integer, nullable=False)
    default_included: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    required_flag: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    renderer_key: Mapped[str] = mapped_column(String(60), nullable=False)

    template = relationship("ReportTemplateModel", back_populates="sections")

    __table_args__ = (
        UniqueConstraint("report_template_id", "section_code", name="uq_template_section_code"),
    )


class GeneratedReportModel(Base):
    __tablename__ = "generated_reports"

    id: Mapped[uuid.UUID] = mapped_column(GUID(), primary_key=True, default=uuid.uuid4)
    project_id: Mapped[uuid.UUID] = mapped_column(
        GUID(),
        ForeignKey("projects.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    scenario_id: Mapped[uuid.UUID] = mapped_column(
        GUID(),
        ForeignKey("project_scenarios.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    calculation_run_id: Mapped[uuid.UUID] = mapped_column(
        GUID(),
        ForeignKey("calculation_runs.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    report_template_id: Mapped[uuid.UUID] = mapped_column(
        GUID(),
        ForeignKey("report_templates.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    report_version: Mapped[str] = mapped_column(String(30), default="1.0", nullable=False)
    output_type: Mapped[str] = mapped_column(String(15), nullable=False)  # PDF, DOCX, XLSX
    stored_relative_path: Mapped[str] = mapped_column(Text, nullable=False)
    file_hash: Mapped[str] = mapped_column(CHAR(64), nullable=False)  # SHA-256
    generated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    generation_status: Mapped[str] = mapped_column(String(20), default="SUCCESS", nullable=False)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    template = relationship("ReportTemplateModel", back_populates="generated_reports")
    run = relationship("CalculationRunModel")

    __table_args__ = (
        Index("idx_gen_reports_run", "calculation_run_id", "report_template_id"),
    )
