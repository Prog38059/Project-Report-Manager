# Decision Log

Record approved decisions using this format. Do not delete superseded decisions.

## Template
- Decision ID:
- Date:
- Status: Proposed / Approved / Superseded
- Decision:
- Rationale:
- Alternatives considered:
- Approver:
- Affected documents / modules:
- Database migration required: Yes / No / Unknown
- Calculation engine version impact: Yes / No / Unknown
- Supersedes:

---

## Approved Phase 0 Decisions

### ADR-001: Financial Year Convention
- Decision ID: ADR-001
- Date: 2026-11-01
- Status: Approved
- Decision: Adopt India April–March (start month = 4) as default financial year convention, with `projects.financial_year_start_month` configurable (1–12).
- Rationale: Standard corporate and income-tax practice in India.
- Alternatives considered: Calendar year (Jan–Dec) or non-configurable April-March.
- Approver: User (Phase 0 Review Approval)
- Affected documents / modules: `app/domain/entities/project.py`, `app/infrastructure/database/models/project_model.py`
- Database migration required: Yes (Phase 1 initial migration)
- Calculation engine version impact: No
- Supersedes: None

### ADR-002: Default Projection Horizon
- Decision ID: ADR-002
- Date: 2026-11-01
- Status: Approved
- Decision: 7 annual projection years by default; configurable (3, 5, 7, 10, or custom).
- Rationale: Industry standard for bank appraisal and project financing reports.
- Alternatives considered: Fixed 5-year or 10-year projection.
- Approver: User
- Affected documents / modules: `projects.projection_year_count`, `project_periods`
- Database migration required: Yes
- Calculation engine version impact: No
- Supersedes: None

### ADR-003: Historical Financial Data Mode
- Decision ID: ADR-003
- Date: 2026-11-01
- Status: Approved
- Decision: Historical financial info is disabled and hidden by default; explicitly enabled per project when required.
- Rationale: Avoids cluttering greenfield/new project reports with irrelevant prior-year forms.
- Alternatives considered: Always showing historical inputs.
- Approver: User
- Affected documents / modules: `projects.historical_data_enabled`, UI project wizard
- Database migration required: Yes
- Calculation engine version impact: No
- Supersedes: None

### ADR-004: Horizontal Financial Statement Presentation
- Decision ID: ADR-004
- Date: 2026-11-01
- Status: Approved
- Decision: Default horizontal annual layout: Col A = Sr. No., Col B = Note/Schedule Ref., Col C = Particulars, Col D:J = Project Years 1–7. Database storage remains strictly normalized (line_code + period_id + amount_paise).
- Rationale: Matches standard CA project reporting conventions while keeping relational schema clean and dynamic.
- Alternatives considered: Separate column per year in database tables.
- Approver: User
- Affected documents / modules: Presentation grids, report renderers
- Database migration required: Yes
- Calculation engine version impact: No
- Supersedes: None

### ADR-005: Legal Entity Coverage
- Decision ID: ADR-005
- Date: 2026-11-01
- Status: Approved
- Decision: Support 6 distinct legal constitutions: Individual, Sole Proprietorship, HUF, Partnership Firm, LLP, and Private Limited Company.
- Rationale: Non-interchangeable legal structures with distinct governance, capital accounts, and tax treatments.
- Alternatives considered: Generic entity table with free-text constitution.
- Approver: User
- Affected documents / modules: `entities`, `entity_members`, constitution extension tables
- Database migration required: Yes
- Calculation engine version impact: No
- Supersedes: None

### ADR-022: Local Encryption Provider
- Decision ID: ADR-022
- Date: 2026-11-01
- Status: Approved
- Decision: Use Windows DPAPI to derive/protect a master encryption key, encrypting sensitive fields (`pan_encrypted`, `identifier_value_encrypted`) via Fernet/AES-256. Provide a fallback key-provider interface for automated test environments.
- Rationale: Secure local key management tied to Windows user credentials without hardcoding secrets in source code.
- Alternatives considered: Hardcoded salt/key or plaintext storage.
- Approver: User
- Affected documents / modules: `app/infrastructure/security/`
- Database migration required: Yes
- Calculation engine version impact: No
- Supersedes: None

### GAP-B1: Attachment Parent Relationship Flexibility
- Decision ID: GAP-B1
- Date: 2026-11-01
- Status: Approved
- Decision: Make `attachments.project_id` nullable and add `entity_id UUID FK entities.id NULL`, with a database CHECK constraint ensuring at least one parent reference exists.
- Rationale: Enables storing entity-level documents (PAN card, Partnership Deed, LLP Agreement, COI) before any project is created.
- Alternatives considered: Requiring dummy projects for entity files.
- Approver: User
- Affected documents / modules: `attachments` table schema
- Database migration required: Yes
- Calculation engine version impact: No
- Supersedes: None

### GAP-B3: Application-Wide Unique Project Code
- Decision ID: GAP-B3
- Date: 2026-11-01
- Status: Approved
- Decision: Enforce global `projects(project_code) UNIQUE`.
- Rationale: Prevents filesystem folder naming collisions under local application data directories and eliminates cross-entity project ambiguity.
- Alternatives considered: Entity-scoped unique project codes.
- Approver: User
- Affected documents / modules: `projects` schema
- Database migration required: Yes
- Calculation engine version impact: No
- Supersedes: None
