"""Data transfer objects for unified report generation across Excel, Word, and PDF."""

from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal
from typing import Dict, List, Optional
from uuid import UUID

from app.application.dtos.appraisal_dto import SensitivityRowDTO, ValidationIssueDTO
from app.application.dtos.financial_statements_dto import AssetScheduleRowDTO, LoanScheduleRowDTO


@dataclass
class ReportDocumentMetadataDTO:
    report_title: str
    client_name: str
    entity_legal_name: str
    constitution_label: str
    project_name: str
    project_code: str
    scenario_name: str
    calculation_run_number: int
    calculation_run_id: UUID
    engine_version: str
    input_hash: str
    generated_at: datetime
    template_name: str
    template_version: str
    prepared_by: str = "Lead Financial Analyst"
    confidentiality_notice: str = "CONFIDENTIAL & PROPRIETARY — PREPARED FOR BANK APPRAISAL ONLY"


@dataclass
class ExecutiveSummaryDTO:
    total_project_cost_rupees: Decimal
    promoter_equity_rupees: Decimal
    term_loan_rupees: Decimal
    working_capital_limit_rupees: Decimal
    first_year_net_revenue_rupees: Decimal
    terminal_year_net_revenue_rupees: Decimal
    average_gross_dscr: Optional[Decimal]
    average_net_cfads_dscr: Optional[Decimal]
    cumulative_dscr: Optional[Decimal]
    project_irr_pct: Optional[Decimal]
    npv_rupees: Decimal
    payback_years: Decimal
    first_year_bep_capacity_pct: Decimal
    validation_status: str  # PASSED, WARNINGS, ERRORS
    validation_error_count: int
    validation_warning_count: int


@dataclass
class CostItemRowDTO:
    head_name: str
    description: str
    basic_rupees: Decimal
    gst_rate_pct: Decimal
    capitalised_rupees: Decimal
    cash_required_rupees: Decimal


@dataclass
class FundingSourceRowDTO:
    head_name: str
    source_name: str
    amount_rupees: Decimal
    percentage: Decimal
    terms_note: str


@dataclass
class CostAndFundingDTO:
    cost_items: List[CostItemRowDTO] = field(default_factory=list)
    funding_sources: List[FundingSourceRowDTO] = field(default_factory=list)
    total_cost_rupees: Decimal = Decimal("0.00")
    total_funding_rupees: Decimal = Decimal("0.00")
    funding_gap_rupees: Decimal = Decimal("0.00")
    debt_equity_ratio: Optional[Decimal] = None


@dataclass
class HorizontalTableRowDTO:
    sr_no: str
    note_ref: str
    particulars: str
    is_heading: bool
    is_total: bool
    amounts: Dict[int, Decimal] = field(default_factory=dict)


@dataclass
class HorizontalStatementDTO:
    statement_type: str  # PL, BS, CASH_FLOW, RATIOS, BREAK_EVEN
    title: str
    period_headers: List[str]
    rows: List[HorizontalTableRowDTO] = field(default_factory=list)


@dataclass
class AnnualLoanSummaryDTO:
    period_sequence: int
    period_label: str
    opening_balance_rupees: Decimal
    disbursement_rupees: Decimal
    principal_repaid_rupees: Decimal
    interest_paid_rupees: Decimal
    total_debt_service_rupees: Decimal
    closing_balance_rupees: Decimal


@dataclass
class ProjectReportDataDTO:
    """Master consolidated report data object consumed by PDF, Word, and Excel renderers."""
    metadata: ReportDocumentMetadataDTO
    executive_summary: ExecutiveSummaryDTO
    cost_and_funding: CostAndFundingDTO
    pl_statement: HorizontalStatementDTO
    bs_statement: HorizontalStatementDTO
    cf_statement: HorizontalStatementDTO
    ratios_statement: HorizontalStatementDTO
    break_even_statement: HorizontalStatementDTO
    sensitivity_scenarios: List[SensitivityRowDTO]
    loan_annual_summaries: List[AnnualLoanSummaryDTO]
    loan_monthly_installments: List[LoanScheduleRowDTO]
    asset_schedules: List[AssetScheduleRowDTO]
    validation_issues: List[ValidationIssueDTO]


@dataclass
class GeneratedReportResultDTO:
    report_id: UUID
    calculation_run_id: UUID
    output_type: str  # PDF, DOCX, XLSX
    file_path: str
    file_hash: str
    generated_at: datetime
    file_size_bytes: int
