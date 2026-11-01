# Antigravity Prompt — Phase 1 Start (Use Only After Explicit Approval)

The user has explicitly approved Phase 1. Implement only the Phase 1 scope in `PLANS.md` and the approved Phase 1 plan. Before changing files, restate the scope and file plan.

Requirements:
- Follow `AGENTS.md` and matching `.agents/rules/` rules.
- Use the `phase-implementation` skill.
- Do not implement financial calculations beyond the approved foundation interfaces.
- Add SQLAlchemy models and Alembic migrations only for the approved Phase 1 entities/tables.
- Keep SQLite local to the Windows machine.
- Implement repositories/services and UI CRUD through the specified boundaries.
- Include tests for create/read/update/archive, migration upgrade, backup and restore.
- Do not begin Phase 2 without a separate user approval.

At completion, report all modified files, migrations, tests and exact results, known limitations, rollback instructions, and the approval needed for Phase 2.
