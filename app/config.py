"""Application configuration and path management.

Strictly enforces local disk storage and prevents storing live SQLite databases
or application directories on network shares (UNC paths) or cloud-synchronised LAN shares.
"""

from __future__ import annotations

import os
import sys
import logging
from pathlib import Path
from typing import Optional


class PathSecurityError(ValueError):
    """Raised when an insecure, UNC, or forbidden network path is supplied."""
    pass


class AppConfig:
    """Manages application directories and configuration settings."""

    DEFAULT_APP_DIR_NAME = "ProjectReportManager"

    def __init__(self, base_dir: Optional[Path] = None) -> None:
        if base_dir is None:
            # Standard Windows user-local AppData
            local_app_data = os.environ.get("LOCALAPPDATA")
            if local_app_data:
                self.base_dir = Path(local_app_data) / self.DEFAULT_APP_DIR_NAME
            else:
                self.base_dir = Path.home() / f".{self.DEFAULT_APP_DIR_NAME.lower()}"
        else:
            self.base_dir = Path(base_dir).resolve()

        self._validate_local_path(self.base_dir)

        # Standard subdirectories per docs/02 Section 11 and docs/10 Section 1
        self.database_dir = self.base_dir / "database"
        self.projects_dir = self.base_dir / "projects"
        self.templates_dir = self.base_dir / "templates"
        self.backups_dir = self.base_dir / "backups"
        self.logs_dir = self.base_dir / "logs"
        self.config_dir = self.base_dir / "config"

        self.db_path = self.database_dir / "project_report_manager.db"

    @classmethod
    def _validate_local_path(cls, path: Path) -> None:
        """Ensure path is local to the machine and not a UNC/network share."""
        path_str = str(path)
        # Check for UNC path (e.g. \\server\share or //server/share)
        if path_str.startswith(("\\\\", "//")):
            raise PathSecurityError(
                f"Forbidden network UNC path: '{path_str}'. "
                "SQLite databases and live application storage must remain on a local drive."
            )
        # On Windows, drive letters like C:, D: are expected.
        # If drive is specified, check if it's considered remote (if win32 api available)
        if sys.platform == "win32":
            drive = os.path.splitdrive(path_str)[0]
            if drive.startswith(("\\\\", "//")):
                raise PathSecurityError(f"UNC network paths are forbidden: '{path_str}'")

    def ensure_directories(self) -> None:
        """Create required application directory tree."""
        for directory in [
            self.base_dir,
            self.database_dir,
            self.projects_dir,
            self.templates_dir,
            self.backups_dir,
            self.logs_dir,
            self.config_dir,
        ]:
            directory.mkdir(parents=True, exist_ok=True)

    @property
    def sqlite_url(self) -> str:
        """Returns standard SQLAlchemy SQLite connection URL."""
        # Forward slashes for SQLite URI
        normalized = self.db_path.as_posix()
        return f"sqlite:///{normalized}"


def setup_logging(config: AppConfig, log_level: int = logging.INFO) -> None:
    """Configures application-wide logging with sensitive data redaction."""
    from app.infrastructure.security.redaction import RedactingFormatter

    config.logs_dir.mkdir(parents=True, exist_ok=True)
    log_file = config.logs_dir / "app.log"

    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)

    # Avoid duplicate handlers on re-init
    if root_logger.handlers:
        root_logger.handlers.clear()

    formatter = RedactingFormatter(
        "%(asctime)s [%(levelname)s] [%(name)s] %(message)s"
    )

    file_handler = logging.FileHandler(log_file, encoding="utf-8")
    file_handler.setFormatter(formatter)
    file_handler.setLevel(log_level)

    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    console_handler.setLevel(log_level)

    root_logger.addHandler(file_handler)
    root_logger.addHandler(console_handler)
