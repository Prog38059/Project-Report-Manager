---
trigger: glob
globs: "app/infrastructure/database/**/*.py, app/infrastructure/repositories/**/*.py, migrations/**/*.py, **/*schema*.py, **/*model*.py"
description: "Apply when modifying SQLAlchemy models, database schema, repositories, data migrations or calculation snapshot storage."
---

# Database and Migration Rules

- Read `docs/03_DATABASE_DATA_DICTIONARY.md`, `docs/10_SECURITY_STORAGE_BACKUP.md` and `docs/11_OPEN_DECISIONS_REGISTER.md` before schema changes.
- Use SQLAlchemy 2.x typed mappings and repository/service boundaries.
- Every schema change requires an Alembic migration with upgrade and downgrade behaviour reviewed.
- Never mutate the production schema through ad-hoc startup SQL or silently recreate a database.
- Preserve records referenced by calculation runs or generated reports; use restrictive deletion or archive workflows.
- Store money as integer paise, rates/quantities as exact decimal representations, dates as dates and timestamps in UTC.
- Store versioned calculation input snapshots separately from mutable project inputs. A hash alone is not a reproducible snapshot.
- SQLite is local-only in the initial release. Do not put a live SQLite database on a LAN share or cloud-sync folder.
- Add constraints and indexes based on access patterns and data integrity, not indiscriminately.
- Never store plaintext secrets or unnecessary full sensitive identifiers in logs or audit JSON.
- Add migration tests against a fresh database and the previous supported schema version.
