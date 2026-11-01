"""Integration tests for PySide6 application shell and views in offscreen mode."""

import os
import sys
import pytest
from PySide6.QtWidgets import QApplication

from app.config import AppConfig
from app.infrastructure.database.connection import DatabaseManager
from app.infrastructure.security.encryption import EncryptionService
from app.presentation.main_window import MainWindow
from app.presentation.views.dashboard_view import DashboardView
from app.presentation.views.client_view import ClientView
from app.presentation.views.entity_view import EntityView
from app.presentation.views.project_view import ProjectView
from app.presentation.views.backup_view import BackupView
from app.application.dtos.client_dto import CreateClientDTO
from app.application.dtos.entity_dto import CreateEntityDTO
from app.common.types import ConstitutionCode


from app.presentation.views.appraisal_view import AppraisalView
from app.presentation.views.statements_view import StatementsView


@pytest.fixture(scope="session")
def qapp():
    """Ensure a single QApplication instance exists with offscreen rendering."""
    os.environ["QT_QPA_PLATFORM"] = "offscreen"
    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)
    return app


def test_main_window_and_views_instantiation(
    qapp,
    test_config: AppConfig,
    test_db: DatabaseManager,
    encryption_service: EncryptionService,
):
    # Initialize Main Window
    window = MainWindow(test_config, test_db, encryption_service)
    assert window.windowTitle() == "Project Report Manager v1.0"

    # Verify all views are instantiated in stack
    assert isinstance(window.view_dashboard, DashboardView)
    assert isinstance(window.view_clients, ClientView)
    assert isinstance(window.view_entities, EntityView)
    assert isinstance(window.view_projects, ProjectView)
    assert isinstance(window.view_statements, StatementsView)
    assert isinstance(window.view_appraisal, AppraisalView)
    assert isinstance(window.view_backup, BackupView)

    # Add a client and refresh views
    client = window.client_service.create_client(
        CreateClientDTO(client_code="CLT-UI-01", display_name="UI Test Client")
    )
    window.entity_service.create_entity(
        CreateEntityDTO(
            client_id=client.id,
            constitution_code=ConstitutionCode.LLP,
            legal_name="UI Test LLP",
        )
    )

    # Test navigation tab switching
    window.nav_list.setCurrentRow(1)
    assert window.stack.currentIndex() == 1
    assert window.view_clients.table.rowCount() == 1

    window.nav_list.setCurrentRow(2)
    assert window.stack.currentIndex() == 2

    window.nav_list.setCurrentRow(3)
    assert window.stack.currentIndex() == 3

    window.nav_list.setCurrentRow(4)
    assert window.stack.currentIndex() == 4

    window.nav_list.setCurrentRow(5)
    assert window.stack.currentIndex() == 5

    window.nav_list.setCurrentRow(6)
    assert window.stack.currentIndex() == 6

    window.close()

