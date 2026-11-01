"""Project, Scenario, and Period domain models."""

from dataclasses import dataclass, field
from datetime import date, datetime, timezone
from typing import Optional
import uuid

from app.common.types import (
    ProjectNatureCode,
    ProjectStatusCode,
    ScenarioTypeCode,
    PeriodRole,
    PeriodGranularity,
    PeriodType,
)


@dataclass
class Project:
    """Core project model."""
    id: uuid.UUID = field(default_factory=uuid.uuid4)
    entity_id: uuid.UUID = field(default_factory=uuid.uuid4)
    project_code: str = ""
    project_name: str = ""
    industry_code: Optional[str] = None
    business_model_code: Optional[str] = None
    project_nature_code: ProjectNatureCode = ProjectNatureCode.NEW
    location_address: Optional[str] = None
    district: Optional[str] = None
    state: Optional[str] = None
    pin_code: Optional[str] = None
    project_description: Optional[str] = None
    implementation_start: Optional[date] = None
    commercial_operation_date: Optional[date] = None
    financial_year_start_month: int = 4  # Default April per ADR-001
    currency_code: str = "INR"
    projection_granularity: PeriodGranularity = PeriodGranularity.ANNUAL
    projection_year_count: int = 7  # Default 7 years per ADR-002
    projection_start_financial_year: int = 2026
    historical_data_enabled: bool = False  # Default False per ADR-003
    historical_year_count: Optional[int] = None
    statement_layout_code: str = "HORIZONTAL_YEAR_COLUMNS"  # Default ADR-004
    status_code: ProjectStatusCode = ProjectStatusCode.DRAFT
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    created_by_label: Optional[str] = None
    updated_by_label: Optional[str] = None

    def validate(self) -> None:
        """Domain validations for Project."""
        from app.common.exceptions import ValidationError

        if not self.project_code or not self.project_code.strip():
            raise ValidationError("Project code is required.")
        if not self.project_name or not self.project_name.strip():
            raise ValidationError("Project name is required.")
        if not (1 <= self.financial_year_start_month <= 12):
            raise ValidationError("Financial year start month must be between 1 and 12.")
        if self.projection_year_count < 1 or self.projection_year_count > 30:
            raise ValidationError("Projection horizon must be between 1 and 30 years.")


@dataclass
class ProjectScenario:
    """Projection scenario model."""
    id: uuid.UUID = field(default_factory=uuid.uuid4)
    project_id: uuid.UUID = field(default_factory=uuid.uuid4)
    scenario_code: str = "BASE"
    scenario_name: str = "Base Case"
    scenario_type: ScenarioTypeCode = ScenarioTypeCode.BASE
    parent_scenario_id: Optional[uuid.UUID] = None
    probability_pct: Optional[str] = None
    is_default: bool = True
    notes: Optional[str] = None
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


@dataclass
class ProjectPeriod:
    """Reporting period model."""
    id: uuid.UUID = field(default_factory=uuid.uuid4)
    project_id: uuid.UUID = field(default_factory=uuid.uuid4)
    period_sequence: int = 1
    period_role: PeriodRole = PeriodRole.PROJECTION
    period_granularity: PeriodGranularity = PeriodGranularity.ANNUAL
    period_label: str = "Project Year 1"
    period_type: PeriodType = PeriodType.FULL_YEAR
    start_date: date = field(default_factory=date.today)
    end_date: date = field(default_factory=date.today)
    financial_year_label: Optional[str] = None
    display_sequence: int = 1
    is_report_column: bool = True
