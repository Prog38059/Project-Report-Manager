"""Enumerations and shared domain types."""

from enum import Enum


class ConstitutionCode(str, Enum):
    """Supported legal constitutions for applicant entities."""
    INDIVIDUAL = "INDIVIDUAL"
    PROPRIETORSHIP = "PROPRIETORSHIP"
    HUF = "HUF"
    PARTNERSHIP = "PARTNERSHIP"
    LLP = "LLP"
    PRIVATE_LIMITED = "PRIVATE_LIMITED"


class MemberRoleCode(str, Enum):
    """Person roles associated with an entity."""
    INDIVIDUAL_APPLICANT = "INDIVIDUAL_APPLICANT"
    PROPRIETOR = "PROPRIETOR"
    KARTA = "KARTA"
    COPARCENER = "COPARCENER"
    PARTNER = "PARTNER"
    DESIGNATED_PARTNER = "DESIGNATED_PARTNER"
    DIRECTOR = "DIRECTOR"
    SHAREHOLDER = "SHAREHOLDER"
    PROMOTER = "PROMOTER"
    AUTHORISED_SIGNATORY = "AUTHORISED_SIGNATORY"
    OTHER = "OTHER"


class IdentifierTypeCode(str, Enum):
    """Entity statutory and tax identifiers."""
    PAN = "PAN"
    GSTIN = "GSTIN"
    TAN = "TAN"
    CIN = "CIN"
    LLPIN = "LLPIN"
    UDYAM = "UDYAM"
    OTHER = "OTHER"


class ProjectNatureCode(str, Enum):
    """Nature of the investment project."""
    NEW = "NEW"
    EXPANSION = "EXPANSION"
    MODERNISATION = "MODERNISATION"
    DIVERSIFICATION = "DIVERSIFICATION"
    ACQUISITION = "ACQUISITION"
    OTHER = "OTHER"


class ProjectStatusCode(str, Enum):
    """Workflow state of a project."""
    DRAFT = "DRAFT"
    INPUT_IN_PROGRESS = "INPUT_IN_PROGRESS"
    READY_FOR_CALCULATION = "READY_FOR_CALCULATION"
    CALCULATED = "CALCULATED"
    UNDER_REVIEW = "UNDER_REVIEW"
    APPROVED_FOR_REPORT = "APPROVED_FOR_REPORT"
    REPORT_GENERATED = "REPORT_GENERATED"
    ARCHIVED = "ARCHIVED"


class ScenarioTypeCode(str, Enum):
    """Projection scenario variants."""
    BASE = "BASE"
    CONSERVATIVE = "CONSERVATIVE"
    OPTIMISTIC = "OPTIMISTIC"
    BANK_APPRAISAL = "BANK_APPRAISAL"
    CUSTOM = "CUSTOM"


class PeriodRole(str, Enum):
    """Role of a reporting period."""
    PROJECTION = "PROJECTION"
    HISTORICAL = "HISTORICAL"


class PeriodGranularity(str, Enum):
    """Granularity of a reporting period."""
    ANNUAL = "ANNUAL"
    QUARTERLY = "QUARTERLY"
    MONTHLY = "MONTHLY"


class PeriodType(str, Enum):
    """Type of reporting period."""
    FULL_YEAR = "FULL_YEAR"
    STUB_PERIOD = "STUB_PERIOD"
    MONTH = "MONTH"
    QUARTER = "QUARTER"
    OTHER = "OTHER"
