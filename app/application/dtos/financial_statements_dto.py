"""Data transfer objects for Financial Calculations and Statement Presentation."""

from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal
from typing import Dict, List, Optional
from uuid import UUID


@dataclass
class StatementLineResultDTO:
    period_id: UUID
    period_sequence: int
    statement_type: str
    line_code: str
    line_label: str
    amount_paise: int
    amount_rupees: Decimal


@dataclass
class HorizontalStatementRowDTO:
    sr_no: str
    note_ref: str
    particulars: str
    is_header: bool = False
    is_total: bool = False
    period_amounts: Dict[int, Decimal] = field(default_factory=dict)


@dataclass
class StatementsTableDTO:
    statement_type: str
    title: str
    period_headers: List[str]
    rows: List[HorizontalStatementRowDTO]


@dataclass
class LoanScheduleRowDTO:
    installment_number: int
    due_date: str
    opening_balance_rupees: Decimal
    disbursement_rupees: Decimal
    payment_rupees: Decimal
    interest_rupees: Decimal
    principal_rupees: Decimal
    closing_balance_rupees: Decimal


@dataclass
class AssetScheduleRowDTO:
    period_sequence: int
    period_label: str
    opening_gross_rupees: Decimal
    additions_rupees: Decimal
    disposals_rupees: Decimal
    closing_gross_rupees: Decimal
    depreciation_rupees: Decimal
    accumulated_depreciation_rupees: Decimal
    closing_nbv_rupees: Decimal


@dataclass
class CalculationRunDTO:
    id: UUID
    project_id: UUID
    scenario_id: UUID
    run_number: int
    engine_version: str
    input_hash: str
    run_timestamp: datetime
    run_status: str
    prepared_by_label: Optional[str] = None
    summary_note: Optional[str] = None
    validation_error_count: int = 0
    validation_warning_count: int = 0
    pl_table: Optional[StatementsTableDTO] = None
    bs_table: Optional[StatementsTableDTO] = None
    cf_table: Optional[StatementsTableDTO] = None
    loan_schedule: List[LoanScheduleRowDTO] = field(default_factory=list)
    asset_schedule: List[AssetScheduleRowDTO] = field(default_factory=list)
