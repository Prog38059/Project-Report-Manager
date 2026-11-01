"""Main desktop application window and navigation shell."""

from typing import Optional
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QListWidget,
    QListWidgetItem,
    QStackedWidget,
    QStatusBar,
)

from app.config import AppConfig
from app.infrastructure.database.connection import DatabaseManager
from app.infrastructure.security.encryption import EncryptionService
from app.application.services.backup_service import BackupService
from app.application.services.client_service import ClientService
from app.application.services.entity_service import EntityService
from app.application.services.expense_service import ExpenseService
from app.application.services.financial_engine_service import FinancialEngineService
from app.application.services.funding_service import FundingService
from app.application.services.historical_service import HistoricalService
from app.application.services.project_cost_service import ProjectCostService
from app.application.services.project_service import ProjectService
from app.application.services.revenue_service import RevenueService
from app.application.services.template_service import TemplateService

from app.presentation.views.backup_view import BackupView
from app.presentation.views.client_view import ClientView
from app.presentation.views.dashboard_view import DashboardView
from app.presentation.views.entity_view import EntityView
from app.presentation.views.project_view import ProjectView
from app.presentation.views.statements_view import StatementsView
from app.presentation.widgets.context_bar import ContextBar



class MainWindow(QMainWindow):
    """Main window shell containing navigation rail and module views."""

    def __init__(
        self,
        config: AppConfig,
        db_manager: DatabaseManager,
        encryption_service: EncryptionService,
        parent: Optional[QWidget] = None,
    ) -> None:
        super().__init__(parent)
        self.config = config
        self.db_manager = db_manager
        self.encryption_service = encryption_service

        # Initialize application services
        self.client_service = ClientService(db_manager)
        self.entity_service = EntityService(db_manager, encryption_service)
        self.project_service = ProjectService(db_manager)
        self.backup_service = BackupService(config, db_manager)
        self.project_cost_service = ProjectCostService(db_manager)
        self.funding_service = FundingService(db_manager)
        self.revenue_service = RevenueService(db_manager)
        self.expense_service = ExpenseService(db_manager)
        self.template_service = TemplateService(db_manager)
        self.historical_service = HistoricalService(db_manager)
        self.fin_engine_service = FinancialEngineService(db_manager)

        self.setWindowTitle("Project Report Manager v1.0")
        self.resize(1180, 750)

        # Main Layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # 1. Top Context Bar
        self.context_bar = ContextBar(self)
        main_layout.addWidget(self.context_bar)

        # 2. Body Area (Left Nav Rail + Right Stack)
        body_layout = QHBoxLayout()
        body_layout.setContentsMargins(0, 0, 0, 0)
        body_layout.setSpacing(0)

        # Left Nav Rail
        self.nav_list = QListWidget()
        self.nav_list.setFixedWidth(200)
        self.nav_list.setStyleSheet("""
            QListWidget {
                background-color: #202124;
                color: #e8eaed;
                font-size: 14px;
                border: none;
                padding-top: 12px;
            }
            QListWidget::item {
                height: 44px;
                padding-left: 16px;
            }
            QListWidget::item:selected {
                background-color: #1a73e8;
                color: #ffffff;
                font-weight: bold;
            }
            QListWidget::item:hover {
                background-color: #303134;
            }
        """)

        nav_items = [
            ("📊 Dashboard", 0),
            ("👥 Clients", 1),
            ("🏛 Entities", 2),
            ("📁 Projects", 3),
            ("📈 Statements", 4),
            ("💾 Backup & Restore", 5),
        ]
        for label, idx in nav_items:
            item = QListWidgetItem(label)
            item.setData(Qt.UserRole, idx)
            self.nav_list.addItem(item)

        self.nav_list.currentRowChanged.connect(self._on_nav_changed)
        body_layout.addWidget(self.nav_list)

        # Right Stacked Area
        self.stack = QStackedWidget()
        self.view_dashboard = DashboardView()
        self.view_clients = ClientView(self.client_service)
        self.view_entities = EntityView(self.client_service, self.entity_service)
        self.view_projects = ProjectView(
            client_service=self.client_service,
            entity_service=self.entity_service,
            project_service=self.project_service,
            project_cost_service=self.project_cost_service,
            funding_service=self.funding_service,
            revenue_service=self.revenue_service,
            expense_service=self.expense_service,
            template_service=self.template_service,
            historical_service=self.historical_service,
        )
        self.view_statements = StatementsView(
            project_service=self.project_service,
            financial_engine_service=self.fin_engine_service,
        )
        self.view_backup = BackupView(self.backup_service, self.config)

        self.stack.addWidget(self.view_dashboard)
        self.stack.addWidget(self.view_clients)
        self.stack.addWidget(self.view_entities)
        self.stack.addWidget(self.view_projects)
        self.stack.addWidget(self.view_statements)
        self.stack.addWidget(self.view_backup)

        body_layout.addWidget(self.stack)
        main_layout.addLayout(body_layout)

        # Status Bar
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("Project Report Manager ready. Local database connected.")

        # Wire Signals
        self._wire_signals()
        self.nav_list.setCurrentRow(0)
        self._refresh_dashboard_counts()

    def _wire_signals(self) -> None:
        # Dashboard quick actions
        self.view_dashboard.request_new_project.connect(self._open_project_wizard)
        self.view_dashboard.request_new_client.connect(self._open_add_client)
        self.view_dashboard.request_view_projects.connect(lambda: self.nav_list.setCurrentRow(3))

        # Context selection updates
        self.view_clients.client_selected.connect(self._on_client_selected)
        self.view_entities.entity_selected.connect(self._on_entity_selected)
        self.view_projects.project_selected.connect(self._on_project_selected)

    def _on_nav_changed(self, row: int) -> None:
        self.stack.setCurrentIndex(row)
        if row == 0:
            self._refresh_dashboard_counts()
        elif row == 1:
            self.view_clients.refresh()
        elif row == 2:
            self.view_entities.refresh_clients()
        elif row == 3:
            self.view_projects.refresh()
        elif row == 4:
            self.view_statements.refresh_projects()
        elif row == 5:
            self.view_backup.refresh()


    def _refresh_dashboard_counts(self) -> None:
        clients = len(self.client_service.list_clients())
        projects = len(self.project_service.list_all_projects())
        # Aggregate entities
        total_entities = 0
        for c in self.client_service.list_clients():
            total_entities += len(self.entity_service.list_entities_for_client(c.id))
        self.view_dashboard.update_stats(clients, total_entities, projects)

    def _open_project_wizard(self) -> None:
        self.view_projects.open_wizard()
        self._refresh_dashboard_counts()

    def _open_add_client(self) -> None:
        self.view_clients.open_add_dialog()
        self._refresh_dashboard_counts()

    def _on_client_selected(self, client) -> None:
        self.context_bar.set_context(client_name=client.display_name)

    def _on_entity_selected(self, entity) -> None:
        self.context_bar.set_context(entity_name=entity.legal_name)

    def _on_project_selected(self, project) -> None:
        self.context_bar.set_context(
            project_name=f"{project.project_name} ({project.project_code})",
            status=project.status_code.value,
        )
