# Phase 4 Context — Appraisal Metrics & Validation Engine

## Objectives Achieved
1. **Lender Appraisal Metrics & Financial Ratios**:
   - `app/domain/financial/appraisal.py`:
     - Liquidity Ratios: Current Ratio, Quick (Acid Test) Ratio.
     - Solvency & Leverage Ratios: Debt-Equity Ratio, Term Debt-Equity Ratio, Interest Coverage Ratio (EBITDA / Finance Costs).
     - Lender DSCR Coverage:
       - Gross Cash Flow DSCR: `(PAT + Depreciation + Term Loan Interest) / (Principal Repaid + Term Loan Interest)`.
       - Net Operating CFADS DSCR: `Cash Flow Available for Debt Service (CFADS) / Scheduled Debt Service`.
       - Period-wise, Arithmetic Average, and Cumulative DSCR over the repayment lifecycle.
     - Profitability Margins: Gross Profit Margin %, EBITDA Margin %, EBIT Margin %, Net Profit (PAT) Margin %, Return on Capital Employed (ROCE) %, Return on Net Worth (RONW) %.
     - Break-Even Analysis:
       - Cost Segregation: Fixed Costs (Employee, Admin, Depreciation, Finance Costs) vs Variable Costs (Raw Materials, Other Direct, Selling Expenses).
       - Contribution Margin %: `(Net Revenue - Variable Costs) / Net Revenue`.
       - Break-Even Sales: `Fixed Costs / Contribution Margin`.
       - Break-Even Capacity Utilization %: `(Break-Even Sales / Net Revenue) * 100`.
       - Cash Break-Even Sales: `(Fixed Costs - Depreciation) / Contribution Margin`.
       - Margin of Safety (₹ and %): `Net Revenue - Break-Even Sales`.
     - Project Lifetime Returns:
       - Free Cash Flow to Firm (FCFF) series.
       - Net Present Value (NPV) calculated in integer paise at configurable discount rates.
       - Project Internal Rate of Return (IRR) computed via 60-iteration exact Decimal bisection root-finding within 1 paise tolerance.
       - Simple Payback Period (years and fractional years).
       - Profitability Index (PI).
     - Sensitivity Analysis:
       - Simulates operational driver shocks (+/-5% and +/-10% on Selling Price and Raw Material Cost).
       - Reports impact on Average DSCR, Project IRR, Average PAT, and Year 1 Break-Even Capacity %.

2. **Cross-Statement Validation & Audit Engine**:
   - `app/domain/financial/validation.py`:
     - Rule `VAL-BS-001` (Severity ERROR, non-overridable): Detects any Balance Sheet difference (`Total Assets != Total Liabilities + Equity`).
     - Rule `VAL-CASH-001` (Severity ERROR, non-overridable): Detects negative projected closing cash balances in any period.
     - Rule `VAL-FUND-001` (Severity ERROR / WARNING, overridable): Detects shortfall or surplus between Total Project Cost items and Total Funding Sources.
     - Rule `VAL-DSCR-001` & `VAL-DSCR-002` (Severity WARNING): Flags Average Gross DSCR or Net CFADS DSCR falling below underwriting threshold (default 1.25x).
     - Rule `VAL-DSCR-003` (Severity WARNING): Flags single-year DSCR dip below minimum safe threshold (default 1.10x).
     - Rule `VAL-CR-001` & `VAL-CR-002` (Severity WARNING / INFO): Audits Current Ratio against bank minimum (1.33x) and Year 1 initial threshold (1.20x).
     - Rule `VAL-DER-001` (Severity WARNING): Flags Debt-Equity Ratio exceeding lender maximum (default 3.00x).
     - Rule `VAL-BEP-001` (Severity WARNING): Flags Year 1 Break-Even Capacity utilization exceeding safe ceiling (default 60%).

3. **Persistence & Database Models**:
   - `RatioResultModel`: Persists period-wise and project-lifetime ratios with metric code, unit code, method code, and benchmark notes.
   - `ValidationResultModel`: Persists audit findings with rule code, severity, scope, message, expected/actual values, and resolution status.
   - `CalculationRunModel`: Automatically tracks `validation_error_count`, `validation_warning_count`, and updates `run_status` (`SUCCESS`, `COMPLETED_WITH_WARNINGS`, `COMPLETED_WITH_ERRORS`).
   - Alembic Migration `0004_phase4_appraisal_and_validation.py` applied and verified.

4. **Application Services & DTOs**:
   - `app/application/dtos/appraisal_dto.py`: Type-safe DTOs for `AppraisalReportDTO`, `RatioMetricRowDTO`, `ProjectLifetimeReturnsDTO`, `SensitivityRowDTO`, and `ValidationIssueDTO`.
   - `app/application/services/appraisal_service.py`: Reconstructs statements from persisted calculation runs without mutating state, calculates appraisal metrics and audit rules, persists results, and formats presentation DTOs.

5. **Desktop GUI View**:
   - `AppraisalView` (`app/presentation/views/appraisal_view.py`):
     - 4 Top KPI Cards: Project Returns (NPV, IRR, Payback), Lender DSCR Coverage, Solvency/Liquidity, and Audit Integrity Status.
     - Tab 1: 📊 Financial Ratios & DSCR (Horizontal Year presentation with benchmark status).
     - Tab 2: 🎯 Break-Even Analysis (Fixed/Variable costs, BEP sales, capacity %, cash BEP, MOS %).
     - Tab 3: 🔀 Sensitivity Matrix (+/-5%, +/-10% price and raw material shock testing).
     - Tab 4: 🛡️ Audit & Invariant Rules (Error/Warning issues list with expected/actual and suggested corrective actions).
     - Integrated into `MainWindow` navigation rail with index 5.
