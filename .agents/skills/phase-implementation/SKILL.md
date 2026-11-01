---
name: phase-implementation
description: Use when implementing one explicitly approved Project Report Manager development phase, following its scope, evidence and approval gate.
---

# Phase Implementation Procedure

1. Read `AGENTS.md`, `PLANS.md`, the relevant phase plan and applicable docs/rules.
2. Confirm that the user has explicitly approved this phase. If not, do not implement.
3. State the phase objective, in-scope work, exclusions, intended files and tests before editing.
4. Inspect the current repository and current phase status. Do not assume a clean or empty repository.
5. Propose any necessary schema or accounting decisions before coding. Record approved decisions in `harness/decision-log.md`.
6. Implement only the approved phase in small vertical slices.
7. Add/update automated tests and documentation with each material feature.
8. Run the required tests, formatting, lint and type checks that are available. Report exact commands and actual results.
9. Update `harness/build-log.md` with date, phase, changed files, migrations, tests, known issues and next approval gate.
10. Stop after the phase exit criteria are met. Do not begin the next phase without explicit user approval.

## Completion report

Include objective achieved, files changed, database changes, commands run, test outcomes, screenshots/artifacts where useful, limitations, rollback notes and the next decision required.
