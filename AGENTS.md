# Project Report Manager — Persistent Agent Instructions

## Mission
Build a professional, reliable Windows desktop application for preparing project reports and integrated financial projections across supported Indian legal constitutions and business models. The full specification is in `docs/`; read it before implementation.

## Working mode and approval gates
1. Start with the planning-only review requested in `prompts/`.
2. Do not write application code, create database tables, install dependencies, change project files or run migrations during a planning-only task.
3. Do not begin a development phase unless the user explicitly approves that phase.
4. Implement one approved phase at a time. Before moving to the next phase, report changed files, tests run, results, unresolved issues and the next approval needed.
5. Do not silently expand scope or make unresolved accounting, tax, legal, lender or presentation decisions.
6. If requirements conflict or are materially ambiguous, stop and present the conflict, evidence and options. Do not guess.

## Architecture rules
- Use a modular monolith for the initial desktop application.
- Keep the GUI, application services, domain/financial engines, persistence, and reporting renderers separate.
- Financial/domain modules must not import PySide6, SQLAlchemy ORM models or PDF/Word/Excel rendering packages.
- GUI screens collect and display data; they do not implement accounting, tax, loan, depreciation or ratio formulas.
- Use service and repository boundaries. Avoid giant windows, giant modules and a single-file application.
- SQLite is local-only for the initial single-user release. Never place the live SQLite database on a shared LAN folder. Future LAN deployment requires a central API/service and server database.

## Financial integrity — non-negotiable
- Use `Decimal` for financial calculations. Never use Python binary `float` for money or financial rates.
- Persist monetary values in integer paise (or an explicitly approved exact-money representation); persist non-monetary decimals as exact decimal strings or an explicitly scaled integer.
- Define and document rounding at each calculation boundary. Avoid repeated rounding during intermediate calculations.
- Never use an unexplained suspense, balancing or plug figure to force the balance sheet to balance.
- Never treat loan principal as a Profit & Loss expense.
- Separate book depreciation from income-tax depreciation.
- Separate gross customer collections, output GST, net revenue and recoverable input GST.
- Do not assume every input GST amount is eligible for credit.
- Do not hardcode tax rates, statutory depreciation rates, lender DSCR thresholds or universal industry benchmarks without effective dates, jurisdiction, entity applicability and an authoritative source record.
- Make lender-specific DSCR definitions and appraisal assumptions configurable and identify the selected method in outputs.
- Do not execute arbitrary formula text stored in the database. Formula definitions are explanatory metadata; calculation logic is tested Python code.
- If a required figure is unknown, expose it as a missing input, assumption or documented exclusion. Do not invent it.

## Projection and presentation defaults
- Seven annual projection years by default; permit configured 3, 5, 7, 10 or custom horizons within an approved limit.
- Historical financial information is disabled and hidden by default. Enable it explicitly per project when required.
- Main annual financial statements use horizontal year-wise presentation: Column A = Sr. No.; Column B = Note/Schedule reference; Column C = Particulars; Columns D:J = Project Years 1–7. If the projection horizon differs, extend or reduce period columns while retaining the first three descriptive columns.
- Database storage remains normalised: one result per line item and period. Pivot only in the presentation/reporting layer.
- Annual statements are the default; monthly loan schedules are included. Monthly/quarterly operating projections are optional.

## Calculation runs and reports
- Every calculation run must preserve an immutable input snapshot, input hash, engine version, timestamps and validation outcomes.
- A new calculation creates a new run; do not overwrite prior run outputs.
- PDF, Word and Excel renderers consume one common report-data object for a selected calculation run. Renderers must not recalculate figures.
- Every generated report must link to project, scenario, calculation run, report template/version and file hash.
- Do not mark a project report approved while material validation errors remain unresolved, unless an explicit documented override is permitted by the specification and user workflow.

## Code quality and testing
- Add type hints to public functions and domain data structures.
- Use small, cohesive modules and meaningful names.
- Add unit tests for every financial formula and integration tests for end-to-end statement flows.
- Add migrations for every schema change. Never mutate production databases with ad-hoc startup SQL.
- Run formatting, linting, type checks and tests available for the phase. Report commands and outcomes accurately.
- Tests must include expected-value fixtures independently checked outside the implementation under test.
- Maintain `harness/build-log.md` after approved implementation work and phase context files under `harness/context/`.

## Data protection and operational safeguards
- Do not log passwords, full PANs, bank account numbers or other unnecessary sensitive data.
- Store attachments in managed project folders and record hashes/metadata in the database.
- Use safe backup and restore processes. Verify restore, not merely backup creation.
- Avoid irreversible deletion. Prefer archive/inactive status and restrictive foreign-key behaviour for records used by approved calculation runs.
- Do not send project data to external services or AI APIs unless the user has explicitly enabled and approved that integration.

## Deliverable discipline
- Before modifying files, state the phase scope and intended changes.
- Do not claim a test passed unless it was actually run.
- Do not create fake sample values in real client projects. Clearly label sample/demo data.
- Do not change approved financial methodologies without proposing the change and obtaining user approval.

## Antigravity workspace customizations
- This repository is primarily intended to be opened as a Google Antigravity workspace.
- Keep `.agents/rules/*.md` and `.agents/skills/<name>/SKILL.md` at their documented paths; their trigger metadata is intentional.
- Use the relevant skill for phase implementation, financial calculation changes and output verification.
- The root `AGENTS.md` is the shared always-active instruction source. Do not create a second contradictory `GEMINI.md` instruction set.
- For the first Antigravity task, use `prompts/ANTIGRAVITY_PHASE_0_REVIEW.md` and stop after the planning-only review.
