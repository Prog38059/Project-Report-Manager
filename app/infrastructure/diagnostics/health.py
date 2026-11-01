"""System diagnostics and health check engine for Project Report Manager."""

from dataclasses import dataclass, field
from datetime import datetime, timezone
import importlib
import os
from pathlib import Path
import shutil
import sys
from typing import Any, Dict, List, Optional

from app.config import AppConfig
from app.infrastructure.database.connection import DatabaseManager
from app.infrastructure.database.migration_manager import (
    check_database_integrity,
    get_migration_status,
)
from app.infrastructure.security.encryption import EncryptionService


@dataclass
class DiagnosticCheckResult:
    check_name: str
    category: str  # DATABASE, STORAGE, SECURITY, REPORTING, SYSTEM
    passed: bool
    status_label: str  # PASS, WARN, FAIL
    details: str
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class SystemHealthReport:
    timestamp: datetime
    overall_status: str  # HEALTHY, DEGRADED, UNHEALTHY
    passed_count: int
    failed_count: int
    warning_count: int
    checks: List[DiagnosticCheckResult]


class SystemHealthService:
    """Orchestrates comprehensive diagnostics across persistence, security, storage, and renderers."""

    def __init__(self, config: AppConfig, db_manager: DatabaseManager, encryption_service: EncryptionService) -> None:
        self.config = config
        self.db_manager = db_manager
        self.encryption_service = encryption_service

    def run_all_checks(self) -> SystemHealthReport:
        checks: List[DiagnosticCheckResult] = []

        # 1. Database Connectivity & PRAGMA Integrity
        checks.append(self._check_database_integrity())

        # 2. Schema Migration Status
        checks.append(self._check_migration_status())

        # 3. Storage & Directory Permissions
        checks.extend(self._check_directories_and_storage())

        # 4. Security & Cryptographic Subsystem
        checks.append(self._check_encryption_subsystem())

        # 5. Reporting Engine Modules
        checks.extend(self._check_reporting_engines())

        # Aggregate counts
        passed_count = sum(1 for c in checks if c.status_label == "PASS")
        warning_count = sum(1 for c in checks if c.status_label == "WARN")
        failed_count = sum(1 for c in checks if c.status_label == "FAIL")

        if failed_count > 0:
            overall = "UNHEALTHY"
        elif warning_count > 0:
            overall = "DEGRADED"
        else:
            overall = "HEALTHY"

        return SystemHealthReport(
            timestamp=datetime.now(timezone.utc),
            overall_status=overall,
            passed_count=passed_count,
            failed_count=failed_count,
            warning_count=warning_count,
            checks=checks,
        )

    def _check_database_integrity(self) -> DiagnosticCheckResult:
        try:
            ok, msg = check_database_integrity(self.db_manager.engine)
            return DiagnosticCheckResult(
                check_name="SQLite Database Physical Integrity",
                category="DATABASE",
                passed=ok,
                status_label="PASS" if ok else "FAIL",
                details=f"SQLite PRAGMA integrity_check result: {msg}",
                metadata={"db_url": self.config.sqlite_url},
            )
        except Exception as e:
            return DiagnosticCheckResult(
                check_name="SQLite Database Physical Integrity",
                category="DATABASE",
                passed=False,
                status_label="FAIL",
                details=f"Could not connect to database: {str(e)}",
            )

    def _check_migration_status(self) -> DiagnosticCheckResult:
        try:
            status = get_migration_status(self.db_manager.engine)
            is_up = status.get("is_up_to_date", False)
            cur = status.get("current_revision")
            head = status.get("head_revision")
            return DiagnosticCheckResult(
                check_name="Alembic Schema Revision Alignment",
                category="DATABASE",
                passed=bool(is_up),
                status_label="PASS" if is_up else "WARN",
                details=f"Current: {cur} | Target Head: {head}",
                metadata=status,
            )
        except Exception as e:
            return DiagnosticCheckResult(
                check_name="Alembic Schema Revision Alignment",
                category="DATABASE",
                passed=False,
                status_label="WARN",
                details=f"Schema inspection warning: {str(e)}",
            )

    def _check_directories_and_storage(self) -> List[DiagnosticCheckResult]:
        results = []
        dirs_to_check = [
            ("Application Base Directory", self.config.base_dir),
            ("Database Storage Directory", self.config.database_dir),
            ("Projects & Attachments Directory", self.config.projects_dir),
            ("Backups Storage Directory", self.config.backups_dir),
            ("Logs Directory", self.config.logs_dir),
        ]

        for label, dir_path in dirs_to_check:
            try:
                dir_path.mkdir(parents=True, exist_ok=True)
                test_file = dir_path / f".health_check_{os.getpid()}.tmp"
                test_file.write_text("health_check_ok", encoding="utf-8")
                test_file.unlink()

                results.append(
                    DiagnosticCheckResult(
                        check_name=f"Write Access: {label}",
                        category="STORAGE",
                        passed=True,
                        status_label="PASS",
                        details=f"Directory verified writable at {dir_path}",
                    )
                )
            except Exception as e:
                results.append(
                    DiagnosticCheckResult(
                        check_name=f"Write Access: {label}",
                        category="STORAGE",
                        passed=False,
                        status_label="FAIL",
                        details=f"Write check failed at {dir_path}: {str(e)}",
                    )
                )

        # Check Free Disk Space
        try:
            usage = shutil.disk_usage(self.config.base_dir)
            free_gb = usage.free / (1024**3)
            passed = free_gb >= 0.5  # at least 500 MB
            results.append(
                DiagnosticCheckResult(
                    check_name="Disk Free Space Threshold",
                    category="STORAGE",
                    passed=passed,
                    status_label="PASS" if passed else "WARN",
                    details=f"Free storage available: {free_gb:.2f} GB (Total: {usage.total / (1024**3):.2f} GB)",
                    metadata={"free_bytes": usage.free, "total_bytes": usage.total},
                )
            )
        except Exception as e:
            results.append(
                DiagnosticCheckResult(
                    check_name="Disk Free Space Threshold",
                    category="STORAGE",
                    passed=True,
                    status_label="WARN",
                    details=f"Could not query disk space: {str(e)}",
                )
            )

        return results

    def _check_encryption_subsystem(self) -> DiagnosticCheckResult:
        try:
            test_val = "SECRET_PAN_ABCDE1234F_TEST"
            enc = self.encryption_service.encrypt(test_val)
            dec = self.encryption_service.decrypt(enc)
            passed = dec == test_val
            return DiagnosticCheckResult(
                check_name="Cryptographic Key & Encryption Roundtrip",
                category="SECURITY",
                passed=passed,
                status_label="PASS" if passed else "FAIL",
                details="AES/Fernet cipher roundtrip verified successfully." if passed else "Decryption mismatch.",
            )
        except Exception as e:
            return DiagnosticCheckResult(
                check_name="Cryptographic Key & Encryption Roundtrip",
                category="SECURITY",
                passed=False,
                status_label="FAIL",
                details=f"Encryption engine check failed: {str(e)}",
            )

    def _check_reporting_engines(self) -> List[DiagnosticCheckResult]:
        results = []
        modules = [
            ("openpyxl", "Excel Spreadsheet Engine (.xlsx)", "REPORTING"),
            ("docx", "Microsoft Word Document Engine (.docx)", "REPORTING"),
            ("reportlab", "PDF Document & Vector Layout Engine (.pdf)", "REPORTING"),
            ("PySide6", "Desktop GUI Framework & Qt Shell", "SYSTEM"),
        ]

        for mod_name, desc, cat in modules:
            try:
                mod = importlib.import_module(mod_name)
                ver = getattr(mod, "__version__", "Available")
                results.append(
                    DiagnosticCheckResult(
                        check_name=desc,
                        category=cat,
                        passed=True,
                        status_label="PASS",
                        details=f"Module '{mod_name}' loaded successfully (version {ver}).",
                        metadata={"version": str(ver)},
                    )
                )
            except Exception as e:
                results.append(
                    DiagnosticCheckResult(
                        check_name=desc,
                        category=cat,
                        passed=False,
                        status_label="FAIL",
                        details=f"Failed to import module '{mod_name}': {str(e)}",
                    )
                )

        return results


def run_diagnostics_cli() -> int:
    """CLI runner printing clean formatted diagnostics table."""
    config = AppConfig()
    db_manager = DatabaseManager.from_config(config)
    key_path = config.config_dir / "master.key"
    encryption_service = EncryptionService(key_file_path=key_path)

    service = SystemHealthService(config, db_manager, encryption_service)
    report = service.run_all_checks()

    print("\n" + "=" * 80)
    print(" PROJECT REPORT MANAGER -- SYSTEM HEALTH & DIAGNOSTIC REPORT")
    print("=" * 80)
    print(f"Timestamp (UTC) : {report.timestamp.strftime('%Y-%m-%d %H:%M:%S UTC')}")
    print(f"Overall Status  : {report.overall_status}")
    print(f"Passed Checks   : {report.passed_count}")
    print(f"Warnings        : {report.warning_count}")
    print(f"Failed Checks   : {report.failed_count}")
    print("-" * 80)
    print(f"{'STATUS':<8} | {'CATEGORY':<10} | {'CHECK NAME':<35} | {'DETAILS'}")
    print("-" * 80)

    for c in report.checks:
        status_symbol = "[PASS]" if c.status_label == "PASS" else ("[WARN]" if c.status_label == "WARN" else "[FAIL]")
        print(f"{status_symbol:<8} | {c.category:<10} | {c.check_name[:35]:<35} | {c.details[:60]}")

    print("=" * 80 + "\n")
    return 0 if report.overall_status in ("HEALTHY", "DEGRADED") else 1


if __name__ == "__main__":
    sys.exit(run_diagnostics_cli())
