# Antigravity Prompt — Phase 0: Planning-Only Review

Use this prompt in Antigravity after opening the complete `Project_Report_Manager_Antigravity_Handoff_v1.0` folder as the workspace.

---

You are the technical architect and senior financial-software reviewer for Project Report Manager. Read the repository instructions in `AGENTS.md`, then read `GOALS.md`, `PLANS.md`, every file in `docs/`, and the Antigravity-specific rules and skills under `.agents/`.

## Task: Review and prepare the implementation plan only

This is a planning-only task. Do not write or modify application code, create ORM models, create database tables, run migrations, install packages, execute project-generation commands or create a database.

Review the complete specification for:
1. Architecture completeness and dependency boundaries.
2. Data dictionary completeness, data types, constraints, relationships, indexes and referential integrity.
3. Entity-specific records and financial statement mappings.
4. Seven-year default periods, optional historical mode and dynamic horizontal financial statement layout.
5. Financial calculation methodology, formula definitions, rounding and timing conventions.
6. Loan, depreciation, working capital, GST and tax requirements.
7. Calculation-run snapshots, reproducibility and report traceability.
8. UI workflows, grid behaviour, keyboard input and validation UX.
9. PDF, Word and Excel output requirements.
10. Security, local storage, attachment management, backup and restore.
11. Automated tests, golden fixtures and phase acceptance evidence.
12. Any contradictions, missing information or assumptions that should not be made.

## Required response

Prepare a review artifact containing:
- Summary of what is ready.
- Blocking gaps.
- Non-blocking recommendations.
- Conflicts between documents, if any.
- Open decisions referenced by ADR ID.
- Proposed database/architecture changes, with rationale.
- Phase 1 implementation plan and file-level change plan.
- Proposed test commands and acceptance evidence.

For each issue, cite the exact document and section. Separate user-approved requirements from agent recommendations. Do not rewrite specifications or make decisions on the user's behalf.

## Stop condition

After presenting the review and Phase 1 plan, stop. Wait for the user to approve the design review and Phase 1. Do not start implementation automatically.
