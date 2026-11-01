# Project Report Manager — Developer Handoff Pack v1.0

**Primary coding environment:** Google Antigravity  
**Compatible secondary environment:** Codex (shared root `AGENTS.md` instructions)  
**Status:** Design/specification handoff; implementation has not been approved or started.  
**Target:** Windows desktop, single-computer first release, designed for future LAN expansion.  
**Default reporting:** Seven annual projection years, historical data disabled by default, horizontal year-wise financial statements.

## Start here for Antigravity

1. Read `ANTIGRAVITY_START_HERE.md`.
2. Read root `AGENTS.md`, `GOALS.md` and `PLANS.md`.
3. Read every numbered document in `docs/`.
4. Review `.agents/rules/` and `.agents/skills/`.
5. Give Antigravity `prompts/ANTIGRAVITY_PHASE_0_REVIEW.md` as the first task.
6. Do not allow code, dependency installation, database creation or migrations until the user approves Phase 1.

## Documentation index

1. `docs/01_PRODUCT_REQUIREMENTS.md` — functional scope and supported constitu­tions/industries.
2. `docs/02_TECHNICAL_ARCHITECTURE_BASELINE_v1.1.md` — reviewed architecture and original schema baseline.
3. `docs/03_DATABASE_DATA_DICTIONARY.md` — implementation-level database field definitions.
4. `docs/04_FINANCIAL_MODEL_SPECIFICATION.md` — calculation sequence and financial formula contracts.
5. `docs/05_STATEMENT_CATALOGUE_AND_MAPPINGS.md` — stable statement lines and entity-aware presentation.
6. `docs/06_UI_UX_SPECIFICATION.md` — screen and interaction behaviour.
7. `docs/07_REPORT_OUTPUT_SPECIFICATION.md` — PDF, Word and Excel output contracts.
8. `docs/08_VALIDATION_AND_TEST_CATALOGUE.md` — financial invariants, tests and acceptance criteria.
9. `docs/09_KNOWLEDGE_AND_REFERENCE_POLICY.md` — knowledge base and statutory-source governance.
10. `docs/10_SECURITY_STORAGE_BACKUP.md` — local storage, privacy, backup and restore.
11. `docs/11_OPEN_DECISIONS_REGISTER.md` — decisions requiring user/professional approval.

## Antigravity customizations

- `.agents/rules/*.md` — trigger-based persistent project rules.
- `.agents/skills/*/SKILL.md` — reusable procedural playbooks.
- `AGENTS.md` — concise always-active project rules.

## Source-of-truth rules

- User-approved requirements and the documents in `docs/` govern the product.
- v1.1 architecture is retained for traceability; implementation specifications add detail and do not silently override approved decisions.
- If documents conflict, stop and report the conflict.
- Open decisions remain open until approved.
- Tax rates, accounting policies, lender benchmarks and statutory interpretations must be configurable, sourced and versioned.
- Never imply that generated projections are audited or statutory financial statements.

## Implementation governance

- Follow `PLANS.md` and the phase documents in `harness/build/`.
- Implement one explicitly approved phase at a time.
- Update `harness/build-log.md` and `harness/decision-log.md`.
- Preserve reproducibility of calculation runs and generated reports.
