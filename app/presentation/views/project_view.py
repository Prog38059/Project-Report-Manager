"""Project list and detail view with 7-year period grid inspector."""

from typing import Optional, List
import uuid
from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QLineEdit,
    QTableWidget,
    QTableWidgetItem,
    QHeaderView,
    QSplitter,
    QTabWidget,
    QMessageBox,
)

from app.application.dtos.project_dto import ProjectResponseDTO
from app.application.services.project_service import ProjectService
from app.application.services.client_service import ClientService
from app.application.services.entity_service import EntityService
from app.presentation.views.project_wizard import ProjectWizardDialog


class ProjectView(QWidget):
    """View managing projects, viewing their generated 7-year periods, and scenarios."""

    project_selected = Signal(object)  # Emits ProjectResponseDTO

    def __init__(
        self,
        client_service: ClientService,
        entity_service: EntityService,
        project_service: ProjectService,
        parent: Optional[QWidget] = None,
    ) -> None:
        super().__init__(parent)
        self.client_service = client_service
        self.entity_service = entity_service
        self.project_service = project_service
        self.current_project: Optional[ProjectResponseDTO] = None

        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)

        # Header bar
        header = QHBoxLayout()
        title = QLabel("Projects")
        title.setStyleSheet("font-size: 20px; font-weight: bold; color: #202124;")
        header.addWidget(title)
        header.addStretch()

        btn_new_wizard = QPushButton("🚀 New Project Wizard")
        btn_new_wizard.setStyleSheet("background-color: #1a73e8; color: white; padding: 6px 14px; font-weight: bold;")
        btn_new_wizard.clicked.connect(self.open_wizard)
        header.addWidget(btn_new_wizard)
        layout.addLayout(header)

        # Splitter: Left Project List, Right Details & Periods
        splitter = QSplitter(Qt.Horizontal)

        # Left Panel: Project Table
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)
        left_layout.setContentsMargins(0, 0, 0, 0)

        self.table_projects = QTableWidget(0, 4)
        self.table_projects.setHorizontalHeaderLabels(["Code", "Project Name", "Nature", "Status"])
        self.table_projects.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table_projects.setSelectionBehavior(QTableWidget.SelectRows)
        self.table_projects.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table_projects.itemSelectionChanged.connect(self._on_project_selected)
        left_layout.addWidget(self.table_projects)

        # Right Panel: Tabs for Generated Periods and Scenarios
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)
        right_layout.setContentsMargins(0, 0, 0, 0)

        self.lbl_selected_title = QLabel("Select a project to inspect periods and settings")
        self.lbl_selected_title.setStyleSheet("font-size: 14px; font-weight: bold; color: #3c4043;")
        right_layout.addWidget(self.lbl_selected_title)

        self.tabs = QTabWidget()

        # Tab 1: Projection Periods
        tab_periods = QWidget()
        tab_per_layout = QVBoxLayout(tab_periods)
        self.table_periods = QTableWidget(0, 5)
        self.table_periods.setHorizontalHeaderLabels(["Seq", "Period Label", "FY Label", "Start Date", "End Date"])
        self.table_periods.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table_periods.setSelectionBehavior(QTableWidget.SelectRows)
        self.table_periods.setEditTriggers(QTableWidget.NoEditTriggers)
        tab_per_layout.addWidget(self.table_periods)
        self.tabs.addTab(tab_periods, "Projection Periods (Dynamic)")

        # Tab 2: Scenarios
        tab_scenarios = QWidget()
        tab_scen_layout = QVBoxLayout(tab_scenarios)
        self.table_scenarios = QTableWidget(0, 4)
        self.table_scenarios.setHorizontalHeaderLabels(["Code", "Name", "Type", "Default"])
        self.table_scenarios.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table_scenarios.setSelectionBehavior(QTableWidget.SelectRows)
        self.table_scenarios.setEditTriggers(QTableWidget.NoEditTriggers)
        tab_scen_layout.addWidget(self.table_scenarios)
        self.tabs.addTab(tab_scenarios, "Scenarios")

        right_layout.addWidget(self.tabs)

        splitter.addWidget(left_panel)
        splitter.addWidget(right_panel)
        splitter.setStretchFactor(0, 4)
        splitter.setStretchFactor(1, 6)
        layout.addWidget(splitter)

        self.refresh()

    def refresh(self) -> None:
        self.table_projects.setRowCount(0)
        self.table_periods.setRowCount(0)
        self.table_scenarios.setRowCount(0)
        self.current_project = None
        self.lbl_selected_title.setText("Select a project to inspect periods and settings")

        projects = self.project_service.list_all_projects()
        for p in projects:
            row = self.table_projects.rowCount()
            self.table_projects.insertRow(row)

            item = QTableWidgetItem(p.project_code)
            item.setData(Qt.UserRole, p)
            self.table_projects.setItem(row, 0, item)
            self.table_projects.setItem(row, 1, QTableWidgetItem(p.project_name))
            self.table_projects.setItem(row, 2, QTableWidgetItem(p.project_nature_code.value))
            self.table_projects.setItem(row, 3, QTableWidgetItem(p.status_code.value))

    def _on_project_selected(self) -> None:
        items = self.table_projects.selectedItems()
        if not items:
            return
        project: ProjectResponseDTO = self.table_projects.item(items[0].row(), 0).data(Qt.UserRole)
        self.current_project = project
        self.lbl_selected_title.setText(
            f"Project: <b>{project.project_name}</b> [{project.project_code}] — {project.projection_year_count} Projection Years"
        )
        self.project_selected.emit(project)
        self.refresh_periods()
        self.refresh_scenarios()

    def refresh_periods(self) -> None:
        self.table_periods.setRowCount(0)
        if not self.current_project:
            return
        periods = self.project_service.list_periods(self.current_project.id)
        for p in periods:
            row = self.table_periods.rowCount()
            self.table_periods.insertRow(row)
            self.table_periods.setItem(row, 0, QTableWidgetItem(str(p.period_sequence)))
            self.table_periods.setItem(row, 1, QTableWidgetItem(p.period_label))
            self.table_periods.setItem(row, 2, QTableWidgetItem(p.financial_year_label or "-"))
            self.table_periods.setItem(row, 3, QTableWidgetItem(str(p.start_date)))
            self.table_periods.setItem(row, 4, QTableWidgetItem(str(p.end_date)))

    def refresh_scenarios(self) -> None:
        self.table_scenarios.setRowCount(0)
        if not self.current_project:
            return
        scenarios = self.project_service.list_scenarios(self.current_project.id)
        for s in scenarios:
            row = self.table_scenarios.rowCount()
            self.table_scenarios.insertRow(row)
            self.table_scenarios.setItem(row, 0, QTableWidgetItem(s.scenario_code))
            self.table_scenarios.setItem(row, 1, QTableWidgetItem(s.scenario_name))
            self.table_scenarios.setItem(row, 2, QTableWidgetItem(s.scenario_type.value))
            self.table_scenarios.setItem(row, 3, QTableWidgetItem("Yes" if s.is_default else "No"))

    def open_wizard(self) -> None:
        wizard = ProjectWizardDialog(self.client_service, self.entity_service, self.project_service, self)
        if wizard.exec():
            self.refresh()
