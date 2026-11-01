"""Integration tests for Phase 6: Hardening, Diagnostics, Demo Project, and Packaging Readiness."""

from decimal import Decimal
from pathlib import Path
import pytest

from alembic.config import Config
from alembic import command

from app.application.services.demo_service import DemoProjectService
from app.config import AppConfig
from app.infrastructure.database.connection import DatabaseManager
from app.infrastructure.diagnostics.health import SystemHealthService
from app.infrastructure.security.encryption import EncryptionService
from scripts.verify_distribution import verify_distribution_prerequisites


@pytest.fixture
def phase6_env(test_config: AppConfig, encryption_service: EncryptionService):
    alembic_ini_path = Path(__file__).resolve().parent.parent.parent / "alembic.ini"
    alembic_cfg = Config(str(alembic_ini_path))
    alembic_cfg.set_main_option("sqlalchemy.url", test_config.sqlite_url)
    command.upgrade(alembic_cfg, "head")


def test_system_health_diagnostics(
    phase6_env,
    test_config: AppConfig,
    test_db: DatabaseManager,
    encryption_service: EncryptionService,
):
    service = SystemHealthService(test_config, test_db, encryption_service)
    report = service.run_all_checks()

    assert report.overall_status in ("HEALTHY", "DEGRADED")
    assert report.failed_count == 0
    assert report.passed_count >= 10

    # Verify specific diagnostic checks
    checks_by_name = {c.check_name: c for c in report.checks}
    assert "SQLite Database Physical Integrity" in checks_by_name
    assert checks_by_name["SQLite Database Physical Integrity"].passed is True

    assert "Cryptographic Key & Encryption Roundtrip" in checks_by_name
    assert checks_by_name["Cryptographic Key & Encryption Roundtrip"].passed is True

    assert "Excel Spreadsheet Engine (.xlsx)" in checks_by_name
    assert checks_by_name["Excel Spreadsheet Engine (.xlsx)"].passed is True

    assert "PDF Document & Vector Layout Engine (.pdf)" in checks_by_name
    assert checks_by_name["PDF Document & Vector Layout Engine (.pdf)"].passed is True


def test_demo_project_generation_and_projection(
    phase6_env,
    test_db: DatabaseManager,
    encryption_service: EncryptionService,
):
    demo_service = DemoProjectService(test_db, encryption_service)
    summary = demo_service.create_or_get_demo_project()

    assert summary.client_name == "Aerospace Dynamics Group"
    assert summary.entity_name == "Aerospace Dynamics Technologies Private Limited"
    assert summary.project_name == "Aerospace Machining & Turbine Assembly Unit"
    assert summary.total_cost_rupees == Decimal("100000000.00")
    assert summary.term_debt_rupees == Decimal("65000000.00")
    assert summary.equity_rupees == Decimal("35000000.00")
    assert summary.run_status in ("SUCCESS", "COMPLETED_WITH_WARNINGS")
    assert summary.average_dscr is not None
    assert summary.average_dscr > Decimal("1.00")
    assert summary.project_irr_pct is not None
    assert summary.project_irr_pct > Decimal("10.00")


def test_packaging_and_distribution_prerequisites():
    code = verify_distribution_prerequisites()
    assert code == 0
