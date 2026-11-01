"""SQLAlchemy models for Financial Calculation Runs, Snapshots, and Statement Results."""

from datetime import date, datetime, timezone
from typing import Optional
import uuid

from sqlalchemy import (
    BigInteger,
    Boolean,
    CHAR,
    Date,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    SmallInteger,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.infrastructure.database.models.base import Base, GUID


class StatementLineDefinitionModel(Base):
    __tablename__ = "statement_line_definitions"

    id: Mapped[uuid.UUID] = mapped_column(GUID(), primary_key=True, default=uuid.uuid4)
    line_code: Mapped[str] = mapped_column(String(60), unique=True, nullable=False)
    statement_type: Mapped[str] = mapped_column(String(20), nullable=False)  # PL, BS, CASH_FLOW
    display_name: Mapped[str] = mapped_column(String(180), nullable=False)
    parent_line_code: Mapped[Optional[str]] = mapped_column(String(60), nullable=True)
    line_kind: Mapped[str] = mapped_column(String(20), nullable=False)  # INPUT, CALCULATED, SUBTOTAL, TOTAL, MEMO
    normal_balance: Mapped[Optional[str]] = mapped_column(String(10), nullable=True)  # DEBIT, CREDIT, NEUTRAL
    sort_order: Mapped[int] = mapped_column(Integer, nullable=False)
    is_required: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    formula_code: Mapped[Optional[str]] = mapped_column(String(60), nullable=True)
    active_flag: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    mappings = relationship("EntityStatementMappingModel", back_populates="line_definition")


class EntityStatementMappingModel(Base):
    __tablename__ = "entity_statement_mappings"

    id: Mapped[uuid.UUID] = mapped_column(GUID(), primary_key=True, default=uuid.uuid4)
    constitution_code: Mapped[str] = mapped_column(String(30), nullable=False)
    reporting_basis_code: Mapped[str] = mapped_column(String(40), nullable=False)
    statement_type: Mapped[str] = mapped_column(String(20), nullable=False)
    line_code: Mapped[str] = mapped_column(
        String(60),
        ForeignKey("statement_line_definitions.line_code", ondelete="CASCADE"),
        nullable=False,
    )
    display_label: Mapped[str] = mapped_column(String(180), nullable=False)
    sort_order: Mapped[int] = mapped_column(Integer, nullable=False)
    required_flag: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    effective_from: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    effective_to: Mapped[Optional[date]] = mapped_column(Date, nullable=True)

    line_definition = relationship("StatementLineDefinitionModel", back_populates="mappings")

    __table_args__ = (
        UniqueConstraint(
            "constitution_code",
            "reporting_basis_code",
            "statement_type",
            "line_code",
            "effective_from",
            name="uq_entity_stmt_map",
        ),
        Index("idx_stmt_map_lookup", "constitution_code", "reporting_basis_code", "statement_type"),
    )


class CalculationRunModel(Base):
    __tablename__ = "calculation_runs"

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
    run_number: Mapped[int] = mapped_column(Integer, nullable=False)
    engine_version: Mapped[str] = mapped_column(String(40), nullable=False)
    input_hash: Mapped[str] = mapped_column(CHAR(64), nullable=False)
    run_timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    run_status: Mapped[str] = mapped_column(String(20), nullable=False)  # SUCCESS, FAILED, COMPLETED_WITH_WARNINGS
    prepared_by_label: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    summary_note: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    validation_error_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    validation_warning_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    # Relationships
    snapshot = relationship("CalculationRunSnapshotModel", back_populates="run", uselist=False, cascade="all, delete-orphan")
    line_results = relationship("StatementLineResultModel", back_populates="run", cascade="all, delete-orphan")
    loan_results = relationship("LoanScheduleResultModel", back_populates="run", cascade="all, delete-orphan")
    asset_results = relationship("AssetScheduleResultModel", back_populates="run", cascade="all, delete-orphan")

    __table_args__ = (
        UniqueConstraint("scenario_id", "run_number", name="uq_scenario_run_number"),
    )


class CalculationRunSnapshotModel(Base):
    __tablename__ = "calculation_run_snapshots"

    id: Mapped[uuid.UUID] = mapped_column(GUID(), primary_key=True, default=uuid.uuid4)
    calculation_run_id: Mapped[uuid.UUID] = mapped_column(
        GUID(),
        ForeignKey("calculation_runs.id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
    )
    snapshot_schema_version: Mapped[str] = mapped_column(String(30), nullable=False)
    input_snapshot_json: Mapped[str] = mapped_column(Text, nullable=False)
    input_hash: Mapped[str] = mapped_column(CHAR(64), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    run = relationship("CalculationRunModel", back_populates="snapshot")


class StatementLineResultModel(Base):
    __tablename__ = "statement_line_results"

    id: Mapped[uuid.UUID] = mapped_column(GUID(), primary_key=True, default=uuid.uuid4)
    calculation_run_id: Mapped[uuid.UUID] = mapped_column(
        GUID(),
        ForeignKey("calculation_runs.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    period_id: Mapped[uuid.UUID] = mapped_column(
        GUID(),
        ForeignKey("project_periods.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    statement_type: Mapped[str] = mapped_column(String(20), nullable=False)  # PL, BS, CASH_FLOW
    line_code: Mapped[str] = mapped_column(String(60), nullable=False)
    line_label_snapshot: Mapped[str] = mapped_column(String(180), nullable=False)
    amount_paise: Mapped[int] = mapped_column(BigInteger, nullable=False)
    formula_reference: Mapped[Optional[str]] = mapped_column(String(60), nullable=True)
    trace_json: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    run = relationship("CalculationRunModel", back_populates="line_results")

    __table_args__ = (
        UniqueConstraint("calculation_run_id", "period_id", "statement_type", "line_code", name="uq_calc_period_stmt_line"),
        Index("idx_stmt_results_lookup", "calculation_run_id", "statement_type", "period_id"),
    )


class LoanScheduleResultModel(Base):
    __tablename__ = "loan_schedule_results"

    id: Mapped[uuid.UUID] = mapped_column(GUID(), primary_key=True, default=uuid.uuid4)
    calculation_run_id: Mapped[uuid.UUID] = mapped_column(
        GUID(),
        ForeignKey("calculation_runs.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    loan_facility_id: Mapped[Optional[uuid.UUID]] = mapped_column(GUID(), nullable=True)
    installment_number: Mapped[int] = mapped_column(Integer, nullable=False)
    due_date: Mapped[date] = mapped_column(Date, nullable=False)
    opening_balance_paise: Mapped[int] = mapped_column(BigInteger, nullable=False)
    disbursement_paise: Mapped[int] = mapped_column(BigInteger, default=0, nullable=False)
    payment_paise: Mapped[int] = mapped_column(BigInteger, nullable=False)
    interest_paise: Mapped[int] = mapped_column(BigInteger, nullable=False)
    principal_paise: Mapped[int] = mapped_column(BigInteger, nullable=False)
    closing_balance_paise: Mapped[int] = mapped_column(BigInteger, nullable=False)

    run = relationship("CalculationRunModel", back_populates="loan_results")

    __table_args__ = (
        UniqueConstraint("calculation_run_id", "loan_facility_id", "installment_number", name="uq_loan_sched_inst"),
    )


class AssetScheduleResultModel(Base):
    __tablename__ = "asset_schedule_results"

    id: Mapped[uuid.UUID] = mapped_column(GUID(), primary_key=True, default=uuid.uuid4)
    calculation_run_id: Mapped[uuid.UUID] = mapped_column(
        GUID(),
        ForeignKey("calculation_runs.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    asset_item_id: Mapped[Optional[uuid.UUID]] = mapped_column(GUID(), nullable=True)
    period_id: Mapped[uuid.UUID] = mapped_column(
        GUID(),
        ForeignKey("project_periods.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    opening_gross_paise: Mapped[int] = mapped_column(BigInteger, nullable=False)
    additions_paise: Mapped[int] = mapped_column(BigInteger, nullable=False)
    disposals_paise: Mapped[int] = mapped_column(BigInteger, default=0, nullable=False)
    closing_gross_paise: Mapped[int] = mapped_column(BigInteger, nullable=False)
    depreciation_paise: Mapped[int] = mapped_column(BigInteger, nullable=False)
    accumulated_depreciation_paise: Mapped[int] = mapped_column(BigInteger, nullable=False)
    closing_nbv_paise: Mapped[int] = mapped_column(BigInteger, nullable=False)

    run = relationship("CalculationRunModel", back_populates="asset_results")

    __table_args__ = (
        UniqueConstraint("calculation_run_id", "asset_item_id", "period_id", name="uq_asset_sched_period"),
    )
