# Database Data Dictionary and Implementation Schema

**Purpose:** Turn the logical architecture into an implementation-level database design. This document is a specification; the coding agent must review it, identify omissions and propose migrations before writing ORM models.

## 1. Canonical storage conventions

| Concern | Rule |
|---|---|
| Primary keys | UUID. SQLite representation may be 36-character text initially; use one consistent SQLAlchemy UUID type abstraction. |
| Foreign keys | Explicit, indexed where used in joins. Use RESTRICT for records referenced by calculation runs/reports; use CASCADE only for disposable child rows in draft-owned aggregates after explicit review. |
| Monetary values | Integer paise (`BIGINT`, suffix `_paise`). Convert to/from `Decimal` only in domain services. |
| Rates, percentages, quantities | Exact decimal values. SQLite-friendly canonical decimal strings (`VARCHAR` with validation) are acceptable; never persist binary float. Define precision/scale per field. |
| Dates | ISO date / SQL `DATE`; financial period start and end inclusive. |
| Timestamps | UTC ISO timestamp with timezone; display in local timezone. |
| Boolean | SQL Boolean; SQLite representation handled by SQLAlchemy. |
| JSON snapshots | Versioned JSON text, validated against a schema before storing. Never use JSON as a substitute for core relational fields. |
| Codes | Stable uppercase machine codes; labels are separate editable display text. |
| Soft delete | Prefer `is_active` / `archived_at`; do not hard-delete items referenced by an approved run. |
| Audit | Store who/when/what changed for material records; never log credentials or full sensitive identifiers. |

### Common columns
Where appropriate, mutable master/input tables should include:
- `id UUID PK`
- `created_at TIMESTAMP NOT NULL`
- `updated_at TIMESTAMP NOT NULL`
- `created_by_label VARCHAR(100) NULL`
- `updated_by_label VARCHAR(100) NULL`
- `is_active BOOLEAN NOT NULL DEFAULT TRUE` for reusable masters

Do not add common columns mechanically to immutable result tables; those use run creation metadata and should not be editable.

## 2. Identity and entity tables

### 2.1 `clients`
- `id UUID PK`
- `client_code VARCHAR(30) NOT NULL UNIQUE`
- `display_name VARCHAR(200) NOT NULL`
- `client_category VARCHAR(30) NOT NULL` (e.g. PERSON, BUSINESS, OTHER)
- `phone VARCHAR(30) NULL`
- `email VARCHAR(254) NULL`
- `address_text TEXT NULL`
- `notes TEXT NULL`
- common audit columns

Indexes: unique `client_code`; index on `display_name`.

### 2.2 `entities`
- `id UUID PK`
- `client_id UUID FK clients.id NOT NULL`
- `constitution_code VARCHAR(30) NOT NULL` (`INDIVIDUAL`, `PROPRIETORSHIP`, `HUF`, `PARTNERSHIP`, `LLP`, `PRIVATE_LIMITED`, future codes)
- `legal_name VARCHAR(250) NOT NULL`
- `trade_name VARCHAR(250) NULL`
- `business_description TEXT NULL`
- `accounting_framework_code VARCHAR(40) NULL`
- `tax_profile_code VARCHAR(40) NULL`
- `date_of_formation DATE NULL`
- `active_flag BOOLEAN NOT NULL DEFAULT TRUE`
- common audit columns

Indexes: `(client_id, legal_name)`, `constitution_code`. Do not assume a proprietorship is a separate incorporated legal person.

### 2.3 `entity_identifiers`
- `id UUID PK`
- `entity_id UUID FK entities.id NOT NULL`
- `identifier_type VARCHAR(30) NOT NULL` (PAN, GSTIN, TAN, CIN, LLPIN, UDYAM, OTHER)
- `identifier_value_encrypted TEXT NOT NULL` for sensitive values; provide a masked display value separately if needed
- `identifier_value_hash VARCHAR(128) NULL` for duplicate detection without plaintext indexing
- `valid_from DATE NULL`, `valid_to DATE NULL`
- `verification_status VARCHAR(25) NOT NULL DEFAULT 'UNVERIFIED'`
- `source_attachment_id UUID FK attachments.id NULL`
- `notes TEXT NULL`
- common audit columns

Indexes: `(entity_id, identifier_type)`, `identifier_value_hash`. Uniqueness policy must be configurable by identifier type/jurisdiction; do not assume a database-global uniqueness rule for every identifier.

### 2.4 `entity_members`
- `id UUID PK`
- `entity_id UUID FK entities.id NOT NULL`
- `full_name VARCHAR(200) NOT NULL`
- `role_code VARCHAR(35) NOT NULL` (INDIVIDUAL_APPLICANT, PROPRIETOR, KARTA, COPARCENER, PARTNER, DESIGNATED_PARTNER, DIRECTOR, SHAREHOLDER, PROMOTER, AUTHORISED_SIGNATORY, OTHER)
- `pan_encrypted TEXT NULL`
- `address_text TEXT NULL`
- `contact_phone VARCHAR(30) NULL`
- `contact_email VARCHAR(254) NULL`
- `profit_share_pct DECIMAL_TEXT NULL`
- `shareholding_pct DECIMAL_TEXT NULL`
- `capital_commitment_paise BIGINT NULL`
- `date_from DATE NULL`, `date_to DATE NULL`
- `notes TEXT NULL`
- common audit columns

Validation: percentages must be in the range permitted by the applicable field; aggregate ratios require an explicit validation rule. Do not silently force all partner or shareholder percentages to 100% if the project has not supplied complete information.

### 2.5 Constitution extension tables

`huf_details`: `entity_id UUID PK/FK`, `karta_member_id UUID FK entity_members.id NOT NULL`, `formation_note TEXT NULL`. Validate that Karta belongs to the same entity.

`proprietorship_details`: `entity_id UUID PK/FK`, `proprietor_member_id UUID FK entity_members.id NOT NULL`, `business_start_date DATE NULL`. Validate member role PROPRIETOR and matching entity.

`partnership_details`: `entity_id UUID PK/FK`, `deed_date DATE NULL`, `registration_status VARCHAR(25) NULL`, `deed_attachment_id UUID FK attachments.id NULL`.

`llp_details`: `entity_id UUID PK/FK`, `incorporation_date DATE NULL`, `llp_agreement_date DATE NULL`, `agreement_attachment_id UUID FK attachments.id NULL`.

`company_details`: `entity_id UUID PK/FK`, `incorporation_date DATE NULL`, `company_class VARCHAR(30) NULL`, `authorised_capital_paise BIGINT NULL`, `paid_up_capital_paise BIGINT NULL`, `registered_office_address TEXT NULL`.

Individual profile-specific personal fields should be collected only when required for the project/report. Consider a later `individual_details` extension rather than overloading `entities` with sensitive personal information.

## 3. Project, periods and scenarios

### 3.1 `projects`
- `id UUID PK`
- `entity_id UUID FK entities.id NOT NULL`
- `project_code VARCHAR(30) NOT NULL`
- `project_name VARCHAR(250) NOT NULL`
- `industry_code VARCHAR(40) NULL`
- `business_model_code VARCHAR(40) NULL`
- `project_nature_code VARCHAR(30) NOT NULL` (NEW, EXPANSION, MODERNISATION, DIVERSIFICATION, ACQUISITION, OTHER)
- `location_address TEXT NULL`, `district VARCHAR(100) NULL`, `state VARCHAR(100) NULL`, `pin_code VARCHAR(12) NULL`
- `project_description TEXT NULL`
- `implementation_start DATE NULL`
- `commercial_operation_date DATE NULL`
- `financial_year_start_month SMALLINT NOT NULL DEFAULT 4`
- `currency_code CHAR(3) NOT NULL DEFAULT 'INR'`
- `projection_granularity VARCHAR(15) NOT NULL DEFAULT 'ANNUAL'`
- `projection_year_count SMALLINT NOT NULL DEFAULT 7`
- `projection_start_financial_year SMALLINT NOT NULL` (start year, e.g. 2026 for FY 2026-27 under April–March convention)
- `historical_data_enabled BOOLEAN NOT NULL DEFAULT FALSE`
- `historical_year_count SMALLINT NULL`
- `statement_layout_code VARCHAR(40) NOT NULL DEFAULT 'HORIZONTAL_YEAR_COLUMNS'`
- `status_code VARCHAR(30) NOT NULL DEFAULT 'DRAFT'`
- common audit columns

Constraints: unique `(entity_id, project_code)`; projection horizon must be within configured application limits; financial-year start month 1–12.

### 3.2 `project_scenarios`
- `id UUID PK`
- `project_id UUID FK projects.id NOT NULL`
- `scenario_code VARCHAR(30) NOT NULL`
- `scenario_name VARCHAR(100) NOT NULL`
- `scenario_type VARCHAR(25) NOT NULL` (BASE, CONSERVATIVE, OPTIMISTIC, BANK_APPRAISAL, CUSTOM)
- `parent_scenario_id UUID FK project_scenarios.id NULL`
- `probability_pct DECIMAL_TEXT NULL`
- `is_default BOOLEAN NOT NULL DEFAULT FALSE`
- `notes TEXT NULL`
- common audit columns

Constraints: unique `(project_id, scenario_code)`; at most one default scenario per project (partial unique index where supported or service validation).

### 3.3 `project_periods`
- `id UUID PK`
- `project_id UUID FK projects.id NOT NULL`
- `period_sequence SMALLINT NOT NULL`
- `period_role VARCHAR(20) NOT NULL` (HISTORICAL, PROJECTION)
- `period_granularity VARCHAR(15) NOT NULL` (ANNUAL, QUARTERLY, MONTHLY)
- `period_label VARCHAR(50) NOT NULL`
- `period_type VARCHAR(20) NOT NULL` (FULL_YEAR, STUB_PERIOD, MONTH, QUARTER, OTHER)
- `start_date DATE NOT NULL`, `end_date DATE NOT NULL`
- `financial_year_label VARCHAR(30) NULL`
- `display_sequence SMALLINT NOT NULL`
- `is_report_column BOOLEAN NOT NULL DEFAULT TRUE`

Constraints: `start_date <= end_date`; unique `(project_id, period_role, period_granularity, period_sequence)`; periods of same granularity must not overlap unless explicitly supported. Create seven annual projection periods by default. Historical rows only when enabled. Project Year 1 may be a stub period if commercial operation begins part-way through a financial year; show the exact period dates in report assumptions.

### 3.4 `project_assumptions`
- `id UUID PK`
- `scenario_id UUID FK project_scenarios.id NOT NULL`
- `period_id UUID FK project_periods.id NULL`
- `assumption_code VARCHAR(60) NOT NULL`
- `value_type VARCHAR(15) NOT NULL` (DECIMAL, INTEGER, TEXT, BOOLEAN, DATE)
- `value_decimal_text VARCHAR(80) NULL`
- `value_text TEXT NULL`
- `unit_code VARCHAR(30) NULL`
- `projection_method VARCHAR(35) NULL`
- `source_id UUID FK project_sources.id NULL`
- `preparer_note TEXT NULL`
- `review_status VARCHAR(20) NOT NULL DEFAULT 'UNREVIEWED'`

Use only for supplementary extensible assumptions. Core financial drivers must remain in typed module tables. Add uniqueness on `(scenario_id, period_id, assumption_code)` with null-period handling in service logic.

## 4. Sources, attachments and audit

### `project_sources`
- `id UUID PK`, `project_id UUID FK NOT NULL`
- `source_type VARCHAR(30) NOT NULL` (VENDOR_QUOTE, BANK_TERM_SHEET, PROMOTER_ESTIMATE, GOVERNMENT_SOURCE, MARKET_STUDY, STATUTORY_SOURCE, OTHER)
- `source_title VARCHAR(250) NOT NULL`, `source_party VARCHAR(200) NULL`
- `source_date DATE NULL`, `source_reference VARCHAR(120) NULL`
- `verification_status VARCHAR(25) NOT NULL DEFAULT 'UNVERIFIED'`
- `review_note TEXT NULL`
- common audit columns

### `attachments`
- `id UUID PK`, `project_id UUID FK NOT NULL`, `source_id UUID FK project_sources.id NULL`
- `file_category VARCHAR(35) NOT NULL`, `original_filename VARCHAR(255) NOT NULL`
- `stored_relative_path TEXT NOT NULL`, `mime_type VARCHAR(120) NULL`, `file_size_bytes BIGINT NOT NULL`
- `sha256_hash CHAR(64) NOT NULL`, `uploaded_at TIMESTAMP NOT NULL`, `notes TEXT NULL`

Store files in managed project storage; reject path traversal and executable attachments by policy. The DB contains metadata, not binary blobs for ordinary documents.

### `audit_events`
- `id UUID PK`, `project_id UUID FK NULL`, `entity_id UUID FK NULL`
- `event_type VARCHAR(40) NOT NULL`, `record_type VARCHAR(60) NOT NULL`, `record_id VARCHAR(36) NOT NULL`
- `before_json TEXT NULL`, `after_json TEXT NULL`, `event_timestamp TIMESTAMP NOT NULL`, `actor_label VARCHAR(100) NULL`
- `change_reason TEXT NULL`

Do not place passwords, full PANs, bank credentials or unnecessary sensitive data in audit JSON.

## 5. Project cost and funding

### `project_cost_heads`
- `id UUID PK`, `head_code VARCHAR(40) UNIQUE NOT NULL`, `head_name VARCHAR(150) NOT NULL`
- `category_code VARCHAR(30) NOT NULL` (LAND, BUILDING, PLANT, OTHER_FIXED_ASSET, PREOPERATIVE, DEPOSIT, CONTINGENCY, WORKING_CAPITAL_MARGIN, OTHER)
- `capitalisation_default BOOLEAN NOT NULL`, `sort_order SMALLINT NOT NULL`, `active_flag BOOLEAN NOT NULL DEFAULT TRUE`

### `project_cost_items`
- `id UUID PK`, `scenario_id UUID FK NOT NULL`, `cost_head_id UUID FK NOT NULL`
- `description VARCHAR(250) NOT NULL`
- `quantity_decimal_text VARCHAR(80) NULL`, `unit_code VARCHAR(30) NULL`, `rate_decimal_text VARCHAR(80) NULL`
- `basic_amount_paise BIGINT NOT NULL`
- `gst_rate_pct_text VARCHAR(40) NULL`, `gst_amount_paise BIGINT NOT NULL DEFAULT 0`
- `eligible_itc_paise BIGINT NOT NULL DEFAULT 0`, `non_creditable_tax_paise BIGINT NOT NULL DEFAULT 0`
- `capitalised_amount_paise BIGINT NOT NULL DEFAULT 0`
- `project_cash_requirement_paise BIGINT NOT NULL DEFAULT 0`
- `payment_due_date DATE NULL`, `supplier_name VARCHAR(200) NULL`
- `source_id UUID FK project_sources.id NULL`, `notes TEXT NULL`

Rules: validate invoice/estimate reconciliation; do not derive capitalised amount from a blanket GST assumption. Separate capitalisable amounts from deposits, pre-operative costs, expenses and working-capital margin.

### `funding_heads`
- `id UUID PK`, `funding_code VARCHAR(40) UNIQUE NOT NULL`, `funding_name VARCHAR(150) NOT NULL`
- `funding_category VARCHAR(30) NOT NULL` (PROMOTER, PARTNER, SHARE_CAPITAL, TERM_LOAN, UNSECURED_LOAN, SUBSIDY, GRANT, WORKING_CAPITAL, OTHER)
- `sort_order SMALLINT NOT NULL`, `active_flag BOOLEAN NOT NULL DEFAULT TRUE`

### `funding_sources`
- `id UUID PK`, `scenario_id UUID FK NOT NULL`, `funding_head_id UUID FK NOT NULL`
- `source_name VARCHAR(200) NOT NULL`, `amount_paise BIGINT NOT NULL`
- `expected_date DATE NULL`, `status_code VARCHAR(20) NOT NULL DEFAULT 'PROPOSED'` (PROPOSED, COMMITTED, RECEIVED)
- `loan_facility_id UUID FK loan_facilities.id NULL`, `source_id UUID FK project_sources.id NULL`
- `terms_note TEXT NULL`, `notes TEXT NULL`

The funding service validates source/use reconciliation. Avoid circular insert ordering: loan facility can be created first and linked to the funding line.

## 6. Revenue and expense

### `revenue_methods`
- `method_code VARCHAR(40) PK`, `method_name VARCHAR(120) NOT NULL`, `description TEXT NULL`, `active_flag BOOLEAN NOT NULL`

Initial methods: `CAPACITY_UTILISATION_PRICE`, `UNITS_PRICE`, `CUSTOMERS_AVERAGE_BILL`, `OCCUPANCY_RATE`, `RENTAL_UNITS_RATE`, `HEADCOUNT_BILLING`, `TURNOVER_GROWTH`, `MANUAL`, `CUSTOM_REGISTERED_METHOD`.

### `revenue_streams`
- `id UUID PK`, `scenario_id UUID FK NOT NULL`, `stream_code VARCHAR(40) NOT NULL`, `stream_name VARCHAR(150) NOT NULL`
- `method_code VARCHAR(40) FK revenue_methods NOT NULL`, `unit_code VARCHAR(30) NULL`
- `gst_treatment_code VARCHAR(30) NOT NULL` (EXEMPT, NIL_RATED, ZERO_RATED, TAXABLE_EXCLUSIVE, TAXABLE_INCLUSIVE, OUT_OF_SCOPE, NOT_APPLICABLE, REVIEW_REQUIRED)
- `gst_rate_pct_text VARCHAR(40) NULL`, `active_flag BOOLEAN NOT NULL`, `notes TEXT NULL`
- unique `(scenario_id, stream_code)`

### `revenue_forecasts`
- `id UUID PK`, `revenue_stream_id UUID FK NOT NULL`, `period_id UUID FK NOT NULL`
- `capacity_decimal_text VARCHAR(80) NULL`, `utilisation_pct_text VARCHAR(40) NULL`
- `units_decimal_text VARCHAR(80) NULL`, `price_per_unit_decimal_text VARCHAR(80) NULL`
- `operating_days_decimal_text VARCHAR(80) NULL`, `growth_pct_text VARCHAR(40) NULL`
- `gross_billing_override_paise BIGINT NULL`, `calculation_mode VARCHAR(20) NOT NULL` (DRIVER, MANUAL_OVERRIDE)
- `source_id UUID FK project_sources.id NULL`, `notes TEXT NULL`
- unique `(revenue_stream_id, period_id)`

Computed gross billing, output tax and net revenue are calculation results, not mutable input fields. If a user overrides a computed result, store override value, reason and source explicitly.

### `expense_heads`
- `id UUID PK`, `expense_code VARCHAR(40) UNIQUE NOT NULL`, `expense_name VARCHAR(150) NOT NULL`
- `expense_group VARCHAR(30) NOT NULL` (DIRECT, EMPLOYEE, ADMIN, SELLING, FINANCE, TAX, OTHER)
- `default_cost_behaviour VARCHAR(20) NOT NULL` (FIXED, VARIABLE, SEMI_VARIABLE)
- `default_projection_method VARCHAR(30) NOT NULL`
- `active_flag BOOLEAN NOT NULL`

### `expense_forecasts`
- `id UUID PK`, `scenario_id UUID FK NOT NULL`, `expense_head_id UUID FK NOT NULL`, `period_id UUID FK NOT NULL`
- `projection_method VARCHAR(30) NOT NULL` (FIXED_AMOUNT, GROWTH, PERCENT_REVENUE, PER_UNIT, CAPACITY_BASED, HEADCOUNT_BASED, MANUAL)
- `base_amount_paise BIGINT NULL`, `growth_pct_text VARCHAR(40) NULL`, `revenue_pct_text VARCHAR(40) NULL`
- `unit_cost_decimal_text VARCHAR(80) NULL`, `quantity_driver_code VARCHAR(60) NULL`
- `manual_amount_paise BIGINT NULL`, `source_id UUID FK project_sources.id NULL`, `notes TEXT NULL`
- unique `(scenario_id, expense_head_id, period_id)`

## 7. Assets and depreciation

### `asset_categories`
- `id UUID PK`, `asset_code VARCHAR(40) UNIQUE NOT NULL`, `asset_name VARCHAR(150) NOT NULL`
- `default_useful_life_years_text VARCHAR(40) NULL`, `active_flag BOOLEAN NOT NULL`

### `asset_items`
- `id UUID PK`, `scenario_id UUID FK NOT NULL`, `asset_category_id UUID FK NOT NULL`
- `asset_code VARCHAR(40) NULL`, `asset_name VARCHAR(180) NOT NULL`, `asset_description TEXT NULL`
- `vendor_name VARCHAR(200) NULL`, `source_id UUID FK project_sources.id NULL`, `notes TEXT NULL`

### `asset_additions`
- `id UUID PK`, `asset_item_id UUID FK NOT NULL`, `period_id UUID FK NOT NULL`
- `gross_addition_paise BIGINT NOT NULL`, `eligible_itc_paise BIGINT NOT NULL DEFAULT 0`
- `capitalised_amount_paise BIGINT NOT NULL`, `put_to_use_date DATE NULL`
- `useful_life_years_text VARCHAR(40) NULL`, `book_depreciation_method VARCHAR(25) NOT NULL`
- `book_residual_value_paise BIGINT NOT NULL DEFAULT 0`, `tax_block_code VARCHAR(50) NULL`
- `source_id UUID FK project_sources.id NULL`, `notes TEXT NULL`

### `depreciation_policies`
- `id UUID PK`, `scenario_id UUID FK NULL`, `asset_category_id UUID FK NULL`
- `policy_type VARCHAR(20) NOT NULL` (BOOK, TAX)
- `method_code VARCHAR(25) NOT NULL` (SLM, WDV, UNITS_OF_PRODUCTION, MANUAL)
- `rate_pct_text VARCHAR(40) NULL`, `useful_life_years_text VARCHAR(40) NULL`
- `effective_from DATE NOT NULL`, `effective_to DATE NULL`
- `source_reference TEXT NULL`, `review_status VARCHAR(20) NOT NULL`

Do not set tax depreciation based only on asset category defaults. Tax treatment requires jurisdiction, tax year, asset classification and verified source.

## 8. Loans and working capital

### `loan_facilities`
- `id UUID PK`, `scenario_id UUID FK NOT NULL`, `facility_code VARCHAR(40) NOT NULL`
- `lender_name VARCHAR(180) NOT NULL`, `loan_type VARCHAR(30) NOT NULL`
- `sanctioned_amount_paise BIGINT NOT NULL`, `rate_type VARCHAR(15) NOT NULL` (FIXED, FLOATING)
- `interest_rate_pct_text VARCHAR(40) NOT NULL`, `repayment_method VARCHAR(30) NOT NULL` (EMI_REDUCING, EQUAL_PRINCIPAL, INTEREST_ONLY, CUSTOM)
- `repayment_frequency VARCHAR(15) NOT NULL` (MONTHLY, QUARTERLY, HALF_YEARLY, ANNUAL, CUSTOM)
- `tenure_count INTEGER NOT NULL`, `moratorium_count INTEGER NOT NULL DEFAULT 0`
- `interest_basis VARCHAR(20) NOT NULL` (MONTHLY_PERIODIC, ACT_365, ACT_360, ACT_ACT, LENDER_CUSTOM)
- `compounding_frequency VARCHAR(20) NULL`, `first_repayment_date DATE NULL`
- `processing_fee_paise BIGINT NOT NULL DEFAULT 0`, `prepayment_terms TEXT NULL`
- `source_id UUID FK project_sources.id NULL`, `notes TEXT NULL`
- unique `(scenario_id, facility_code)`

### `loan_disbursements`
- `id UUID PK`, `loan_facility_id UUID FK NOT NULL`, `disbursement_date DATE NOT NULL`
- `amount_paise BIGINT NOT NULL`, `source_id UUID FK project_sources.id NULL`, `notes TEXT NULL`

### `loan_rate_changes`
- `id UUID PK`, `loan_facility_id UUID FK NOT NULL`, `effective_date DATE NOT NULL`
- `annual_rate_pct_text VARCHAR(40) NOT NULL`, `source_id UUID FK project_sources.id NULL`, `notes TEXT NULL`

### `loan_repayment_overrides`
- `id UUID PK`, `loan_facility_id UUID FK NOT NULL`, `installment_number INTEGER NOT NULL`, `due_date DATE NOT NULL`
- `principal_override_paise BIGINT NULL`, `interest_override_paise BIGINT NULL`, `total_payment_override_paise BIGINT NULL`
- `reason TEXT NOT NULL`, `source_id UUID FK project_sources.id NULL`

### `working_capital_assumptions`
- `id UUID PK`, `scenario_id UUID FK NOT NULL`, `period_id UUID FK NOT NULL`
- `component_code VARCHAR(35) NOT NULL` (RAW_MATERIAL, WIP, FINISHED_GOODS, RECEIVABLES, PAYABLES, EXPENSE_CREDITORS, CASH, STATUTORY_DUES, OTHER)
- `method_code VARCHAR(25) NOT NULL` (HOLDING_DAYS, TURNOVER_PERCENT, DIRECT_AMOUNT, BANK_METHOD)
- `holding_days_text VARCHAR(40) NULL`, `turnover_pct_text VARCHAR(40) NULL`, `amount_override_paise BIGINT NULL`
- `source_id UUID FK project_sources.id NULL`, `notes TEXT NULL`
- unique `(scenario_id, period_id, component_code)`

## 9. Historical data and tax parameters

### `historical_statement_lines`
- `id UUID PK`, `project_id UUID FK NOT NULL`, `period_id UUID FK NOT NULL`
- `statement_type VARCHAR(20) NOT NULL` (PL, BS, CASH_FLOW)
- `line_code VARCHAR(60) NOT NULL`, `line_label VARCHAR(180) NOT NULL`
- `amount_paise BIGINT NOT NULL`, `source_id UUID FK project_sources.id NULL`
- `is_imported BOOLEAN NOT NULL DEFAULT FALSE`, `mapping_status VARCHAR(20) NOT NULL DEFAULT 'UNREVIEWED'`, `notes TEXT NULL`
- unique `(project_id, period_id, statement_type, line_code)`

UI and import workflow must remain hidden when `projects.historical_data_enabled = FALSE`.

### `tax_profiles`
- `id UUID PK`, `scenario_id UUID FK NOT NULL`, `entity_type_code VARCHAR(30) NOT NULL`
- `financial_year_label VARCHAR(30) NOT NULL`, `tax_regime_code VARCHAR(30) NULL`
- `tax_calculation_method VARCHAR(25) NOT NULL` (EFFECTIVE_RATE_ESTIMATE, BRACKET_ESTIMATE, USER_ENTERED, NOT_COMPUTED)
- `effective_tax_rate_pct_text VARCHAR(40) NULL`, `surcharge_pct_text VARCHAR(40) NULL`, `cess_pct_text VARCHAR(40) NULL`
- `loss_brought_forward_paise BIGINT NOT NULL DEFAULT 0`, `tax_override_note TEXT NULL`
- `source_reference TEXT NULL`, `review_status VARCHAR(20) NOT NULL`

### `tax_rule_versions`
- `id UUID PK`, `rule_code VARCHAR(60) NOT NULL`, `jurisdiction VARCHAR(80) NOT NULL`
- `entity_type_code VARCHAR(30) NULL`, `effective_from DATE NOT NULL`, `effective_to DATE NULL`
- `rule_value_text TEXT NOT NULL`, `source_title VARCHAR(250) NOT NULL`, `source_url TEXT NULL`
- `verified_on DATE NULL`, `verified_by_label VARCHAR(100) NULL`, `status VARCHAR(20) NOT NULL`

No automated tax calculation may rely on an unverified/expired rule version.

## 10. Statement catalogue and calculation outputs

### `statement_line_definitions`
- `id UUID PK`, `line_code VARCHAR(60) UNIQUE NOT NULL`, `statement_type VARCHAR(20) NOT NULL`
- `display_name VARCHAR(180) NOT NULL`, `parent_line_code VARCHAR(60) NULL`
- `line_kind VARCHAR(20) NOT NULL` (INPUT, CALCULATED, SUBTOTAL, TOTAL, MEMO)
- `normal_balance VARCHAR(10) NULL` (DEBIT, CREDIT, NEUTRAL)
- `sort_order INTEGER NOT NULL`, `is_required BOOLEAN NOT NULL DEFAULT FALSE`
- `formula_code VARCHAR(60) NULL`, `active_flag BOOLEAN NOT NULL DEFAULT TRUE`

### `entity_statement_mappings`
- `id UUID PK`, `constitution_code VARCHAR(30) NOT NULL`, `reporting_basis_code VARCHAR(40) NOT NULL`
- `statement_type VARCHAR(20) NOT NULL`, `line_code VARCHAR(60) FK statement_line_definitions.line_code NOT NULL`
- `display_label VARCHAR(180) NOT NULL`, `sort_order INTEGER NOT NULL`, `required_flag BOOLEAN NOT NULL`
- `effective_from DATE NULL`, `effective_to DATE NULL`
- unique `(constitution_code, reporting_basis_code, statement_type, line_code, effective_from)`

### `calculation_runs`
- `id UUID PK`, `project_id UUID FK NOT NULL`, `scenario_id UUID FK NOT NULL`
- `run_number INTEGER NOT NULL`, `engine_version VARCHAR(40) NOT NULL`
- `input_hash CHAR(64) NOT NULL`, `run_timestamp TIMESTAMP NOT NULL`
- `run_status VARCHAR(20) NOT NULL` (SUCCESS, FAILED, COMPLETED_WITH_WARNINGS)
- `prepared_by_label VARCHAR(100) NULL`, `summary_note TEXT NULL`
- `validation_error_count INTEGER NOT NULL DEFAULT 0`, `validation_warning_count INTEGER NOT NULL DEFAULT 0`
- unique `(scenario_id, run_number)`

### `calculation_run_snapshots`
- `id UUID PK`, `calculation_run_id UUID FK calculation_runs.id UNIQUE NOT NULL`
- `snapshot_schema_version VARCHAR(30) NOT NULL`, `input_snapshot_json TEXT NOT NULL`
- `input_hash CHAR(64) NOT NULL`, `created_at TIMESTAMP NOT NULL`
- immutable after creation. Validate hash before recalculation/reproduction.

### `statement_line_results`
- `id UUID PK`, `calculation_run_id UUID FK NOT NULL`, `period_id UUID FK NOT NULL`
- `statement_type VARCHAR(20) NOT NULL`, `line_code VARCHAR(60) NOT NULL`
- `line_label_snapshot VARCHAR(180) NOT NULL`, `amount_paise BIGINT NOT NULL`
- `formula_reference VARCHAR(60) NULL`, `trace_json TEXT NULL`
- unique `(calculation_run_id, period_id, statement_type, line_code)`

### `loan_schedule_results`
- `id UUID PK`, `calculation_run_id UUID FK NOT NULL`, `loan_facility_id UUID FK NOT NULL`
- `installment_number INTEGER NOT NULL`, `due_date DATE NOT NULL`
- `opening_balance_paise BIGINT NOT NULL`, `disbursement_paise BIGINT NOT NULL DEFAULT 0`
- `payment_paise BIGINT NOT NULL`, `interest_paise BIGINT NOT NULL`, `principal_paise BIGINT NOT NULL`
- `closing_balance_paise BIGINT NOT NULL`
- unique `(calculation_run_id, loan_facility_id, installment_number)`

### `asset_schedule_results`
- `id UUID PK`, `calculation_run_id UUID FK NOT NULL`, `asset_item_id UUID FK NOT NULL`, `period_id UUID FK NOT NULL`
- `opening_gross_paise BIGINT NOT NULL`, `additions_paise BIGINT NOT NULL`, `disposals_paise BIGINT NOT NULL`
- `closing_gross_paise BIGINT NOT NULL`, `depreciation_paise BIGINT NOT NULL`
- `accumulated_depreciation_paise BIGINT NOT NULL`, `closing_nbv_paise BIGINT NOT NULL`
- unique `(calculation_run_id, asset_item_id, period_id)`

### `ratio_results`
- `id UUID PK`, `calculation_run_id UUID FK NOT NULL`, `period_id UUID FK NULL`
- `ratio_code VARCHAR(60) NOT NULL`, `numerator_value_text VARCHAR(100) NULL`, `denominator_value_text VARCHAR(100) NULL`
- `ratio_value_text VARCHAR(100) NULL`, `unit_code VARCHAR(20) NULL`
- `method_code VARCHAR(60) NOT NULL`, `interpretation_code VARCHAR(40) NULL`, `benchmark_note TEXT NULL`

### `validation_results`
- `id UUID PK`, `calculation_run_id UUID FK NOT NULL`, `rule_code VARCHAR(60) NOT NULL`
- `severity VARCHAR(15) NOT NULL` (ERROR, WARNING, INFO)
- `scope_code VARCHAR(30) NOT NULL`, `message TEXT NOT NULL`
- `expected_value_text VARCHAR(120) NULL`, `actual_value_text VARCHAR(120) NULL`
- `resolution_status VARCHAR(20) NOT NULL DEFAULT 'OPEN'`
- `override_reason TEXT NULL`, `resolved_by_label VARCHAR(100) NULL`, `resolved_at TIMESTAMP NULL`

## 11. Knowledge, formula and report templates

### `knowledge_categories`
- `id UUID PK`, `category_code VARCHAR(50) UNIQUE NOT NULL`, `category_name VARCHAR(120) NOT NULL`, `parent_id UUID FK NULL`, `sort_order INTEGER NOT NULL`

### `knowledge_articles`
- `id UUID PK`, `category_id UUID FK NOT NULL`, `title VARCHAR(250) NOT NULL`, `body_markdown TEXT NOT NULL`
- `jurisdiction VARCHAR(80) NULL`, `effective_from DATE NULL`, `effective_to DATE NULL`
- `source_id UUID FK project_sources.id NULL`, `reviewed_on DATE NULL`, `review_status VARCHAR(20) NOT NULL`

### `formula_definitions`
- `id UUID PK`, `formula_code VARCHAR(60) UNIQUE NOT NULL`, `formula_name VARCHAR(160) NOT NULL`
- `formula_text TEXT NOT NULL`, `purpose TEXT NOT NULL`, `limitations TEXT NULL`
- `source_id UUID FK project_sources.id NULL`, `review_status VARCHAR(20) NOT NULL`

Formula text is descriptive. The executable implementation is version-controlled Python, not database-supplied code.

### `industry_templates` / `industry_template_fields`
`industry_templates`: `id UUID PK`, `industry_code VARCHAR(50) UNIQUE`, `industry_name VARCHAR(150)`, `description TEXT`, `template_version VARCHAR(30)`, `active_flag BOOLEAN`.

`industry_template_fields`: `id UUID PK`, `industry_template_id UUID FK`, `module_code VARCHAR(40)`, `field_code VARCHAR(60)`, `field_label VARCHAR(150)`, `input_type VARCHAR(25)`, `unit_code VARCHAR(30) NULL`, `required_flag BOOLEAN`, `default_value_text TEXT NULL`, `help_text TEXT NULL`, `sort_order INTEGER`.

### `report_templates` / `report_template_sections`
`report_templates`: `id UUID PK`, `template_code VARCHAR(50) UNIQUE`, `template_name VARCHAR(160)`, `output_type VARCHAR(15)` (PDF, DOCX, XLSX), `constitution_code VARCHAR(30) NULL`, `bank_name VARCHAR(160) NULL`, `template_version VARCHAR(30)`, `layout_profile_id UUID FK NULL`, `active_flag BOOLEAN`.

`report_template_sections`: `id UUID PK`, `report_template_id UUID FK`, `section_code VARCHAR(60)`, `section_title VARCHAR(180)`, `sort_order INTEGER`, `default_included BOOLEAN`, `required_flag BOOLEAN`, `renderer_key VARCHAR(60)`.

### `report_layout_profiles` / `report_layout_columns`
`report_layout_profiles`: `id UUID PK`, `layout_code VARCHAR(50) UNIQUE`, `layout_name VARCHAR(120)`, `orientation VARCHAR(15)`, `default_period_columns SMALLINT`, `show_serial_column BOOLEAN`, `show_note_reference_column BOOLEAN`, `particulars_column_width DECIMAL_TEXT`, `period_column_width DECIMAL_TEXT`, `freeze_leading_columns SMALLINT`, `active_flag BOOLEAN`.

`report_layout_columns`: `id UUID PK`, `layout_profile_id UUID FK`, `column_role VARCHAR(25)` (SERIAL, NOTE_REF, PARTICULARS, PERIOD), `column_sequence SMALLINT`, `column_label VARCHAR(50)`, `width_ratio DECIMAL_TEXT`, `is_fixed BOOLEAN`.

Default mapping: A = SERIAL; B = NOTE_REF; C = PARTICULARS; D onwards = PERIOD columns in chronological order. The number of period columns follows the selected projection horizon.

### `generated_reports`
- `id UUID PK`, `project_id UUID FK NOT NULL`, `scenario_id UUID FK NOT NULL`, `calculation_run_id UUID FK NOT NULL`
- `report_template_id UUID FK NOT NULL`, `report_version VARCHAR(30) NOT NULL`, `output_type VARCHAR(15) NOT NULL`
- `stored_relative_path TEXT NOT NULL`, `file_hash CHAR(64) NOT NULL`, `generated_at TIMESTAMP NOT NULL`
- `generation_status VARCHAR(20) NOT NULL`, `notes TEXT NULL`

### System support tables
- `schema_migrations`: managed by Alembic; do not hand-maintain.
- `app_settings`: non-sensitive application settings only; secrets must use Windows Credential Manager or an equivalent OS-protected store.
- `app_diagnostics`: optional local diagnostic events with sensitive-data redaction.

## 12. Key indexes and constraints

At minimum:
- All foreign key columns indexed where queries/joins require them.
- `projects(entity_id, project_code)` unique.
- `project_scenarios(project_id, scenario_code)` unique.
- `project_periods(project_id, period_role, period_granularity, period_sequence)` unique.
- `revenue_forecasts(revenue_stream_id, period_id)` unique.
- `expense_forecasts(scenario_id, expense_head_id, period_id)` unique.
- `loan_schedule_results(calculation_run_id, loan_facility_id, installment_number)` unique.
- `statement_line_results(calculation_run_id, period_id, statement_type, line_code)` unique.
- `calculation_runs(scenario_id, run_number)` unique.
- `generated_reports(calculation_run_id, report_template_id, report_version)` indexed.
- Index text search fields: client display name, entity legal name, project name/code and source title.

Use database check constraints where portable and repeat critical business validations in the domain service. Do not rely only on SQLite constraints if later server databases will be used.

## 13. Relationship summary

- Client 1:M Entities.
- Entity 1:M Entity Members and 1:M Projects.
- Entity 1:1 optional constitution extension table.
- Project 1:M Scenarios, Periods, Sources, Attachments and Participants.
- Scenario 1:M Cost Items, Funding Sources, Revenue Streams, Expense Forecasts, Asset Items, Loan Facilities and Working-Capital Assumptions.
- Revenue Stream 1:M Period Forecasts.
- Asset Item 1:M Additions.
- Loan Facility 1:M Disbursements, Rate Changes, Repayment Overrides and Calculation-Run Loan Schedule Results.
- Project/Scenario 1:M Calculation Runs.
- Calculation Run 1:1 Snapshot; 1:M statement, asset, loan, ratio and validation results.
- Calculation Run 1:M Generated Reports.

## 14. Design gaps the agent must explicitly review

Before ORM implementation, confirm:
1. Whether `project_periods` are project-wide and shared by scenarios (recommended) or scenario-specific.
2. Whether annual projected statements should start at financial-year start or commercial-operation date; support stub years and disclose period length.
3. Multi-rate GST within a revenue stream and composite supply handling; may require tax components rather than one rate.
4. Loan date/day-count behaviour for non-monthly and irregular first periods.
5. Partner/member capital movement tables for contributions, drawings, remuneration, interest, profit allocation and distributions.
6. Company equity movement tables for share issue, premium, reserve transfer and dividend; avoid storing these only as a single opening capital figure.
7. Cash flow classification and non-cash transactions.
8. Deferred tax support: explicitly scope out of initial release or specify separately; do not imply tax provision equals final tax liability.
9. Multi-currency and foreign-currency treatment: out of initial release unless separately approved.
10. Deletion/retention policy for entities and projects linked to approved reports.

The coding agent must return these decisions for approval before migrations are created.
