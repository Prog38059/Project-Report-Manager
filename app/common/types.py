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


class CostCategory(str, Enum):
    """Broad category of project capital or pre-operative cost."""
    LAND = "LAND"
    BUILDING = "BUILDING"
    PLANT = "PLANT"
    OTHER_FIXED_ASSET = "OTHER_FIXED_ASSET"
    PREOPERATIVE = "PREOPERATIVE"
    DEPOSIT = "DEPOSIT"
    CONTINGENCY = "CONTINGENCY"
    WORKING_CAPITAL_MARGIN = "WORKING_CAPITAL_MARGIN"
    OTHER = "OTHER"


class FundingCategory(str, Enum):
    """Source / means of finance category."""
    PROMOTER = "PROMOTER"
    PARTNER = "PARTNER"
    SHARE_CAPITAL = "SHARE_CAPITAL"
    TERM_LOAN = "TERM_LOAN"
    UNSECURED_LOAN = "UNSECURED_LOAN"
    SUBSIDY = "SUBSIDY"
    GRANT = "GRANT"
    WORKING_CAPITAL = "WORKING_CAPITAL"
    OTHER = "OTHER"


class FundingStatus(str, Enum):
    """Commitment status of funding source."""
    PROPOSED = "PROPOSED"
    COMMITTED = "COMMITTED"
    RECEIVED = "RECEIVED"


class RevenueMethodCode(str, Enum):
    """Supported revenue forecasting models."""
    CAPACITY_UTILISATION_PRICE = "CAPACITY_UTILISATION_PRICE"
    UNITS_PRICE = "UNITS_PRICE"
    CUSTOMERS_AVERAGE_BILL = "CUSTOMERS_AVERAGE_BILL"
    OCCUPANCY_RATE = "OCCUPANCY_RATE"
    RENTAL_UNITS_RATE = "RENTAL_UNITS_RATE"
    HEADCOUNT_BILLING = "HEADCOUNT_BILLING"
    TURNOVER_GROWTH = "TURNOVER_GROWTH"
    MANUAL = "MANUAL"
    CUSTOM_REGISTERED_METHOD = "CUSTOM_REGISTERED_METHOD"


class GstTreatmentCode(str, Enum):
    """Indirect tax treatment for revenue streams."""
    EXEMPT = "EXEMPT"
    NIL_RATED = "NIL_RATED"
    ZERO_RATED = "ZERO_RATED"
    TAXABLE_EXCLUSIVE = "TAXABLE_EXCLUSIVE"
    TAXABLE_INCLUSIVE = "TAXABLE_INCLUSIVE"
    OUT_OF_SCOPE = "OUT_OF_SCOPE"
    NOT_APPLICABLE = "NOT_APPLICABLE"
    REVIEW_REQUIRED = "REVIEW_REQUIRED"


class RevenueCalculationMode(str, Enum):
    """Mode of revenue determination."""
    DRIVER = "DRIVER"
    MANUAL_OVERRIDE = "MANUAL_OVERRIDE"


class ExpenseGroup(str, Enum):
    """Operating expense classification group."""
    DIRECT = "DIRECT"
    EMPLOYEE = "EMPLOYEE"
    ADMIN = "ADMIN"
    SELLING = "SELLING"
    FINANCE = "FINANCE"
    TAX = "TAX"
    OTHER = "OTHER"


class CostBehaviour(str, Enum):
    """Cost variability behaviour."""
    FIXED = "FIXED"
    VARIABLE = "VARIABLE"
    SEMI_VARIABLE = "SEMI_VARIABLE"


class ExpenseProjectionMethod(str, Enum):
    """Projection method for operating expense."""
    FIXED_AMOUNT = "FIXED_AMOUNT"
    GROWTH = "GROWTH"
    PERCENT_REVENUE = "PERCENT_REVENUE"
    PER_UNIT = "PER_UNIT"
    CAPACITY_BASED = "CAPACITY_BASED"
    HEADCOUNT_BASED = "HEADCOUNT_BASED"
    MANUAL = "MANUAL"


class StatementType(str, Enum):
    """Financial statement classification."""
    PL = "PL"
    BS = "BS"
    CASH_FLOW = "CASH_FLOW"


class MappingStatus(str, Enum):
    """Review status for historical statement mapping."""
    UNREVIEWED = "UNREVIEWED"
    MAPPED = "MAPPED"
    EXCLUDED = "EXCLUDED"
    REVIEW_REQUIRED = "REVIEW_REQUIRED"


class SourceType(str, Enum):
    """Classification of evidentiary source document."""
    VENDOR_QUOTE = "VENDOR_QUOTE"
    BANK_TERM_SHEET = "BANK_TERM_SHEET"
    PROMOTER_ESTIMATE = "PROMOTER_ESTIMATE"
    GOVERNMENT_SOURCE = "GOVERNMENT_SOURCE"
    MARKET_STUDY = "MARKET_STUDY"
    STATUTORY_SOURCE = "STATUTORY_SOURCE"
    OTHER = "OTHER"


class VerificationStatus(str, Enum):
    """Status of source verification."""
    UNVERIFIED = "UNVERIFIED"
    VERIFIED = "VERIFIED"
    REJECTED = "REJECTED"
    EXPIRED = "EXPIRED"

