"""Application entry point."""

import sys
from PySide6.QtWidgets import QApplication

from app.config import AppConfig, setup_logging
from app.infrastructure.database.connection import DatabaseManager
from app.infrastructure.security.encryption import EncryptionService
from app.presentation.main_window import MainWindow


def main() -> int:
    config = AppConfig()
    config.ensure_directories()
    setup_logging(config)

    # Initialize persistence and ensure schema tables exist
    db_manager = DatabaseManager.from_config(config)
    db_manager.create_tables()

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
