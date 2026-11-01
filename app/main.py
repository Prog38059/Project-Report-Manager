"""Application entry point."""

import sys
from PySide6.QtWidgets import QApplication

from app.config import AppConfig, setup_logging
from app.infrastructure.database.connection import DatabaseManager
from app.infrastructure.database.migration_manager import apply_migrations_to_head
from app.infrastructure.security.encryption import EncryptionService
from app.presentation.main_window import MainWindow


def main() -> int:
    config = AppConfig()
    config.ensure_directories()
    setup_logging(config)

    # Apply database migrations to ensure latest schema and seed catalogues are present
    try:
        apply_migrations_to_head(config.sqlite_url)
    except Exception as e:
        # Fallback to create_tables if running in standalone bundled context without alembic CLI
        db_temp = DatabaseManager.from_config(config)
        db_temp.create_tables()

    db_manager = DatabaseManager.from_config(config)

    # Initialize DPAPI / Fernet encryption service
    key_path = config.config_dir / "master.key"
    encryption_service = EncryptionService(key_file_path=key_path)

    app = QApplication(sys.argv)
    app.setApplicationName("Project Report Manager")
    app.setOrganizationName("CA Practice")

    window = MainWindow(config, db_manager, encryption_service)
    window.show()

    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
