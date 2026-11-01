# Phase 3 Context — Financial Engine & Integrated 3-Statement Model

## Objectives Achieved
1. **Pure Domain Calculations**:
   - `app/domain/financial/depreciation.py`: Straight-line method (SLM) and written-down value (WDV) book depreciation plus Income Tax Act 1961 block depreciation with the Section 32 >180 / <180 day rule.
   - `app/domain/financial/loan_engine.py`: Monthly reducing balance EMI calculations, equal principal amortizations, construction/moratorium interest handling, and rounding clearing on the final installment.
   - `app/domain/financial/working_capital.py`: Component-wise holding days for Raw Materials, Work-in-Progress, Finished Goods, Debtors, and Creditors; Net Working Capital identity (`Current Assets - Current Liabilities`), and MPBF bank limits.
   - `app/domain/financial/tax_engine.py` & `equity_engine.py`: Entity-specific tax rates, PBT/Depreciation adjustments, and constitution-specific equity roll-forwards.
   - `app/domain/financial/statement_pipeline.py`: Comprehensive 7-year integrated financial projection compiling Profit & Loss, Indirect Cash Flow, and Balance Sheet.

2. **Strict Invariant Verification**:
   - Fundamental Balance Sheet identity: `Total Assets == Total Liabilities + Net Worth` asserted to the exact integer paise across every year.
   - Zero-plug invariant: Balancing figures, suspense accounts, or plugs are strictly forbidden and structurally unnecessary.

3. **Immutable Snapshots & Persistence**:
   - Migration `0003_phase3_financial_engine.py` adds `statement_line_definitions`, `entity_statement_mappings`, `calculation_runs`, `calculation_run_snapshots`, `statement_line_results`, `loan_schedule_results`, and `asset_schedule_results`.
   - Complete input payload serialized into canonical sorted JSON, hashed using SHA-256, and stored immutably.

4. **Desktop GUI**:
   - `StatementsView` providing horizontal year presentation (Columns A:C and Years 1:7) across Profit & Loss, Balance Sheet, Cash Flow Statement, Monthly Loan Schedule, and Asset Depreciation schedules.
