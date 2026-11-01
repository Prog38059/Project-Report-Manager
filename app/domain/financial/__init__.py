"""Financial domain calculation and validation engines."""

from app.domain.financial.appraisal import (
    AppraisalEngine,
    PeriodRatioResult,
    ProjectAppraisalSummary,
    SensitivityScenario,
)
from app.domain.financial.depreciation import (
    AssetAdditionInput,
    AssetScheduleCalculator,
    PeriodDepreciationResult,
    calculate_slm_depreciation,
    calculate_wdv_depreciation,
)
from app.domain.financial.equity_engine import (
    EquityRollForwardCalculator,
    PeriodEquityMovement,
)
from app.domain.financial.loan_engine import (
    AnnualLoanSummary,
    LoanAmortizationCalculator,
    MonthlyLoanInstallment,
    calculate_emi_paise,
    calculate_monthly_interest_paise,
)
from app.domain.financial.statement_pipeline import (
    PeriodFinancialStatements,
    StatementPipeline,
)
from app.domain.financial.tax_engine import (
    TaxCalculationResult,
    TaxProvisionCalculator,
)
from app.domain.financial.validation import (
    FinancialValidationEngine,
    ValidationIssue,
    ValidationSeverity,
)
from app.domain.financial.working_capital import (
    WorkingCapitalAssumptions,
    WorkingCapitalCalculator,
    WorkingCapitalResult,
    calculate_net_working_capital_identity,
)

__all__ = [
    "AssetAdditionInput",
    "AssetScheduleCalculator",
    "PeriodDepreciationResult",
    "calculate_slm_depreciation",
    "calculate_wdv_depreciation",
    "LoanAmortizationCalculator",
    "MonthlyLoanInstallment",
    "AnnualLoanSummary",
    "calculate_emi_paise",
    "calculate_monthly_interest_paise",
    "WorkingCapitalAssumptions",
    "WorkingCapitalCalculator",
    "WorkingCapitalResult",
    "calculate_net_working_capital_identity",
    "TaxCalculationResult",
    "TaxProvisionCalculator",
    "EquityRollForwardCalculator",
    "PeriodEquityMovement",
    "PeriodFinancialStatements",
    "StatementPipeline",
    "AppraisalEngine",
    "PeriodRatioResult",
    "ProjectAppraisalSummary",
    "SensitivityScenario",
    "FinancialValidationEngine",
    "ValidationIssue",
    "ValidationSeverity",
]
