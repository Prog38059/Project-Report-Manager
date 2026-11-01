"""Dashboard presentation view."""

from typing import Optional
from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QFrame,
    QGroupBox,
)


class DashboardView(QWidget):
    """Home dashboard view with summary stats and quick action launch buttons."""

    request_new_project = Signal()
    request_new_client = Signal()
    request_view_projects = Signal()
    request_load_demo = Signal()

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(20)

        # Header
        title = QLabel("Dashboard")
        title.setStyleSheet("font-size: 22px; font-weight: bold; color: #1a73e8;")
        subtitle = QLabel("Overview of project reports, clients, and legal entities")
        subtitle.setStyleSheet("font-size: 13px; color: #5f6368;")

        layout.addWidget(title)
        layout.addWidget(subtitle)

        # Stats Cards Row
        stats_layout = QHBoxLayout()
        stats_layout.setSpacing(16)

        self.card_clients = self._create_stat_card("Active Clients", "0")
        self.card_entities = self._create_stat_card("Legal Entities", "0")
        self.card_projects = self._create_stat_card("Active Projects", "0")

        stats_layout.addWidget(self.card_clients)
        stats_layout.addWidget(self.card_entities)
        stats_layout.addWidget(self.card_projects)
        layout.addLayout(stats_layout)

        # Quick Actions
        actions_group = QGroupBox("Quick Actions")
        actions_layout = QHBoxLayout(actions_group)
        actions_layout.setSpacing(12)

        btn_new_proj = QPushButton("🚀 New Project Wizard")
        btn_new_proj.setFixedHeight(36)
        btn_new_proj.setStyleSheet("background-color: #1a73e8; color: white; font-weight: bold; border-radius: 4px;")
        btn_new_proj.clicked.connect(self.request_new_project.emit)

        btn_new_client = QPushButton("+ Add Client")
        btn_new_client.setFixedHeight(36)
        btn_new_client.clicked.connect(self.request_new_client.emit)

        btn_view_projs = QPushButton("📁 View Projects")
        btn_view_projs.setFixedHeight(36)
        btn_view_projs.clicked.connect(self.request_view_projects.emit)

        btn_load_demo = QPushButton("✨ Load Demo Project")
        btn_load_demo.setFixedHeight(36)
        btn_load_demo.setStyleSheet("background-color: #6f42c1; color: white; font-weight: bold; border-radius: 4px; padding: 0 12px;")
        btn_load_demo.clicked.connect(self.request_load_demo.emit)

        actions_layout.addWidget(btn_new_proj)
        actions_layout.addWidget(btn_new_client)
        actions_layout.addWidget(btn_view_projs)
        actions_layout.addWidget(btn_load_demo)
        actions_layout.addStretch()

        layout.addWidget(actions_group)
        layout.addStretch()

    def _create_stat_card(self, title: str, initial_value: str) -> QFrame:
        frame = QFrame()
        frame.setFrameShape(QFrame.StyledPanel)
        frame.setStyleSheet("""
            QFrame {
                background-color: #ffffff;
                border: 1px solid #dadce0;
                border-radius: 8px;
                padding: 16px;
            }
        """)
        f_layout = QVBoxLayout(frame)
        f_layout.setContentsMargins(12, 12, 12, 12)

        lbl_title = QLabel(title)
        lbl_title.setStyleSheet("font-size: 13px; color: #5f6368;")

        lbl_val = QLabel(initial_value)
        lbl_val.setStyleSheet("font-size: 28px; font-weight: bold; color: #202124;")
        lbl_val.setObjectName("val_label")

        f_layout.addWidget(lbl_title)
        f_layout.addWidget(lbl_val)
        return frame

    def update_stats(self, client_count: int, entity_count: int, project_count: int) -> None:
        val_clients = self.card_clients.findChild(QLabel, "val_label")
        if val_clients:
            val_clients.setText(str(client_count))

        val_entities = self.card_entities.findChild(QLabel, "val_label")
        if val_entities:
            val_entities.setText(str(entity_count))

        val_projects = self.card_projects.findChild(QLabel, "val_label")
        if val_projects:
            val_projects.setText(str(project_count))
