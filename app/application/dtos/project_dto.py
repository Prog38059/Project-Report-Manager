"""Project DTOs."""

from dataclasses import dataclass
from datetime import date, datetime
from typing import Optional
import uuid

from app.common.types import ProjectNatureCode, ProjectStatusCode, PeriodGranularity


@dataclass
class CreateProjectDTO:
    entity_id: uuid.UUID
    project_code: str
    project_name: str
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
    financial_year_start_month: int = 4  # Default 4 (April) per ADR-001
    projection_granularity: PeriodGranularity = PeriodGranularity.ANNUAL
    projection_year_count: int = 7  # Default 7 years per ADR-002
    projection_start_financial_year: int = 2026
    historical_data_enabled: bool = False  # Default False per ADR-003


@dataclass
class UpdateProjectDTO:
    project_name: Optional[str] = None
    industry_code: Optional[str] = None
    business_model_code: Optional[str] = None
    project_nature_code: Optional[ProjectNatureCode] = None
    location_address: Optional[str] = None
    district: Optional[str] = None
    state: Optional[str] = None
    pin_code: Optional[str] = None
    project_description: Optional[str] = None
    implementation_start: Optional[date] = None
    commercial_operation_date: Optional[date] = None
    status_code: Optional[ProjectStatusCode] = None
    historical_data_enabled: Optional[bool] = None


@dataclass
class ProjectResponseDTO:
    id: uuid.UUID
    entity_id: uuid.UUID
    project_code: str
    project_name: str
    industry_code: Optional[str]
    business_model_code: Optional[str]
    project_nature_code: ProjectNatureCode
    location_address: Optional[str]
    district: Optional[str]
    state: Optional[str]
    pin_code: Optional[str]
    project_description: Optional[str]
    implementation_start: Optional[date]
    commercial_operation_date: Optional[date]
    financial_year_start_month: int
    currency_code: str
    projection_granularity: PeriodGranularity
    projection_year_count: int
    projection_start_financial_year: int
    historical_data_enabled: bool
    historical_year_count: Optional[int]
    statement_layout_code: str
    status_code: ProjectStatusCode
    created_at: datetime
    updated_at: datetime
