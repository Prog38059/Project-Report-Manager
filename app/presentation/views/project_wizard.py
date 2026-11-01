"""Project creation wizard dialog implementing Phase 1 defaults."""

from typing import Optional, List
import uuid
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QLineEdit,
    QComboBox,
    QCheckBox,
    QFormLayout,
    QSpinBox,
    QGroupBox,
    QMessageBox,
)

from app.application.dtos.project_dto import CreateProjectDTO
from app.application.dtos.client_dto import ClientResponseDTO
from app.application.dtos.entity_dto import EntityResponseDTO
from app.application.services.client_service import ClientService
from app.application.services.entity_service import EntityService
from app.application.services.project_service import ProjectService
from app.common.types import ProjectNatureCode


class ProjectWizardDialog(QDialog):
    """Step-by-step project creation wizard enforcing 7-year default and historical off by default."""

    def __init__(
        self,
        client_service: ClientService,
        entity_service: EntityService,
        project_service: ProjectService,
        parent: Optional[QDialog] = None,
    ) -> None:
        super().__init__(parent)
        self.client_service = client_service
        self.entity_service = entity_service
        self.project_service = project_service

        self.setWindowTitle("New Project Report Wizard")
        self.setFixedWidth(520)

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(16)

        # 1. Entity Selection Group
        grp_entity = QGroupBox("1. Applicant & Entity")
        form_entity = QFormLayout(grp_entity)

        self.cmb_client = QComboBox()
        self.cmb_client.currentIndexChanged.connect(self._on_client_changed)
        self.cmb_entity = QComboBox()

        form_entity.addRow("Client *:", self.cmb_client)
        form_entity.addRow("Legal Entity *:", self.cmb_entity)
        main_layout.addWidget(grp_entity)

        # 2. Project Details Group
        grp_details = QGroupBox("2. Project Definition")
        form_details = QFormLayout(grp_details)

        self.txt_code = QLineEdit()
        self.txt_code.setPlaceholderText("e.g. PRJ-2026-001")
        self.txt_name = QLineEdit()
        self.txt_name.setPlaceholderText("e.g. 50kW EV Charging Station Setup")

        self.cmb_nature = QComboBox()
        for nature in ProjectNatureCode:
            self.cmb_nature.addItem(nature.value, nature)

        self.txt_industry = QLineEdit()
        self.txt_industry.setPlaceholderText("e.g. EV Charging, Manufacturing, Retail")

        form_details.addRow("Project Code *:", self.txt_code)
        form_details.addRow("Project Name *:", self.txt_name)
        form_details.addRow("Project Nature:", self.cmb_nature)
        form_details.addRow("Industry:", self.txt_industry)
        main_layout.addWidget(grp_details)

        # 3. Horizon and Conventions (ADR-001, ADR-002, ADR-003)
        grp_timeline = QGroupBox("3. Projection Settings & Defaults")
        form_timeline = QFormLayout(grp_timeline)

        self.spn_start_fy = QSpinBox()
        self.spn_start_fy.setRange(2020, 2050)
        self.spn_start_fy.setValue(2026)

        self.cmb_start_month = QComboBox()
        self.cmb_start_month.addItem("April (Standard India FY)", 4)
        self.cmb_start_month.addItem("January (Calendar Year)", 1)
        self.cmb_start_month.addItem("July", 7)
        self.cmb_start_month.addItem("October", 10)

        # Default 7 annual projection years per ADR-002
        self.spn_years = QSpinBox()
        self.spn_years.setRange(1, 20)
        self.spn_years.setValue(7)  # Explicit 7-year default!

        # Historical mode toggle: Default False per ADR-003
        self.chk_historical = QCheckBox("Enable Historical Financial Data Mode (Default: Off)")
        self.chk_historical.setChecked(False)  # Explicit False default!

        form_timeline.addRow("Commencement FY *:", self.spn_start_fy)
        form_timeline.addRow("FY Start Month *:", self.cmb_start_month)
        form_timeline.addRow("Projection Horizon (Years) *:", self.spn_years)
        form_timeline.addRow(self.chk_historical)
        main_layout.addWidget(grp_timeline)

        # Action Buttons
        btn_box = QHBoxLayout()
        btn_create = QPushButton("Create Project & Generate Periods")
        btn_create.setStyleSheet("background-color: #1a73e8; color: white; padding: 6px 14px; font-weight: bold;")
        btn_create.clicked.connect(self._create_project)
        btn_cancel = QPushButton("Cancel")
        btn_cancel.clicked.connect(self.reject)

        btn_box.addStretch()
        btn_box.addWidget(btn_cancel)
        btn_box.addWidget(btn_create)
        main_layout.addLayout(btn_box)

        self._populate_clients()

    def _populate_clients(self) -> None:
        self.cmb_client.clear()
        clients = self.client_service.list_clients()
        for c in clients:
            self.cmb_client.addItem(f"{c.display_name} ({c.client_code})", c.id)

    def _on_client_changed(self) -> None:
        self.cmb_entity.clear()
        client_id = self.cmb_client.currentData()
        if not client_id:
            return
        entities = self.entity_service.list_entities_for_client(client_id)
        for ent in entities:
            self.cmb_entity.addItem(f"{ent.legal_name} ({ent.constitution_code.value})", ent.id)

    def _create_project(self) -> None:
        entity_id = self.cmb_entity.currentData()
        if not entity_id:
            QMessageBox.warning(self, "Missing Entity", "Please select a legal entity for this project.")
            return

        code = self.txt_code.text().strip()
        name = self.txt_name.text().strip()
        if not code or not name:
            QMessageBox.warning(self, "Required Fields", "Project code and project name are mandatory.")
            return

        dto = CreateProjectDTO(
            entity_id=entity_id,
            project_code=code,
            project_name=name,
            project_nature_code=self.cmb_nature.currentData(),
            industry_code=self.txt_industry.text().strip() or None,
            financial_year_start_month=self.cmb_start_month.currentData(),
            projection_year_count=self.spn_years.value(),
            projection_start_financial_year=self.spn_start_fy.value(),
            historical_data_enabled=self.chk_historical.isChecked(),
        )

        try:
            self.created_project = self.project_service.create_project(dto)
            self.accept()
        except Exception as e:
            QMessageBox.critical(self, "Creation Failed", f"Could not create project: {e}")
