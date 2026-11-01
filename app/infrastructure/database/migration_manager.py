"""Programmatic database migration manager using Alembic."""

import logging
from pathlib import Path
from typing import Dict, Optional, Tuple

from alembic import command
from alembic.config import Config
from alembic.script import ScriptDirectory
from alembic.runtime.migration import MigrationContext
from sqlalchemy import text
from sqlalchemy.engine import Engine

logger = logging.getLogger(__name__)


def get_alembic_config(db_url: str, alembic_ini_path: Optional[Path] = None) -> Config:
    """Creates an Alembic Config instance configured for the specified database URL."""
    if alembic_ini_path is None:
        # Default to root alembic.ini
        alembic_ini_path = Path(__file__).resolve().parent.parent.parent.parent / "alembic.ini"

    if not alembic_ini_path.exists():
        raise FileNotFoundError(f"Alembic configuration file not found at {alembic_ini_path}")

    config = Config(str(alembic_ini_path))
    config.set_main_option("sqlalchemy.url", db_url)
    return config


def apply_migrations_to_head(db_url: str, alembic_ini_path: Optional[Path] = None) -> None:
    """Applies all pending Alembic migrations up to head revision."""
    config = get_alembic_config(db_url, alembic_ini_path)
    logger.info(f"Applying database migrations to head on {db_url}...")
    command.upgrade(config, "head")
    logger.info("Database migrations successfully applied to head.")


def get_migration_status(engine: Engine, alembic_ini_path: Optional[Path] = None) -> Dict[str, Optional[str]]:
    """Inspects the database and Alembic scripts to determine current revision and head revision."""
    db_url = str(engine.url)
    config = get_alembic_config(db_url, alembic_ini_path)
    script_dir = ScriptDirectory.from_config(config)

    head_rev = script_dir.get_current_head()

    with engine.connect() as conn:
        context = MigrationContext.configure(conn)
        current_rev = context.get_current_revision()

    return {
        "current_revision": current_rev,
        "head_revision": head_rev,
        "is_up_to_date": current_rev == head_rev,
    }


def check_database_integrity(engine: Engine) -> Tuple[bool, str]:
    """Runs SQLite PRAGMA integrity_check to verify physical database health."""
    if "sqlite" not in str(engine.url):
        return True, "Database is not SQLite; integrity check skipped."

    try:
        with engine.connect() as conn:
            result = conn.execute(text("PRAGMA integrity_check;")).scalar()
            if result == "ok":
                return True, "OK"
            return False, f"Database corruption detected: {result}"
    except Exception as e:
        return False, f"Integrity check failed with exception: {str(e)}"
