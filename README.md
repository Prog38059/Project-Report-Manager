# Project Report Manager v1.0
**Enterprise Financial Projections & Bank CMA Report Generator**

[![Build Status](https://img.shields.io/badge/tests-51%20passed-brightgreen.svg)]()
[![Python](https://img.shields.io/badge/python-3.11%20%7C%203.12%20%7C%203.13%20%7C%203.14-blue.svg)]()
[![Platform](https://img.shields.io/badge/platform-Windows%2010%20%2F%2011%20(64--bit)-lightgrey.svg)]()
[![License](https://img.shields.io/badge/license-Proprietary%20%2F%20CA%20Practice-orange.svg)]()

**Project Report Manager** is a professional Windows desktop application engineered for Chartered Accountants, corporate finance advisors, credit analysts, and project appraisal consultants. It automates the preparation of bankable project reports, Credit Monitoring Arrangement (CMA) books, and integrated 7-year financial projection models across all recognized Indian legal constitutions.

---

## Key Features

- **Exact Decimal Arithmetic**: Strict integer paise representation eliminates binary floating-point inaccuracies.
- **Strict Zero-Plug Balance Sheet Invariant**: Total Assets strictly equal Total Liabilities & Equity in every year without unexplained balancing plugs or suspense figures.
- **All 6 Indian Legal Constitutions**: Proprietorship, Partnership Firm, LLP, Private Limited, Public Limited, and Trust/Society.
- **Dual Depreciation Books**: Full separation between Companies Act 2013 book depreciation (SLM/WDV) and Income Tax Act 1961 Section 32 block depreciation (>180 / <180 days rule).
- **Lender Appraisal & Stress Testing**: Gross Cash Flow DSCR, Net CFADS DSCR, ROCE %, RONW %, Break-Even capacity utilization %, and sensitivity analysis (+/-5%, +/-10% price and raw material shocks).
- **Triple-Format Report Export**:
  - 📗 **Excel (`.xlsx`)**: 9-sheet workbook with institutional styling, freeze panes locked on Column D (`D5`), and Indian number grouping.
  - 📘 **Word (`.docx`)**: Detailed Project Report (DPR) book with cover page, narrative, and repeating table headers.
  - 📕 **PDF (`.pdf`)**: A4 Landscape publication with running headers, footers, canonical input hash, and dynamic "Page X of Y" pagination.
- **Security & Verified Backup**: Local SQLite database with WAL mode, DPAPI/Fernet encryption key separation, full PAN masking, and atomic backup/restore with manifest checksum validation.

---

## System Requirements

- **Operating System**: Windows 10 or Windows 11 (64-bit).
- **Python**: 3.11, 3.12, 3.13, or 3.14 (64-bit).
- **Disk Space**: At least 500 MB free space on a local drive (`C:` or `D:`).
- *Note*: Network shares (UNC paths) and cloud-synced folders (OneDrive) are blocked to prevent SQLite database corruption.

---

## Quick Start & Installation

```powershell
# 1. Clone repository
git clone https://github.com/Prog38059/Project-Report-Manager.git
cd Project-Report-Manager

# 2. Install dependencies
pip install -e .

# 3. Run System Diagnostics & Health Check
python -m app.infrastructure.diagnostics.health

# 4. Launch Desktop GUI Application
python -m app.main
```

### Try the Turnkey Benchmark Demo
In the application Dashboard, click **"✨ Load Demo Project"** to instantly generate a full 7-year institutional aerospace manufacturing project with balanced statements, debt amortization, and DSCR metrics.

---

## Running the Automated Test Suite

```powershell
# Run all unit and integration tests
python -m pytest tests/ -v

# Run distribution packaging check
python scripts/verify_distribution.py
```

---

## Documentation Index

- [User Manual & Operations Guide](docs/USER_MANUAL.md) — Complete user guide and walkthrough.
- [Release Verification Checklist](docs/RELEASE_CHECKLIST.md) — Pre-release sign-off protocol.
- [Product Requirements](docs/01_PRODUCT_REQUIREMENTS.md) — Functional requirements and scope.
- [Technical Architecture Baseline](docs/02_TECHNICAL_ARCHITECTURE_BASELINE_v1.1.md) — System boundaries.
- [Database Data Dictionary](docs/03_DATABASE_DATA_DICTIONARY.md) — Tables, columns, and constraints.
- [Financial Model Specification](docs/04_FINANCIAL_MODEL_SPECIFICATION.md) — Formula contracts.
- [Statement Catalogue & Mappings](docs/05_STATEMENT_CATALOGUE_AND_MAPPINGS.md) — 3-statement lines.
- [Report Output Specification](docs/07_REPORT_OUTPUT_SPECIFICATION.md) — Excel, Word, and PDF layouts.
- [Security, Storage & Backup](docs/10_SECURITY_STORAGE_BACKUP.md) — Data protection and recovery.
