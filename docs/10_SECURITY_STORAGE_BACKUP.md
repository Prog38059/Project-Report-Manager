# Security, Local Storage, Backup and Recovery Specification

## 1. Initial single-computer deployment

- Install application binaries under the normal Windows application installation directory.
- Store mutable application data under a user-writable local application-data directory, e.g. `%LOCALAPPDATA%/ProjectReportManager/`.
- Store the SQLite database, logs, configuration and managed attachments in defined subdirectories. The exact path is configurable, but the live database must remain on a local disk for the initial release.
- Store exported reports in a user-selected output directory; do not silently mix generated outputs with the live database or attachments.
- Do not put the live SQLite database on a mapped drive, NAS share, OneDrive-synchronised folder or ordinary LAN folder.

## 2. Data classification

Classify data at minimum as:
- Ordinary project information.
- Confidential business/financial information.
- Personal data (including PAN and contact details).
- Authentication secrets (if any are ever introduced).

Collect only fields necessary for the selected project/report. Mask sensitive identifiers in ordinary screens and logs. Do not store bank portal passwords, DSC credentials or unrelated credentials in this application.

## 3. Protection requirements

- Use Windows user-profile access controls for the local data directory.
- Encrypt especially sensitive values and secrets using a documented key-management approach appropriate to Windows; do not invent or hardcode an encryption key in source code.
- Keep encryption keys separate from the SQLite database and backups. Evaluate Windows DPAPI or an approved OS-backed secret store before implementation.
- Never log plaintext PAN, bank account numbers, contact details beyond operational necessity, or authentication secrets.
- Sanitize filenames and prevent path traversal when adding attachments or generating outputs.
- Validate file type, size and extension; do not execute attachments.
- Use parameterised SQL/ORM operations; do not construct SQL from untrusted input.
- Keep application dependencies pinned and review licence/security implications before packaging.

## 4. Attachment storage

- Store file bytes in project-managed folders, not as ordinary large database blobs.
- Use opaque generated storage names or safe deterministic IDs; preserve original filename as metadata.
- Record MIME type, file size, upload date, SHA-256 hash, project association and source association.
- Prevent cross-project path references and path traversal.
- If an attachment is replaced, preserve historical source references for calculation runs that depended on the prior document where required.

## 5. Backup requirements

The backup operation must include:
- SQLite database in a transactionally consistent state (use SQLite backup API or another supported consistent backup method; do not blindly copy a live database file while writes are active).
- All managed attachments referenced by the backed-up database.
- Relevant configuration and template versions needed to interpret prior reports, excluding secrets that should be re-provisioned securely.
- A manifest listing backup creation date, application/schema version, included projects/files and checksums.

Backups should be versioned and stored in a user-selected location. Offer scheduled reminder or manual backup; do not claim a backup succeeded until integrity checks pass.

## 6. Restore requirements

- Restore to a staging location first.
- Validate database integrity, schema version and migrations.
- Validate attachment presence and hashes.
- Show the user the restore summary and target path before replacing live data.
- Preserve or rename existing live data before replacement; provide a rollback path.
- Test restore in automated tests and as part of release acceptance.

## 7. Audit and retention

- Record material changes to project assumptions, funding, tax settings, loan settings, report template, and approval/override events.
- Audit records must identify timestamp, entity/project, record type/ID, event and reason where applicable.
- Avoid retaining unnecessary sensitive before/after values in audit JSON; redact or mask sensitive attributes.
- Prefer archive/inactive status over destructive deletion for records referenced by calculation runs or reports.

## 8. Future LAN deployment boundary

The future multi-user version must not share a SQLite file over SMB or a network share. Use a central database such as PostgreSQL or SQL Server behind an authenticated application service/API. The service is responsible for validation, transactional persistence, access control, file storage and concurrency. Desktop clients should not connect directly to the server database with embedded credentials.

Multi-user deployment requires separate approval and a design covering identity, roles/permissions, project-level access, concurrency control, audit, central backup, restore, deployment and network security.
