# Implementation Plan and Phase Gates

## Required workflow
The coding agent must not jump directly into implementation. First perform the planning-only review in the selected prompt. After the user approves the review, build one phase at a time.

| Phase | Scope | Required exit evidence | Approval gate |
|---|---|---|---|
| 0 — Specification review | Review all documents; identify conflicts, missing decisions and implementation risks; refine plan only | Written review, risk list, questions, proposed file plan; no code changes | User approves final design and Phase 1 |
| 1 — Foundation | Repo setup, app shell, configuration, SQLite, SQLAlchemy, Alembic, repositories, client/entity/project CRUD, backup | Tests for create/read/update/archive, migration, backup and restore; launchable shell | User approves Phase 2 |
| 2 — Project inputs | Project profile, periods, optional historical mode, project costs, funding, sources/attachments, revenue and expenses, industry templates | Input validation tests, import/export sample, seven-year grid, historical hidden/enable behaviour | User approves Phase 3 |
| 3 — Financial engine | Assets, depreciation, loans, working capital, tax estimates, P&L, Balance Sheet, Cash Flow | Golden test fixtures, statement reconciliation, reproducible snapshots | User approves Phase 4 |
| 4 — Appraisal | Ratios, DSCR variants, break-even, payback, NPV, IRR, scenario/sensitivity, validation dashboard | Independently verified ratio and appraisal fixtures | User approves Phase 5 |
| 5 — Reporting | Shared report-data model, PDF, Word, Excel, horizontal year-wise layouts, charts, annexures and templates | Output comparison tests proving all renderers agree with selected calculation run | User approves Phase 6 |
| 6 — Hardening and deployment | UI polish, performance, accessibility, security, packaging, installer, diagnostics, backup/restore and sample projects | Clean-machine installer/restore tests, user acceptance checklist, documentation | User approves release |
| 7 — Future LAN version | Central API, server database, user authentication, concurrency, file service and migrations | Multi-client concurrency, permission and recovery tests | Separate scope approval required |

## Phase-plan requirements
Each phase plan must state:
- Objective and in-scope features.
- Explicit out-of-scope features.
- Prerequisites and decisions required.
- Data model changes and migrations.
- UI changes.
- Financial/technical logic to be implemented.
- Test cases and acceptance criteria.
- Risks and rollback approach.
- Files expected to change.
- Evidence to report to the user.

## Change control
A requirement change must be recorded in `harness/decision-log.md` with date, decision, rationale, alternatives, affected documents, and whether existing data/migrations are affected. Do not overwrite earlier decisions; mark them superseded.
