"""Backup and restore service implementing transactional SQLite backup and hash verification."""

from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import sqlite3
from typing import Dict, Any, Optional
import uuid
import zipfile

from app.common.exceptions import BackupError
from app.config import AppConfig
from app.infrastructure.database.connection import DatabaseManager
from app.infrastructure.database.models.audit_model import BackupHistoryModel


def _compute_sha256(file_path: Path) -> str:
    hasher = hashlib.sha256()
    with open(file_path, "rb") as f:
        while chunk := f.read(65536):
            hasher.update(chunk)
    return hasher.hexdigest()


class BackupService:
    """Orchestrates safe backups and verified restores."""

    def __init__(self, config: AppConfig, db_manager: DatabaseManager) -> None:
        self.config = config
        self.db_manager = db_manager

    def create_backup(self, destination_dir: Optional[Path] = None, notes: Optional[str] = None) -> Path:
        """Creates a transactionally consistent backup zip containing DB, attachments, and manifest."""
        dest_folder = Path(destination_dir).resolve() if destination_dir else self.config.backups_dir
        dest_folder.mkdir(parents=True, exist_ok=True)

        timestamp_str = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        backup_zip_path = dest_folder / f"backup_{timestamp_str}.zip"
        staging_dir = dest_folder / f"staging_{timestamp_str}"
        staging_dir.mkdir(parents=True, exist_ok=True)

        try:
            # 1. Use SQLite Online Backup API for transactional consistency
            staging_db = staging_dir / "database.db"
            if self.config.db_path.exists():
                src_conn = sqlite3.connect(str(self.config.db_path))
                dst_conn = sqlite3.connect(str(staging_db))
                with dst_conn:
                    src_conn.backup(dst_conn)
                dst_conn.close()
                src_conn.close()
            else:
                # In-memory or empty
                staging_db.touch()

            # 2. Prepare manifest
            manifest: Dict[str, Any] = {
                "application": "Project Report Manager",
                "version": "1.0.0",
                "schema_version": "0001_phase1_foundation",
                "timestamp_utc": datetime.now(timezone.utc).isoformat(),
                "notes": notes,
                "files": {},
            }

            db_hash = _compute_sha256(staging_db)
            manifest["files"]["database.db"] = {
                "sha256": db_hash,
                "size_bytes": staging_db.stat().st_size,
            }

            # 3. Add managed attachments to staging
            staging_attachments = staging_dir / "attachments"
            staging_attachments.mkdir(parents=True, exist_ok=True)

            for root_folder in [self.config.projects_dir, self.config.base_dir / "entities"]:
                if root_folder.exists():
                    for f in root_folder.rglob("*"):
                        if f.is_file() and "attachments" in f.parts:
                            rel_to_base = f.relative_to(self.config.base_dir).as_posix()
                            dest_f = staging_dir / rel_to_base
                            dest_f.parent.mkdir(parents=True, exist_ok=True)
                            dest_f.write_bytes(f.read_bytes())
                            manifest["files"][rel_to_base] = {
                                "sha256": _compute_sha256(dest_f),
                                "size_bytes": dest_f.stat().st_size,
                            }

            # Write manifest
            manifest_path = staging_dir / "manifest.json"
            manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")

            # 4. Create compressed zip archive
            with zipfile.ZipFile(backup_zip_path, "w", zipfile.ZIP_DEFLATED) as zipf:
                for f in staging_dir.rglob("*"):
                    if f.is_file():
                        rel = f.relative_to(staging_dir)
                        zipf.write(f, arcname=rel)

            # Record in backup history
            zip_hash = _compute_sha256(backup_zip_path)
            with self.db_manager.session_scope() as session:
                record = BackupHistoryModel(
                    backup_file_path=str(backup_zip_path),
                    backup_timestamp=datetime.now(timezone.utc),
                    file_size_bytes=backup_zip_path.stat().st_size,
                    sha256_hash=zip_hash,
                    status="SUCCESS",
                    notes=notes,
                )
                session.add(record)

            return backup_zip_path

        finally:
            import shutil
            if staging_dir.exists():
                shutil.rmtree(staging_dir, ignore_errors=True)

    def verify_and_restore(self, backup_zip_path: Path, target_restore_dir: Path) -> Dict[str, Any]:
        """Restores a backup zip to target directory after staging and verifying all file checksums."""
        backup_zip_path = Path(backup_zip_path).resolve()
        target_restore_dir = Path(target_restore_dir).resolve()

        if not backup_zip_path.exists():
            raise BackupError(f"Backup zip not found at '{backup_zip_path}'")

        target_restore_dir.mkdir(parents=True, exist_ok=True)
        staging_dir = target_restore_dir / f"restore_staging_{uuid.uuid4().hex[:8]}"
        staging_dir.mkdir(parents=True, exist_ok=True)

        try:
            # 1. Unzip to staging
            with zipfile.ZipFile(backup_zip_path, "r") as zipf:
                zipf.extractall(staging_dir)

            manifest_path = staging_dir / "manifest.json"
            if not manifest_path.exists():
                raise BackupError("Corrupt backup: 'manifest.json' missing from archive.")

            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            files_dict = manifest.get("files", {})

            # 2. Verify all file hashes in manifest
            for rel_name, meta in files_dict.items():
                staged_file = staging_dir / rel_name
                if not staged_file.exists():
                    raise BackupError(f"Manifest file '{rel_name}' missing from unpacked backup.")
                actual_hash = _compute_sha256(staged_file)
                if actual_hash.lower() != meta["sha256"].lower():
                    raise BackupError(f"Checksum mismatch for '{rel_name}'. Expected {meta['sha256']}, got {actual_hash}")

            # 3. Verify SQLite DB integrity
            staged_db = staging_dir / "database.db"
            if staged_db.exists() and staged_db.stat().st_size > 0:
                conn = sqlite3.connect(str(staged_db))
                cursor = conn.cursor()
                cursor.execute("PRAGMA integrity_check;")
                result = cursor.fetchone()
                conn.close()
                if not result or result[0] != "ok":
                    raise BackupError(f"SQLite database integrity check failed: {result}")

            # 4. Copy verified files from staging to target directory
            import shutil
            # Copy database
            target_db_dir = target_restore_dir / "database"
            target_db_dir.mkdir(parents=True, exist_ok=True)
            if staged_db.exists():
                shutil.copy2(staged_db, target_db_dir / "project_report_manager.db")

            # Copy attachments
            for rel_name in files_dict.keys():
                if rel_name != "database.db":
                    src_f = staging_dir / rel_name
                    dst_f = target_restore_dir / rel_name
                    dst_f.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(src_f, dst_f)

            return {
                "success": True,
                "verified_files_count": len(files_dict),
                "timestamp_utc": manifest.get("timestamp_utc"),
                "schema_version": manifest.get("schema_version"),
            }

        finally:
            import shutil
            if staging_dir.exists():
                shutil.rmtree(staging_dir, ignore_errors=True)
