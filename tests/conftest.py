"""Pytest configuration and shared test fixtures."""

import os
from pathlib import Path
import tempfile
from typing import Generator
import pytest
from cryptography.fernet import Fernet

from app.config import AppConfig
from app.infrastructure.database.connection import DatabaseManager
from app.infrastructure.security.encryption import EncryptionService
from app.infrastructure.storage.file_store import FileStore
from app.application.services.client_service import ClientService
from app.application.services.entity_service import EntityService
from app.application.services.project_service import ProjectService
from app.application.services.backup_service import BackupService


@pytest.fixture
def temp_dir() -> Generator[Path, None, None]:
    """Provides a fresh temporary directory."""
    with tempfile.TemporaryDirectory() as td:
        yield Path(td).resolve()


@pytest.fixture
def test_config(temp_dir: Path) -> AppConfig:
    """Config pointing to temporary storage."""
    cfg = AppConfig(base_dir=temp_dir)
    cfg.ensure_directories()
    return cfg


@pytest.fixture
def test_db(test_config: AppConfig) -> Generator[DatabaseManager, None, None]:
    """DatabaseManager initialized with a fresh local SQLite database and created tables."""
    db_manager = DatabaseManager.from_config(test_config)
    db_manager.create_tables()
    try:
        yield db_manager
    finally:
        db_manager.engine.dispose()


@pytest.fixture
def encryption_service() -> EncryptionService:
    """EncryptionService with a fixed ephemeral key for predictable testing."""
    key = Fernet.generate_key()
    return EncryptionService(fixed_key=key)


@pytest.fixture
def file_store(test_config: AppConfig) -> FileStore:
    """FileStore initialized with test storage directory."""
    return FileStore(test_config.base_dir)


@pytest.fixture
def client_service(test_db: DatabaseManager) -> ClientService:
    return ClientService(test_db)


@pytest.fixture
def entity_service(test_db: DatabaseManager, encryption_service: EncryptionService) -> EntityService:
    return EntityService(test_db, encryption_service)


@pytest.fixture
def project_service(test_db: DatabaseManager) -> ProjectService:
    return ProjectService(test_db)


@pytest.fixture
def backup_service(test_config: AppConfig, test_db: DatabaseManager) -> BackupService:
    return BackupService(test_config, test_db)
