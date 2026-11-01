"""Integration tests for Backup & Restore service."""

from pathlib import Path
import tempfile
import pytest

from app.application.dtos.client_dto import CreateClientDTO
from app.application.dtos.entity_dto import CreateEntityDTO
from app.application.dtos.project_dto import CreateProjectDTO
from app.application.services.client_service import ClientService
from app.application.services.entity_service import EntityService
from app.application.services.project_service import ProjectService
from app.application.services.backup_service import BackupService
from app.common.types import ConstitutionCode
from app.config import AppConfig
from app.infrastructure.database.connection import DatabaseManager
from app.infrastructure.storage.file_store import FileStore


def test_backup_and_verified_restore(
    test_config: AppConfig,
    client_service: ClientService,
    entity_service: EntityService,
    project_service: ProjectService,
    backup_service: BackupService,
    file_store: FileStore,
    temp_dir: Path,
):
    # 1. Populate database with records
    client = client_service.create_client(
        CreateClientDTO(client_code="CLT-BAK-01", display_name="Backup Test Client")
    )
    entity = entity_service.create_entity(
        CreateEntityDTO(
            client_id=client.id,
            constitution_code=ConstitutionCode.PRIVATE_LIMITED,
            legal_name="Backup Test Pvt Ltd",
        )
    )
    project = project_service.create_project(
        CreateProjectDTO(
            entity_id=entity.id,
            project_code="PRJ-BAK-01",
            project_name="Disaster Recovery Plant",
        )
    )

    # 2. Add a sample attachment to disk
    sample_doc = temp_dir / "quotation.pdf"
    sample_doc.write_bytes(b"Vendor quote #123456 content for backup verification")
    file_store.store_file(sample_doc, project_id=project.id, file_category="VENDOR_QUOTE")

    # 3. Create backup
    zip_path = backup_service.create_backup(notes="Automated pre-restore test backup")
    assert zip_path.exists()
    assert zip_path.stat().st_size > 0

    # 4. Perform verified restore into a fresh staging directory
    restore_target = temp_dir / "restored_system"
    restore_result = backup_service.verify_and_restore(zip_path, restore_target)

    assert restore_result["success"] is True
    assert restore_result["verified_files_count"] >= 2  # database.db + at least 1 attachment
    assert restore_result["schema_version"] == "0001_phase1_foundation"

    # 5. Connect to restored database and verify records are intact
    restored_db_file = restore_target / "database" / "project_report_manager.db"
    assert restored_db_file.exists()

    restored_mgr = DatabaseManager(f"sqlite:///{restored_db_file.as_posix()}")
    restored_client_service = ClientService(restored_mgr)
    restored_proj_service = ProjectService(restored_mgr)

    restored_clients = restored_client_service.list_clients()
    assert any(c.client_code == "CLT-BAK-01" for c in restored_clients)

    restored_projects = restored_proj_service.list_all_projects()
    assert any(p.project_code == "PRJ-BAK-01" for p in restored_projects)
    restored_mgr.engine.dispose()
