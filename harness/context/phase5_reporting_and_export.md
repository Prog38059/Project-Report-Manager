# Phase 5 Context — Report Generation & Multi-Format Export Engine

## Objectives Achieved
1. **Shared Report Data Model & Invariant Enforcement**:
   - `app/application/dtos/report_dto.py`:
     - `ProjectReportDataDTO` serves as the single source of truth across all renderers.
     - Enforces the non-negotiable architectural invariant: renderers consume pre-calculated figures and never recalculate numbers.
     - Contains:
       - `ReportDocumentMetadataDTO`: Project name, entity legal name, client name, calculation run number, engine version, canonical input hash, generation timestamp, template metadata.
       - `ExecutiveSummaryDTO`: Project cost, funding breakdown, IRR %, NPV, payback period, average gross DSCR, ROCE %, RONW %, and year 1 break-even capacity.
       - `CostAndFundingDTO`: Itemized capital expenditure, GST components, capitalized cost, means of finance, debt-equity percentages.
       - `HorizontalStatementDTO`: Projected Profit & Loss, Projected Balance Sheet, and Projected Cash Flow (Indirect Method) with standard horizontal layout (Column A = Sr. No., B = Note/Schedule, C = Particulars, Columns D:J = Years 1–7).
       - `AnnualLoanSummaryDTO`: Annual loan balance, disbursement, principal repaid, interest paid, total debt service, and closing balance.
       - `AssetScheduleRowDTO`: Gross block additions, disposals, depreciation, accumulated depreciation, and net book value.
       - `AppraisalReportDTO`: Ratios, break-even indicators, sensitivity matrix, and cross-statement validation audit outcomes.

2. **Excel Multi-Worksheet Workbook Renderer (`app/infrastructure/reporting/excel_renderer.py`)**:
   - Built using `openpyxl` with institutional lender formatting (navy headers `#1B365D`, subtle zebra striping, thin borders).
   - Generates 9 comprehensive worksheets:
     1. `Executive Summary`: High-level metrics, promoter details, project indicators.
     2. `Projected P&L`: Multi-year profit and loss account.
     3. `Projected Balance Sheet`: Multi-year assets and liabilities with zero-plug assertion.
     4. `Projected Cash Flow`: Multi-year cash flow via indirect method.
     5. `Ratios & DSCR`: Complete financial ratios and debt service appraisal.
     6. `Break-Even & Sensitivity`: Break-even sales, capacity %, margin of safety, and shock matrices.
     7. `Loan Amortization`: Annualized debt repayment and service schedule.
     8. `Fixed Assets & Dep`: Fixed asset schedule, additions, book depreciation, and net block.
     9. `Audit & Validation`: Cross-statement integrity certificate, validation error/warning list.
   - Enforces the mandatory presentation rule: freeze panes locked at `D5` so descriptive columns A–C remain permanently visible during horizontal scrolling across projection years.
   - Applies Indian currency formatting pattern `₹ #,##,##0.00` to all monetary cells.

3. **Word Document Renderer (`app/infrastructure/reporting/docx_renderer.py`)**:
   - Built using `python-docx` to format detailed Bank Credit Appraisal Books & DPRs.
   - Includes:
     - Formatted cover page with project title, entity name, submission date, and document control block.
     - Executive summary narrative and key indicator cards.
     - Cost of project and means of finance breakdown tables.
     - Horizontal financial statement tables for P&L, Balance Sheet, and Cash Flow with repeating header rows (`tblHeader` and `cantSplit` XML flags for clean multi-page pagination).
     - Loan repayment summary and DSCR coverage analysis.
     - Operational sensitivity scenario comparison table.
     - Cross-statement audit certificate signed with canonical calculation run input hash.

4. **PDF Landscape Document Renderer (`app/infrastructure/reporting/pdf_renderer.py`)**:
   - Built using `reportlab` on A4 Landscape canvas (`pagesizes.landscape(A4)`).
   - Implements a two-pass `NumberedCanvas` delivering running headers with document title and running footers with generation date, engine input hash, and dynamic "Page X of Y" numbering.
   - Flowables include:
     - Multi-year horizontal financial statement tables with wrapped particulars and right-aligned currency columns.
     - Executive summary KPI grid and appraisal highlights.
     - Term loan debt service schedule and DSCR appraisal metrics.
     - Operational sensitivity matrix and cross-statement invariant validation certificate.

5. **Report Application Service & Audit Logging (`app/application/services/report_service.py`)**:
   - `build_report_data_model`: Assembles the immutable `ProjectReportDataDTO` from the database.
   - `generate_report`: Generates Excel, Word, or PDF documents, calculates SHA-256 file hashes, records entries in `generated_reports` database table, and returns `GeneratedReportResultDTO`.
   - `list_generated_reports`: Queries previously generated reports for audit trails.

6. **Database Persistence & Alembic Migration 0005 (`migrations/versions/0005_phase5_reporting.py`)**:
   - Tables: `report_templates`, `report_template_sections`, and `generated_reports`.
   - Seeded standard templates:
     - `TMPL_CMA_BANK`: Standard Bank CMA & Project Appraisal Book.
     - `TMPL_DPR_FULL`: Detailed Project Report (DPR - Full).
     - `TMPL_EXEC_SUMMARY`: Executive Summary & Term Sheet.

7. **Desktop GUI View (`app/presentation/views/report_view.py`)**:
   - Project & Scenario selection combo boxes.
   - Report template selector.
   - Export action buttons: Excel (`.xlsx`), Word (`.docx`), PDF (`.pdf`), and Export All Formats (Bundle).
   - Live KPI summary card and historical audit table of all previously generated files with double-click file launcher.
   - Integrated into `MainWindow` navigation rail with index 6.

8. **Testing & Verification**:
   - `tests/integration/test_report_service.py`: Verifies full report generation workflow across Excel, Word, and PDF, file size, byte signatures, freeze pane layout, table structures, and cross-renderer numerical agreement.
   - `tests/integration/test_ui_views.py`: Verifies UI instantiation and nav rail navigation.
   - Total test suite: 51 tests passing in 11.04s.
