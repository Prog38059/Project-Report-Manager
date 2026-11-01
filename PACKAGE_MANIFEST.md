# Package Manifest

This package is a documentation-only developer handoff. It contains no application source code or database.

## Root files
- `AGENTS.md` — shared persistent agent instructions; tuned for Antigravity workspace discovery.
- `ANTIGRAVITY_START_HERE.md` — setup and first-task instructions.
- `README.md` — package index and source-of-truth rules.
- `GOALS.md` — product goals, scope and user-approved defaults.
- `PLANS.md` — development phases and approval gates.
- `CHANGELOG.md` — package revision history.

## Documents
- `docs/01_PRODUCT_REQUIREMENTS.md`
- `docs/02_TECHNICAL_ARCHITECTURE_BASELINE_v1.1.md`
- `docs/03_DATABASE_DATA_DICTIONARY.md`
- `docs/04_FINANCIAL_MODEL_SPECIFICATION.md`
- `docs/05_STATEMENT_CATALOGUE_AND_MAPPINGS.md`
- `docs/06_UI_UX_SPECIFICATION.md`
- `docs/07_REPORT_OUTPUT_SPECIFICATION.md`
- `docs/08_VALIDATION_AND_TEST_CATALOGUE.md`
- `docs/09_KNOWLEDGE_AND_REFERENCE_POLICY.md`
- `docs/10_SECURITY_STORAGE_BACKUP.md`
- `docs/11_OPEN_DECISIONS_REGISTER.md`

## Antigravity customizations
- `.agents/rules/` — trigger-based workspace rules.
- `.agents/skills/` — reusable procedural skills.
- `prompts/ANTIGRAVITY_PHASE_0_REVIEW.md` — planning-only first prompt.
- `prompts/ANTIGRAVITY_PHASE_1_START.md` — use only after Phase 1 approval.

## Implementation governance
- `harness/build/` — phase-specific scope and exit criteria.
- `harness/decision-log.md` — approved design decisions.
- `harness/build-log.md` — implementation log (currently no app code exists).
- `tests/financial_test_cases/` — location reserved for golden financial fixtures.
