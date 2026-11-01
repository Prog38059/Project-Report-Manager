"""Verifies that all prerequisites, entry points, and bundled assets for desktop distribution are present."""

from pathlib import Path
import sys

def verify_distribution_prerequisites() -> int:
    root = Path(__file__).resolve().parent.parent
    errors = []

    # 1. Entry point check
    entry_point = root / "app" / "main.py"
    if not entry_point.exists():
        errors.append(f"Application entry point missing: {entry_point}")

    # 2. PyInstaller spec check
    spec_file = root / "project_report_manager.spec"
    if not spec_file.exists():
        errors.append(f"PyInstaller spec file missing: {spec_file}")

    # 3. Alembic config and migrations check
    alembic_ini = root / "alembic.ini"
    if not alembic_ini.exists():
        errors.append(f"Alembic configuration missing: {alembic_ini}")

    versions_dir = root / "migrations" / "versions"
    if not versions_dir.exists():
        errors.append(f"Migration versions directory missing: {versions_dir}")
    else:
        migrations = list(versions_dir.glob("*.py"))
        if len(migrations) < 5:
            errors.append(f"Expected at least 5 migration scripts, found {len(migrations)}")

    # 4. Mandatory modules check
    mandatory_modules = [
        "PySide6",
        "sqlalchemy",
        "alembic",
        "openpyxl",
        "docx",
        "reportlab",
        "cryptography",
    ]
    for mod in mandatory_modules:
        try:
            __import__(mod)
        except ImportError as e:
            errors.append(f"Required package '{mod}' cannot be imported: {str(e)}")

    if errors:
        print("[FAIL] Distribution verification failed with errors:")
        for err in errors:
            print(f"  - {err}")
        return 1

    print("[PASS] All distribution packaging prerequisites and asset files verified successfully.")
    return 0

if __name__ == "__main__":
    sys.exit(verify_distribution_prerequisites())
