"""Integration test for Alembic migrations cycle."""

from pathlib import Path
from alembic.config import Config
from alembic import command
import pytest

from app.config import AppConfig


def test_alembic_upgrade_and_downgrade(test_config: AppConfig):
    # Set up alembic config object pointing to alembic.ini and the test sqlite url
    alembic_ini_path = Path(__file__).resolve().parent.parent.parent / "alembic.ini"
    alembic_cfg = Config(str(alembic_ini_path))
    alembic_cfg.set_main_option("sqlalchemy.url", test_config.sqlite_url)

    # 1. Upgrade from empty to head
    command.upgrade(alembic_cfg, "head")

    # Verify tables were created
    import sqlite3
    conn = sqlite3.connect(str(test_config.db_path))
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = {row[0] for row in cursor.fetchall()}

    assert "clients" in tables
    assert "entities" in tables
    assert "projects" in tables
    assert "attachments" in tables
    assert "huf_details" in tables
    assert "company_details" in tables
    assert "project_cost_heads" in tables
    assert "project_cost_items" in tables
    assert "funding_heads" in tables
    assert "funding_sources" in tables
    assert "revenue_methods" in tables
    assert "revenue_streams" in tables
    assert "revenue_forecasts" in tables
    assert "expense_heads" in tables
    assert "expense_forecasts" in tables
    assert "industry_templates" in tables
    assert "industry_template_fields" in tables
    assert "historical_statement_lines" in tables
    assert "statement_line_definitions" in tables
    assert "entity_statement_mappings" in tables
    assert "calculation_runs" in tables
    assert "calculation_run_snapshots" in tables
    assert "statement_line_results" in tables
    assert "loan_schedule_results" in tables
    assert "asset_schedule_results" in tables
    assert "ratio_results" in tables
    assert "validation_results" in tables
    assert "report_templates" in tables
    assert "report_template_sections" in tables
    assert "generated_reports" in tables

    # Verify seed data
    cursor.execute("SELECT COUNT(*) FROM industry_templates;")
    assert cursor.fetchone()[0] == 10
    cursor.execute("SELECT COUNT(*) FROM revenue_methods;")
    assert cursor.fetchone()[0] == 9
    cursor.execute("SELECT COUNT(*) FROM project_cost_heads;")
    assert cursor.fetchone()[0] >= 10
    cursor.execute("SELECT COUNT(*) FROM funding_heads;")
    assert cursor.fetchone()[0] >= 6
    cursor.execute("SELECT COUNT(*) FROM expense_heads;")
    assert cursor.fetchone()[0] >= 10
    cursor.execute("SELECT COUNT(*) FROM statement_line_definitions;")
    assert cursor.fetchone()[0] >= 30
    cursor.execute("SELECT COUNT(*) FROM report_templates;")
    assert cursor.fetchone()[0] == 3
    cursor.execute("SELECT COUNT(*) FROM report_template_sections;")
    assert cursor.fetchone()[0] == 9
    conn.close()

    # 2. Downgrade to base
    command.downgrade(alembic_cfg, "base")

    conn = sqlite3.connect(str(test_config.db_path))
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables_after_down = {row[0] for row in cursor.fetchall()}
    conn.close()

    assert "clients" not in tables_after_down
    assert "entities" not in tables_after_down

    # 3. Upgrade back to head
    command.upgrade(alembic_cfg, "head")
