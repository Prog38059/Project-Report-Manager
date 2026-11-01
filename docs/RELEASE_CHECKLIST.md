# Project Report Manager — Release Verification Checklist
**Version 1.0.0 | Release Sign-Off**

---

## 1. Architectural Boundaries & Domain Separation
- [x] **Pure Domain Engine**: `app/domain/financial/` has zero dependencies on `PySide6`, `SQLAlchemy`, `openpyxl`, `python-docx`, or `reportlab`.
- [x] **No Recalculation by Renderers**: Excel, Word, and PDF renderers consume the pre-calculated `ProjectReportDataDTO` container without re-evaluating formulas or projections.
- [x] **GUI Role Strictness**: GUI views (`app/presentation/views/`) strictly format and display data; no financial, loan, or tax formulas exist in GUI code.
- [x] **Local SQLite Restriction**: Network UNC shares (`\\server\share`) and cloud-synced folders are rejected by `AppConfig` path security validation.

---

## 2. Financial Integrity & Calculation Non-Negotiables
- [x] **Decimal Currency Precision**: All currency amounts represented using Python `Decimal` and integer paise. Python `float` is strictly forbidden and rejected by type validation.
- [x] **Zero-Plug Balance Sheet Invariant**: In every projection period, $\text{Total Assets} \equiv \text{Total Liabilities \& Equity}$ to the exact integer paise without balancing figures or suspense accounts.
- [x] **Dual Depreciation Accounting**: Companies Act 2013 Book Depreciation (SLM / WDV) is accounted separately from Income Tax Act 1961 Section 32 block depreciation.
- [x] **Tax & ITC Handling**: Recoverable Input Tax Credit (ITC) is separated from gross capex cost; non-creditable GST is capitalized into gross block.
- [x] **Lender DSCR Variants**: Configurable evaluation of both Gross Cash Flow DSCR and Net Operating CFADS (Cash Flow Available for Debt Service) DSCR.
- [x] **Exact IRR Root Finding**: 60-iteration exact Decimal bisection method accurate to within 1 paise without external numerical C-libraries (`numpy`/`scipy`).
- [x] **Loan Principal Accounting**: Loan principal repayments are routed to liabilities reduction in the Balance Sheet and Financing Cash Flow, never expensed in Profit & Loss.

---

## 3. Reporting & Presentation Layouts
- [x] **Standard Horizontal Layout**: Main statements use standard columns:
  - Column A: Sr. No.
  - Column B: Note / Schedule Reference
  - Column C: Particulars
  - Columns D:J: Project Years 1–7
- [x] **Excel Freeze Panes**: Freeze panes locked at cell `D5` across financial statement sheets so Columns A–C remain visible during horizontal scrolling.
- [x] **Indian Number Formatting**: Currency formatted using Indian grouping (`₹ #,##,##0.00`).
- [x] **Word Table Header Repeat**: Word tables include `tblHeader` and `cantSplit` XML flags to ensure headers repeat cleanly across multi-page tables.
- [x] **PDF Landscape Numbered Canvas**: Two-pass `NumberedCanvas` renders running headers, canonical input hashes, and dynamic "Page X of Y" page counts on A4 Landscape canvas.

---

## 4. Security, Local Storage & Audit Trails
- [x] **Cryptographic Key Separation**: Encryption keys managed separately from the SQLite database via `EncryptionService`.
- [x] **Sensitive Data Redaction**: Full PANs masked (`XXXXX1234F`) in ordinary views and logs.
- [x] **Path Traversal Protection**: Attachment filenames and export output paths sanitized to prevent directory traversal.
- [x] **Cryptographic Hashes**: SHA-256 digests computed and recorded for immutable calculation run snapshots, generated reports, and backup manifests.
- [x] **Backup & Verified Restore**: Backup archives validated through manifest checksums, SQLite PRAGMA integrity check, and Alembic schema verification.

---

## 5. Packaging & Verification Sign-Off
- [x] **Distribution Spec**: `project_report_manager.spec` configured with hidden imports and migration datas.
- [x] **Packaging Prerequisites**: `scripts/verify_distribution.py` passes cleanly.
- [x] **System Diagnostics**: `python -m app.infrastructure.diagnostics.health` reports overall status `HEALTHY` / `DEGRADED` (0 failed checks).
- [x] **Automated Test Suite**: All 51+ unit and integration tests passing across all test modules.
- [x] **Benchmark Demo Project**: 1-click turnkey demo generator verified and accessible via Dashboard.
