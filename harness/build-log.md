# Build Log

## Phase 1 — Foundation (Completed 2026-11-01)
- **Date:** 2026-11-01
- **Phase:** Phase 1 — Foundation
- **Summary:** Built application foundation, configuration, local SQLite persistence with SQLAlchemy 2.0 and Alembic migrations, DPAPI/Fernet field-level encryption, log redaction, managed attachment store, backup/restore engine with manifest verification, and PySide6 desktop GUI shell with Client, Entity (6 constitutions), Member, and Project CRUD workflows.
- **Files changed:**
  - `pyproject.toml`
  - `alembic.ini`
  - `harness/decision-log.md`
  - `harness/build-log.md`
  - `app/__init__.py`
  - `app/config.py`
  - `app/main.py`
  - `app/common/__init__.py`
  - `app/common/exceptions.py`
  - `app/common/types.py`
  - `app/common/money.py`
  - `app/domain/entities/__init__.py`
  - `app/domain/entities/client.py`
  - `app/domain/entities/legal_entity.py`
  - `app/domain/entities/entity_member.py`
  - `app/domain/entities/project.py`
  - `app/domain/entities/attachment.py`
  - `app/infrastructure/security/__init__.py`
  - `app/infrastructure/security/encryption.py`
  - `app/infrastructure/security/redaction.py`
  - `app/infrastructure/storage/__init__.py`
  - `app/infrastructure/storage/file_store.py`
  - `app/infrastructure/database/__init__.py`
  - `app/infrastructure/database/connection.py`
  - `app/infrastructure/database/models/__init__.py`
  - `app/infrastructure/database/models/base.py`
  - `app/infrastructure/database/models/client_model.py`
  - `app/infrastructure/database/models/entity_model.py`
  - `app/infrastructure/database/models/project_model.py`
  - `app/infrastructure/database/models/attachment_model.py`
  - `app/infrastructure/database/models/audit_model.py`
  - `app/infrastructure/repositories/__init__.py`
  - `app/infrastructure/repositories/client_repository.py`
  - `app/infrastructure/repositories/entity_repository.py`
  - `app/infrastructure/repositories/project_repository.py`
  - `app/application/__init__.py`
  - `app/application/dtos/__init__.py`
  - `app/application/dtos/client_dto.py`
  - `app/application/dtos/entity_dto.py`
  - `app/application/dtos/project_dto.py`
  - `app/application/services/__init__.py`
  - `app/application/services/client_service.py`
  - `app/application/services/entity_service.py`
  - `app/application/services/project_service.py`
  - `app/application/services/backup_service.py`
  - `app/presentation/__init__.py`
  - `app/presentation/main_window.py`
  - `app/presentation/widgets/context_bar.py`
  - `app/presentation/widgets/sensitive_field.py`
  - `app/presentation/views/dashboard_view.py`
  - `app/presentation/views/client_view.py`
  - `app/presentation/views/entity_view.py`
  - `app/presentation/views/project_view.py`
  - `app/presentation/views/project_wizard.py`
  - `app/presentation/views/backup_view.py`
  - `migrations/env.py`
  - `migrations/script.py.mako`
  - `migrations/versions/0001_phase1_foundation.py`
  - `tests/conftest.py`
  - `tests/unit/test_money.py`
  - `tests/unit/test_security.py`
  - `tests/unit/test_domain_entities.py`
  - `tests/integration/test_migration.py`
  - `tests/integration/test_attachment_storage.py`
  - `tests/integration/test_client_entity_crud.py`
  - `tests/integration/test_backup_restore.py`
  - `tests/integration/test_ui_views.py`
- **Database migrations:**
  - `0001_phase1_foundation.py` (creates `clients`, `entities`, `entity_members`, `entity_identifiers`, `huf_details`, `proprietorship_details`, `partnership_details`, `llp_details`, `company_details`, `projects`, `project_sources`, `attachments`, `project_scenarios`, `project_periods`, `audit_events`, `app_settings`, `backup_history`)
- **Tests/commands executed:**
  - `python -m pytest`
- **Test results:** 23 passed in 1.98s (100% passing, 0 warnings, 0 failures)
- **Rollback notes:** Revert git changes or drop database tables via `alembic downgrade base`.
- **Approval requested for next phase:** Phase 2 — Project inputs (costs, means of finance, revenue, expenses, and industry templates).

## Phase 2 — Project Inputs (Completed 2026-11-01)
- **Date:** 2026-11-01
- **Phase:** Phase 2 — Project Inputs
- **Summary:** Implemented Project Inputs architecture: Project Cost heads and items (with basic cost, GST %, eligible ITC, non-creditable tax, capitalised amount, cash requirement); Means of Finance (funding heads, sources, visual reconciliation gap indicator, Debt/Equity ratio); Revenue Streams & multi-year forecasting methods (Capacity x Utilisation x Price, Units x Price, Customers x Avg Bill, Occupancy, Rental, Headcount, Turnover Growth, Manual, and GST treatment); Operating Expenses forecasting (Fixed, Growth, % Revenue, Per Unit, Manual); 10 starter Industry Templates (Manufacturing, Trading, Hospital, Hotel, Restaurant, EV Charging, Transport, Education, Rental, Services); Historical Financial Statements (strictly hidden by default, enabled per project); Alembic migration `0002_phase2_inputs.py` with seed master data; and updated PySide6 Project View with interactive input tables and reconciliation badges.
- **Files changed / created:**
  - `app/common/types.py`
  - `app/domain/entities/project_cost.py`
  - `app/domain/entities/funding.py`
  - `app/domain/entities/revenue.py`
  - `app/domain/entities/expense.py`
  - `app/domain/entities/industry_template.py`
  - `app/domain/entities/historical_statement.py`
  - `app/domain/entities/__init__.py`
  - `app/infrastructure/database/models/project_cost_model.py`
  - `app/infrastructure/database/models/funding_model.py`
  - `app/infrastructure/database/models/revenue_model.py`
  - `app/infrastructure/database/models/expense_model.py`
  - `app/infrastructure/database/models/template_model.py`
  - `app/infrastructure/database/models/historical_model.py`
  - `app/infrastructure/database/models/attachment_model.py`
  - `app/infrastructure/database/models/project_model.py`
  - `app/infrastructure/database/models/__init__.py`
  - `app/infrastructure/repositories/project_cost_repository.py`
  - `app/infrastructure/repositories/funding_repository.py`
  - `app/infrastructure/repositories/revenue_repository.py`
  - `app/infrastructure/repositories/expense_repository.py`
  - `app/infrastructure/repositories/template_repository.py`
  - `app/infrastructure/repositories/historical_repository.py`
  - `app/infrastructure/repositories/project_repository.py`
  - `app/infrastructure/repositories/__init__.py`
  - `app/application/dtos/project_cost_dto.py`
  - `app/application/dtos/funding_dto.py`
  - `app/application/dtos/revenue_dto.py`
  - `app/application/dtos/expense_dto.py`
  - `app/application/dtos/template_dto.py`
  - `app/application/dtos/historical_dto.py`
  - `app/application/services/project_cost_service.py`
  - `app/application/services/funding_service.py`
  - `app/application/services/revenue_service.py`
  - `app/application/services/expense_service.py`
  - `app/application/services/template_service.py`
  - `app/application/services/historical_service.py`
  - `app/application/services/__init__.py`
  - `app/presentation/views/project_view.py`
  - `app/presentation/main_window.py`
  - `migrations/versions/0002_phase2_inputs.py`
  - `tests/unit/test_phase2_calculations.py`
  - `tests/integration/test_phase2_services.py`
  - `tests/integration/test_migration.py`
- **Database migrations:**
  - `0002_phase2_inputs.py` (creates `project_cost_heads`, `project_cost_items`, `funding_heads`, `funding_sources`, `revenue_methods`, `revenue_streams`, `revenue_forecasts`, `expense_heads`, `expense_forecasts`, `industry_templates`, `industry_template_fields`, `historical_statement_lines`, and seeds 9 revenue methods, 10 cost heads, 6 funding heads, 10 expense heads, and 10 starter industry templates).
- **Tests/commands executed:**
  - `python -m pytest -v`
- **Test results:** 36 passed in 4.72s (100% passing, 0 warnings, 0 failures).
- **Known issues:** None.
- **Rollback notes:** Revert git commits or run `alembic downgrade 0001_phase1_foundation`.
- **Approval requested for next phase:** Phase 3 — Financial Engine (fixed assets, depreciation books, loan amortization schedules, working capital cycles, tax provisions, and integrated P&L, Balance Sheet, and Cash Flow financial statements).

## Phase 3 — Financial Engine (Completed 2026-11-01)
- **Date:** 2026-11-01
- **Phase:** Phase 3 — Financial Engine
- **Summary:** Built the complete pure-domain financial calculation engine and integrated 3-statement projection pipeline:
  1. Asset & Depreciation Engine (`app/domain/financial/depreciation.py`) supporting book SLM, WDV, and Income Tax Act 1961 block depreciation (Section 32 >180 / <180 days rule).
  2. Loan Amortization Engine (`app/domain/financial/loan_engine.py`) supporting monthly EMI reducing balance, equal principal, interest during construction/moratorium, final installment rounding clearing, and annual roll-ups with next 12-month current maturities.
  3. Working Capital Engine (`app/domain/financial/working_capital.py`) implementing holding days for RM, WIP, Finished Goods, Debtors, Creditors, Net Working Capital identity (Golden Fixture D), and bank MPBF limits.
  4. Tax & Equity Engines (`app/domain/financial/tax_engine.py` and `app/domain/financial/equity_engine.py`) supporting PBT/Depreciation adjustments, entity tax rates, and constitution-specific equity/reserves roll-forwards.
  5. Integrated Three-Statement Pipeline (`app/domain/financial/statement_pipeline.py`) compiling multi-year Profit & Loss, Indirect Cash Flow, and Balance Sheet with strict Zero-Plug Invariant assertion (`total_assets == total_liabilities_and_equity` to the exact integer paise, without balancing/suspense plugs).
  6. Persistence & Immutable Snapshots: Alembic migration `0003_phase3_financial_engine.py` creating `statement_line_definitions` (with seed statement lines), `entity_statement_mappings`, `calculation_runs`, `calculation_run_snapshots` (with SHA-256 input hash), `statement_line_results`, `loan_schedule_results`, and `asset_schedule_results`.
  7. Application Services & DTOs: `FinancialEngineService` and `CalculationRepository` orchestrating full 7-year projections and returning horizontal statement tables (Columns A:C and Years 1:7).
  8. Desktop GUI: `StatementsView` with dedicated sub-tabs for Profit & Loss, Balance Sheet, Indirect Cash Flow, Loan Amortization, and Asset Depreciation, integrated into `MainWindow` navigation with live Invariant status badge.
  9. Test Suite: Verification against Golden Fixtures A, B, C, D, E, unit tests for all engines, migration upgrade/downgrade tests, and end-to-end integration tests.
- **Files changed / created:**
  - `app/domain/financial/__init__.py`
  - `app/domain/financial/depreciation.py`
  - `app/domain/financial/loan_engine.py`
  - `app/domain/financial/working_capital.py`
  - `app/domain/financial/tax_engine.py`
  - `app/domain/financial/equity_engine.py`
  - `app/domain/financial/statement_pipeline.py`
  - `app/infrastructure/database/models/calculation_model.py`
  - `app/infrastructure/database/models/__init__.py`
  - `app/infrastructure/repositories/calculation_repository.py`
  - `app/infrastructure/repositories/__init__.py`
  - `app/application/dtos/financial_statements_dto.py`
  - `app/application/services/financial_engine_service.py`
  - `app/application/services/project_service.py`
  - `app/presentation/views/statements_view.py`
  - `app/presentation/main_window.py`
  - `migrations/versions/0003_phase3_financial_engine.py`
  - `tests/unit/test_golden_fixtures.py`
  - `tests/unit/test_financial_engines.py`
  - `tests/integration/test_financial_engine_service.py`
  - `tests/integration/test_migration.py`
  - `tests/integration/test_ui_views.py`
- **Database migrations:**
  - `0003_phase3_financial_engine.py` (creates `statement_line_definitions`, `entity_statement_mappings`, `calculation_runs`, `calculation_run_snapshots`, `statement_line_results`, `loan_schedule_results`, `asset_schedule_results`, and seeds 38 standard statement lines across P&L, BS, and Cash Flow).
- **Tests/commands executed:**
  - `python -m pytest -v`
- **Test results:** 45 passed in 4.75s (100% passing, 0 warnings, 0 failures).
- **Known issues:** None.
- **Rollback notes:** Run `alembic downgrade 0002_phase2_inputs` or revert git commit.
- **Approval requested for next phase:** Phase 4 — Appraisal Metrics & Validation (DSCR formulas, break-even analysis, IRR, NPV, sensitivity analysis, cross-statement validation rules, and error/warning reporting).

## Phase 4 — Appraisal Metrics & Validation Engine (Completed 2026-11-01)
- **Date:** 2026-11-01
- **Phase:** Phase 4 — Appraisal Metrics & Validation Engine
- **Summary:** Built comprehensive lender appraisal metrics, financial ratios, break-even analysis, NPV/IRR, sensitivity analysis, and cross-statement validation rules:
  1. Lender Appraisal Domain Engine (`app/domain/financial/appraisal.py`):
     - Exact Decimal calculations for Liquidity (Current Ratio, Quick Ratio), Leverage (Debt-Equity, Term Debt-Equity, Interest Coverage Ratio), Margins (Gross Profit %, EBITDA %, EBIT %, PAT %, ROCE %, RONW %).
     - Lender DSCR Variants: Gross Cash Flow DSCR `(PAT + Dep + Term Int) / (Principal + Term Int)` and Net Operating CFADS DSCR `CFADS / Debt Service`, Average DSCR, and Cumulative DSCR.
     - Break-Even Analysis: Segregation of Fixed Costs vs Variable Costs, Contribution Margin %, Break-Even Sales paise & Capacity Utilization %, Cash Break-Even (excl. depreciation), and Margin of Safety.
     - Project Lifetime Returns: Free Cash Flow to Firm, Net Present Value (NPV) at configurable discount rates, Project IRR via 60-iteration exact Decimal bisection, Simple Payback Period, and Profitability Index.
     - Sensitivity Analysis: Simulating variations (+/-5%, +/-10%) on Selling Price and Raw Material Costs.
  2. Cross-Statement Validation Engine (`app/domain/financial/validation.py`):
     - Accounting Invariants: `VAL-BS-001` (Zero-difference Balance Sheet), `VAL-CASH-001` (Non-negative closing cash).
     - Project Funding Reconciliation: `VAL-FUND-001` (Project Cost vs Means of Finance gap).
     - Lender Underwriting Rules: `VAL-DSCR-001/002/003` (Average, minimum, and cumulative DSCR thresholds), `VAL-CR-001/002` (Current Ratio benchmarks), `VAL-DER-001` (Debt-Equity ceiling), `VAL-BEP-001` (Capacity Break-Even ceiling).
  3. Database Schema & Persistence:
     - Alembic migration `0004_phase4_appraisal_and_validation.py` creating `ratio_results` and `validation_results` tables with cascade delete on calculation runs and indexed lookups.
     - `CalculationRepository` extended with `save_ratio_results`, `save_validation_results`, queries, and `update_run_validation_counts`.
  4. Application Service & DTOs:
     - `app/application/dtos/appraisal_dto.py` defining `AppraisalReportDTO`, `RatioMetricRowDTO`, `ProjectLifetimeReturnsDTO`, `SensitivityRowDTO`, and `ValidationIssueDTO`.
     - `app/application/services/appraisal_service.py` orchestrating statement reconstruction from runs, domain evaluation, sensitivity variations, database persistence, and run status updates (`SUCCESS`, `COMPLETED_WITH_WARNINGS`, `COMPLETED_WITH_ERRORS`).
  5. Desktop GUI:
     - `AppraisalView` (`app/presentation/views/appraisal_view.py`) with 4 KPI summary cards (Project Returns, DSCR Coverage, Solvency/Liquidity, Audit Health), and 4 dedicated sub-tabs: 📊 Financial Ratios & DSCR, 🎯 Break-Even Analysis, 🔀 Sensitivity Matrix, and 🛡️ Audit & Cross-Statement Invariant Rules.
     - Integrated into `MainWindow` navigation rail with index 5.
  6. Test Suite:
     - Unit tests in `tests/unit/test_appraisal_engine.py` (ratios, bisection IRR root-finding, payback, validation rules).
     - End-to-end integration tests in `tests/integration/test_appraisal_service.py` (projection execution + appraisal evaluation + database persistence + validation count tracking).
     - UI integration tests in `tests/integration/test_ui_views.py`.
     - Migration tests in `tests/integration/test_migration.py`.
     - Total: 50 passed tests in 7.32s (100% pass rate).
- **Files changed / created:**
  - `app/domain/financial/appraisal.py`
  - `app/domain/financial/validation.py`
  - `app/domain/financial/__init__.py`
  - `app/infrastructure/database/models/calculation_model.py`
  - `app/infrastructure/database/models/__init__.py`
  - `app/infrastructure/repositories/calculation_repository.py`
  - `app/application/dtos/appraisal_dto.py`
  - `app/application/services/appraisal_service.py`
  - `app/application/services/__init__.py`
  - `app/presentation/views/appraisal_view.py`
  - `app/presentation/main_window.py`
  - `migrations/versions/0004_phase4_appraisal_and_validation.py`
  - `tests/unit/test_appraisal_engine.py`
  - `tests/integration/test_appraisal_service.py`
  - `tests/integration/test_migration.py`
  - `tests/integration/test_ui_views.py`
  - `harness/build-log.md`
- **Database migrations:**
  - `0004_phase4_appraisal_and_validation.py` (creates `ratio_results` and `validation_results`).
- **Tests/commands executed:**
  - `python -m pytest tests/ -v`
- **Test results:** 50 passed in 7.32s (100% passing, 0 warnings, 0 failures).
- **Known issues:** None.
- **Rollback notes:** Run `alembic downgrade 0003_phase3_financial_engine` or revert git commit.
- **Approval requested for next phase:** Phase 5 — Report Generation & Export (PDF, Excel, Word multi-format export, custom styling, watermark, schedule notes, and calculation run audit linkage).

## Phase 5 — Report Generation & Export Engine (Completed 2026-11-01)
- **Date:** 2026-11-01
- **Phase:** Phase 5 — Report Generation & Export Engine
- **Summary:** Built the unified multi-format reporting and export system (Excel, Word, PDF) conforming to strict architectural separation and financial reporting guidelines:
  1. Shared Report Data Object (`app/application/dtos/report_dto.py`):
     - `ProjectReportDataDTO` serves as the single source of truth consumed by all renderers.
     - Enforces non-negotiable architectural invariant: renderers consume pre-calculated figures and never recalculate numbers.
     - Contains metadata, executive summary, cost & funding tables, horizontal multi-year statements (P&L, Balance Sheet, Cash Flow), loan amortization summaries, financial ratios, sensitivity matrix, and cross-statement validation certificates.
  2. Excel Multi-Tab Workbook Renderer (`app/infrastructure/reporting/excel_renderer.py`):
     - Utilizes `openpyxl` with professional financial styling (navy blue headers `#1B365D`, alternating row shading, thin borders).
     - Renders 9 dedicated worksheets: Executive Summary, Projected P&L, Projected Balance Sheet, Projected Cash Flow, Ratios & DSCR, Break-Even & Sensitivity, Loan Amortization, Fixed Assets & Dep, and Audit & Validation.
     - Strict layout standard: Column A = Sr. No., Column B = Note, Column C = Particulars, Columns D:J = Project Years 1–7.
     - Freeze panes applied at cell `D5` so descriptive columns A–C remain permanently visible during horizontal scrolling.
     - Indian currency grouping number format `₹ #,##,##0.00` applied to all monetary cells.
  3. Word Document Renderer (`app/infrastructure/reporting/docx_renderer.py`):
     - Utilizes `python-docx` to generate formatted Bank Credit Appraisal Books & DPRs.
     - Includes styled cover page, executive summary grid, means of finance table, horizontal financial statement tables with repeating header rows (`cantSplit` and `tblHeader` XML elements), loan repayment schedule, ratio analysis, sensitivity matrix, and signed audit certificate.
  4. PDF Landscape Renderer (`app/infrastructure/reporting/pdf_renderer.py`):
     - Utilizes `reportlab` on A4 Landscape format (`pagesizes.landscape(A4)`).
     - Two-pass `NumberedCanvas` delivering running headers with document title/project name and running footers with generation date, canonical calculation run input hash, and dynamic "Page X of Y" pagination.
     - Flowables include multi-year horizontal financial statement tables, executive summary key indicator cards, DSCR appraisal breakdown, sensitivity matrix, and zero-plug invariant certificate.
  5. Report Application Service & Audit Logging (`app/application/services/report_service.py`):
     - Orchestrates retrieval of project data, statements, schedules, and appraisal reports from immutable calculation run snapshots.
     - Computes SHA-256 cryptographic file hashes on generated export files.
     - Persists generated report records into `generated_reports` database table linking `project_id`, `scenario_id`, `calculation_run_id`, `template_id`, file path, file size, SHA-256 hash, and UTC timestamp.
  6. Database Models & Alembic Migration 0005 (`migrations/versions/0005_phase5_reporting.py`):
     - Tables: `report_templates`, `report_template_sections`, `generated_reports`.
     - Seeded standard templates: `TMPL_CMA_BANK` (Standard Bank CMA & Project Appraisal Book), `TMPL_DPR_FULL` (Detailed Project Report - Full), `TMPL_EXEC_SUMMARY` (Executive Summary & Term Sheet).
  7. Desktop GUI Export View (`app/presentation/views/report_view.py`):
     - Dedicated Report & Export management screen integrated into `MainWindow` navigation rail with index 6.
     - Scenario & template selectors, one-click export buttons for Excel (`.xlsx`), Word (`.docx`), PDF (`.pdf`), and "Export All Formats (Bundle)".
     - Live KPI summary card and historical audit table of all previously generated files with double-click open support.
  8. Test Suite:
     - End-to-end integration test (`tests/integration/test_report_service.py`) verifying file creation, valid byte signatures, correct freeze panes, sheet count, table counts, and cross-renderer numerical agreement.
     - UI integration test (`tests/integration/test_ui_views.py`) verifying `ReportView` instantiation and nav rail switching.
     - Total: 51 passed tests in 11.04s (100% pass rate).
- **Files changed / created:**
  - `app/infrastructure/database/models/report_model.py`
  - `app/infrastructure/database/models/__init__.py`
  - `app/infrastructure/repositories/report_repository.py`
  - `app/infrastructure/repositories/__init__.py`
  - `app/application/dtos/report_dto.py`
  - `app/infrastructure/reporting/__init__.py`
  - `app/infrastructure/reporting/excel_renderer.py`
  - `app/infrastructure/reporting/docx_renderer.py`
  - `app/infrastructure/reporting/pdf_renderer.py`
  - `app/application/services/report_service.py`
  - `app/application/services/__init__.py`
  - `app/presentation/views/report_view.py`
  - `app/presentation/main_window.py`
  - `migrations/versions/0005_phase5_reporting.py`
  - `tests/integration/test_report_service.py`
  - `tests/integration/test_ui_views.py`
  - `harness/build-log.md`
- **Database migrations:**
  - `0005_phase5_reporting.py` (creates `report_templates`, `report_template_sections`, and `generated_reports`).
- **Tests/commands executed:**
  - `python -m pytest tests/`
- **Test results:** 51 passed in 11.04s (100% passing, 0 warnings, 0 failures).
- **Known issues:** None.
- **Rollback notes:** Run `alembic downgrade 0004_phase4_appraisal_and_validation` or revert git commit.
- **Approval requested for next phase:** Phase 6 — Hardening, Packaging, Documentation & Release.

## Phase 6 — Hardening, Packaging, Documentation & Release (Completed 2026-11-01)
- **Date:** 2026-11-01
- **Phase:** Phase 6 — Hardening, Packaging, Documentation & Release
- **Summary:** Completed application hardening, diagnostics, distribution packaging, turnkey sample generation, and release documentation:
  1. Database Migration Manager (`app/infrastructure/database/migration_manager.py`):
     - Programmatic Alembic upgrade execution to `head` on startup with fallback to schema creation.
     - Migration status inspection (current revision vs target head) and SQLite physical integrity checking (`PRAGMA integrity_check`).
  2. System Health & Diagnostic Utility (`app/infrastructure/diagnostics/health.py`):
     - `SystemHealthService` inspecting database integrity, schema alignment, storage write permissions, free disk space (GB), cryptographic key roundtrip, and document rendering module availability (`openpyxl`, `docx`, `reportlab`, `PySide6`).
     - Command-line runner (`python -m app.infrastructure.diagnostics.health`) with ASCII table formatting for Windows console compatibility.
  3. Turnkey Demo Project Generator (`app/application/services/demo_service.py`):
     - Generates benchmark industrial project: *Aerospace Dynamics Technologies Private Limited* (₹10.00 Cr project, ₹6.50 Cr SBI Term Loan, ₹3.50 Cr Promoter Equity, 7-year horizon).
     - Computes balanced statements, DSCR (~1.65x), and project IRR (~22.4%).
     - Wired into Dashboard via **"✨ Load Demo Project"** button for instant exploration.
  4. PyInstaller Windows Packaging Specification (`project_report_manager.spec`):
     - Configured for single-directory/single-file desktop deployment.
     - Bundles `alembic.ini`, `migrations/versions`, `openpyxl`, `reportlab`, `docx`, `cryptography`, and `PySide6`.
     - Packaging verification utility (`scripts/verify_distribution.py`) validating entry points, specs, migrations, and dependencies.
  5. Comprehensive User & Release Documentation:
     - `docs/USER_MANUAL.md`: Complete operations manual covering installation, setup, all 6 constitutions, capex, working capital, projection execution, appraisal, report export, and backup/restore.
     - `docs/RELEASE_CHECKLIST.md`: Release verification protocol covering architecture, decimal integrity, zero-plug invariant, multi-format parity, and security sign-off.
     - `README.md`: Updated comprehensive repository overview, quickstart guide, test commands, and documentation index.
  6. Automated Test Suite:
     - `tests/integration/test_phase6_hardening.py` testing diagnostics, demo generation, and distribution verification.
     - Full test suite: 54 passed tests in 10.48s (100% pass rate).
- **Files changed / created:**
  - `app/infrastructure/database/migration_manager.py`
  - `app/infrastructure/diagnostics/__init__.py`
  - `app/infrastructure/diagnostics/health.py`
  - `app/application/services/demo_service.py`
  - `app/application/services/__init__.py`
  - `app/presentation/views/dashboard_view.py`
  - `app/presentation/main_window.py`
  - `app/main.py`
  - `project_report_manager.spec`
  - `scripts/verify_distribution.py`
  - `docs/USER_MANUAL.md`
  - `docs/RELEASE_CHECKLIST.md`
  - `README.md`
  - `tests/integration/test_phase6_hardening.py`
  - `harness/build-log.md`
- **Database migrations:** None (all Phase 1–5 schemas verified).
- **Tests/commands executed:**
  - `python -m pytest tests/`
  - `python scripts/verify_distribution.py`
  - `python -m app.infrastructure.diagnostics.health`
- **Test results:** 54 passed in 10.48s (100% passing, 0 warnings, 0 failures).
- **Known issues:** None.
- **Rollback notes:** Revert git commit.
- **Release Status:** Ready for production release tag v1.0.0.



