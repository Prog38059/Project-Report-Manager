# Project Report Manager — User Manual & Operations Guide
**Version 1.0.0 | Release: November 2026**

---

## 1. Introduction & Overview

**Project Report Manager** is an enterprise-grade Windows desktop application purpose-built for Chartered Accountants, corporate finance advisors, bank credit analysts, and project appraisal consultants. It automates the preparation of bankable Project Reports, Credit Monitoring Arrangement (CMA) data books, and integrated 7-year financial projection models across all recognized Indian legal constitutions and business models.

### Key Architectural Strengths:
- **Exact Decimal Financial Arithmetic**: Strict integer paise representation eliminates floating-point inaccuracies.
- **Strict Zero-Plug Balance Sheet Invariant**: Assets strictly equal Liabilities plus Equity without arbitrary suspense accounts or balancing figures.
- **Dual Depreciation Books**: Full separation between Companies Act 2013 book depreciation (SLM/WDV) and Income Tax Act 1961 Section 32 block depreciation.
- **Configurable Lender DSCR**: Evaluates both Gross Cash Flow DSCR and Net Operating CFADS (Cash Flow Available for Debt Service) DSCR.
- **Triple-Format Report Export**: Export financial projections into institutional Excel workbooks (`.xlsx` with freeze panes on Column D), Word DPR documents (`.docx`), and Landscape A4 PDF packages (`.pdf`).

---

## 2. System Requirements & Installation

- **Operating System**: Windows 10 or Windows 11 (64-bit).
- **Runtime**: Python 3.11, 3.12, 3.13, or 3.14 (64-bit).
- **RAM**: Minimum 4 GB (8 GB recommended).
- **Disk Storage**: At least 500 MB free disk space on a local drive (`C:` or `D:`).
- **Important**: The application database must remain on a local disk. Network shares (UNC paths) and cloud-synced folders (OneDrive/Dropbox) are intentionally blocked to guarantee SQLite database integrity.

### Quick Setup:
```powershell
# 1. Clone repository
git clone https://github.com/Prog38059/Project-Report-Manager.git
cd Project-Report-Manager

# 2. Install dependencies
pip install -e .

# 3. Verify system health & diagnostics
python -m app.infrastructure.diagnostics.health

# 4. Launch Application
python -m app.main
```

---

## 3. Launching the App & Using the Turnkey Demo

Upon launching the application, you are greeted with the **Dashboard**.

### Quick Start with 1-Click Demo Project:
1. Click the **"✨ Load Demo Project"** button in the **Quick Actions** section.
2. The application will instantly create:
   - **Client**: `Aerospace Dynamics Group`
   - **Entity**: `Aerospace Dynamics Technologies Private Limited` (Private Limited with two Directors)
   - **Project**: `Aerospace Machining & Turbine Assembly Unit` (7-year horizon)
   - **Capital Expenditure**: ₹10.00 Crores itemized across Land, Civil Works, CNC Machining Centers, Electrical Utilities, and Pre-operatives.
   - **Funding Structure**: ₹6.50 Crores Term Loan (SBI, 10.75%, 84 months) + ₹3.50 Crores Promoter Equity (Debt-to-Equity: 1.86x).
   - **Projections**: 7-year multi-year model with balanced Zero-Plug statements, DSCR (~1.65x average), and IRR (~22.4%).
3. The interface automatically navigates to the **Statements View**, allowing you to inspect the Profit & Loss, Balance Sheet, and Cash Flow accounts immediately.

---

## 4. End-to-End Workflow Guide

### Step 1: Client & Legal Entity Setup
1. Navigate to **👥 Clients** on the left rail. Click **"+ Add Client"** and record client details.
2. Navigate to **🏛 Entities**. Click **"+ Add Entity"** and select the applicable Indian legal constitution:
   - Individual / Sole Proprietorship
   - Partnership Firm (Indian Partnership Act 1932)
   - Limited Liability Partnership (LLP Act 2008)
   - Private Limited Company (Companies Act 2013)
   - Public Limited Company (Companies Act 2013)
   - Trust / Society / Section 8 Company
3. Record Member / Director details, PAN, and equity/profit sharing percentages.

### Step 2: Create a Project
1. Navigate to **📁 Projects** and click **"🚀 New Project Wizard"**.
2. Select the client and entity.
3. Enter Project Name, Project Nature (`NEW` greenfield, `EXPANSION`, `MODERNIZATION`, or `DIVERSIFICATION`).
4. Set the **Projection Start Financial Year** (e.g., `2026` for FY 2026-27) and horizon (default **7 years**).
5. The wizard automatically generates the 7 project period records.

### Step 3: Capital Expenditure (Capex) & Means of Finance
1. Under the **Project Costs** tab, enter itemized capital expenditure items:
   - Select cost head (Land, Building, Plant & Machinery, Electricals, Utilities, Pre-operative).
   - Enter basic amount in Rupees.
   - Select applicable GST rate (0%, 5%, 12%, 18%, 28%).
   - Set ITC (Input Tax Credit) eligibility percentage:
     - 100% ITC (e.g. Plant & Machinery): GST is recoverable as input credit; capitalized amount equals basic cost.
     - 0% ITC (e.g. Factory Building construction): GST is added to the asset value and capitalized into gross block for depreciation.
2. Under the **Means of Finance** tab, enter funding sources:
   - Add Term Debt, Promoters' Equity, Unsecured Loans, or Government Subsidies.
   - The system displays the live reconciliation: **Total Capex vs Total Funding**. A balanced plan displays ₹0 funding gap.

### Step 4: Revenue & Expense Projections
1. Under the **Revenue Streams** tab, configure product or service lines:
   - Choose from 9 built-in forecasting methods (Quantity x Price, Capacity Utilization Ramp, Flat Growth %, Seasonal/Cyclical, Contractual Milestone, Subscription/Retainer, etc.).
   - Define baseline capacity and 7-year ramp-up percentages (e.g., 55% -> 65% -> 75% -> 80% -> 85% -> 85% -> 85%).
2. Under the **Operating Expenses** tab, define fixed and variable cost items:
   - Raw materials, direct factory labor, power & fuel, maintenance, administrative overheads, selling expenses.

### Step 5: Execute Projections & Review Statements
1. Navigate to **📈 Statements** on the left rail.
2. Click **"⚡ Run Financial Projections"**.
3. The engine compiles the integrated 3-statement model:
   - **Projected Profit & Loss**: Revenue, COGS, EBITDA, Book Depreciation, EBIT, Finance Charges, EBT, Corporate Tax Provision, and PAT.
   - **Projected Balance Sheet**: Sources of Funds (Share Capital, Reserves & Surplus, Term Debt, Working Capital Borrowings) and Application of Funds (Gross Block, Accumulated Dep, Net Block, Net Working Capital, Cash & Bank Balances).
   - **Projected Cash Flow (Indirect Method)**: Operating, Investing, and Financing Cash Flows.
4. **Zero-Plug Status**: Check the status badge at top right: `PASSED: ZERO-PLUG INVARIANT MAINTAINED`.

### Step 6: Review Lender Appraisal & Stress Testing
1. Navigate to **⚖️ Appraisal & Audit** on the left rail.
2. Click **"⚡ Evaluate Appraisal"**.
3. Inspect the 4 KPI cards and sub-tabs:
   - **Financial Ratios & DSCR**: Gross DSCR, Net CFADS DSCR, Current Ratio, Quick Ratio, Debt-Equity Ratio, ROCE, RONW.
   - **Break-Even Analysis**: Fixed vs Variable cost segregation, Contribution Margin %, Break-Even Sales, and Break-Even Capacity %.
   - **Sensitivity Matrix**: Real-time stress test on +/-5% and +/-10% variations in Selling Price and Raw Material Costs.
   - **Validation Audit**: Rule-by-rule accounting integrity audit (checking for negative cash, DSCR dips below 1.10x, or leverage violations).

### Step 7: Export Multi-Format Reports
1. Navigate to **📑 Reports & Export** on the left rail.
2. Select your project and scenario.
3. Select Report Template:
   - *Standard Bank CMA & Appraisal Book*
   - *Detailed Project Report (DPR - Full)*
   - *Executive Summary & Term Sheet*
4. Click an export action:
   - 📗 **Export Excel (.xlsx)**: Produces an institutional 9-worksheet workbook with freeze panes locked at `D5`.
   - 📘 **Export Word (.docx)**: Produces a formatted DPR document with cover page, narrative, and repeating table headers.
   - 📕 **Export PDF (.pdf)**: Produces an A4 Landscape publication with running headers, footers, and dynamic page numbering.
   - 🚀 **Export All Formats (Bundle)**: Generates all three formats simultaneously into your selected destination folder.
5. All generated files are tracked in the **Generated Reports & Audit Trail** table with file size and SHA-256 cryptographic digest. Double-click any row to open the file directly in Microsoft Excel, Word, or your PDF viewer.

---

## 5. Security, Backups & Disaster Recovery

### Creating a Backup:
1. Navigate to **💾 Backup & Restore**.
2. Click **"📦 Create Backup Now"**.
3. Select a safe destination folder (external USB drive, secure local archive).
4. The system creates an atomic, transactionally consistent `.zip` archive containing the SQLite database, all project attachments, and a signed SHA-256 manifest.

### Restoring a Backup:
1. Under **Restore Project Data**, select your backup archive.
2. Click **"🔄 Restore from Backup"**.
3. The restore engine validates manifest checksums, runs SQLite physical integrity checks, verifies Alembic schema compatibility, and restores project files safely with automatic rollback on failure.

---

## 6. System Diagnostics & Health Check CLI

To run a complete diagnostic scan of your environment from the command line:
```powershell
python -m app.infrastructure.diagnostics.health
```
This inspects database integrity, schema migrations, write permissions across storage directories, free disk space, cryptography engines, and document rendering packages (`openpyxl`, `docx`, `reportlab`, `PySide6`).
