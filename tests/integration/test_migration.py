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
    conn.close()

    assert "clients" in tables
    assert "entities" in tables
    assert "projects" in tables
    assert "attachments" in tables
    assert "huf_details" in tables
    assert "company_details" in tables

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
