"""Data transfer objects for Appraisal Metrics, Ratios, Break-Even, and Validation Issues."""

from dataclasses import dataclass, field
from decimal import Decimal
from typing import Dict, List, Optional
from uuid import UUID


@dataclass
class RatioMetricRowDTO:
    metric_code: str
    metric_name: str
    category: str  # LIQUIDITY, LEVERAGE, COVERAGE, PROFITABILITY, BREAK_EVEN
    unit: str  # "x", "%", "₹", "years"
    benchmark_text: str
    period_values: Dict[int, str] = field(default_factory=dict)
    status: str = "PASS"  # PASS, WARNING, FAIL


@dataclass
class ProjectLifetimeReturnsDTO:
    initial_investment_rupees: Decimal
    discount_rate_pct: Decimal
    npv_rupees: Decimal
    irr_pct: Optional[Decimal]
    payback_years: Decimal
    profitability_index: Optional[Decimal]
    average_gross_dscr: Optional[Decimal]
    average_net_cfads_dscr: Optional[Decimal]
    cumulative_dscr: Optional[Decimal]


@dataclass
class ValidationIssueDTO:
    rule_code: str
    severity: str  # ERROR, WARNING, INFO
    scope_code: str
    message: str
    period_sequence: Optional[int] = None
    expected_value: Optional[str] = None
    actual_value: Optional[str] = None
    is_overridable: bool = False
    suggested_action: Optional[str] = None


@dataclass
class SensitivityRowDTO:
    parameter_name: str
    variation_pct: Decimal
    average_dscr: str
    irr_pct: str
    avg_pat_rupees: Decimal
    first_year_bep_pct: Decimal


@dataclass
class AppraisalReportDTO:
    calculation_run_id: UUID
    run_number: int
    period_headers: List[str]
    lifetime_returns: ProjectLifetimeReturnsDTO
    ratio_rows: List[RatioMetricRowDTO]
    validation_issues: List[ValidationIssueDTO]
    sensitivity_rows: List[SensitivityRowDTO]
    error_count: int = 0
    warning_count: int = 0
