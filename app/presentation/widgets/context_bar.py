"""Context bar widget showing active client, entity, and project."""

from typing import Optional
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QWidget,
    QHBoxLayout,
    QLabel,
    QFrame,
)


class ContextBar(QWidget):
    """Top contextual banner showing current navigation scope."""

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.setFixedHeight(36)
        self.setObjectName("ContextBar")

        layout = QHBoxLayout(self)
        layout.setContentsMargins(16, 4, 16, 4)
        layout.setSpacing(12)

        self.lbl_client = QLabel("Client: <i>None</i>")
        self.lbl_entity = QLabel("Entity: <i>None</i>")
        self.lbl_project = QLabel("Project: <i>None</i>")
        self.lbl_status = QLabel("Status: Ready")

        sep1 = QFrame()
        sep1.setFrameShape(QFrame.VLine)
        sep2 = QFrame()
        sep2.setFrameShape(QFrame.VLine)
        sep3 = QFrame()
        sep3.setFrameShape(QFrame.VLine)

        layout.addWidget(self.lbl_client)
        layout.addWidget(sep1)
        layout.addWidget(self.lbl_entity)
        layout.addWidget(sep2)
        layout.addWidget(self.lbl_project)
        layout.addStretch()
        layout.addWidget(sep3)
        layout.addWidget(self.lbl_status)

        self.setStyleSheet("""
            #ContextBar {
                background-color: #f1f3f4;
                border-bottom: 1px solid #dadce0;
            }
            QLabel {
                font-size: 12px;
                color: #3c4043;
            }
        """)

    def set_context(
        self,
        client_name: Optional[str] = None,
        entity_name: Optional[str] = None,
        project_name: Optional[str] = None,
        status: Optional[str] = None,
    ) -> None:
        if client_name:
            self.lbl_client.setText(f"Client: <b>{client_name}</b>")
        else:
            self.lbl_client.setText("Client: <i>None</i>")

        if entity_name:
            self.lbl_entity.setText(f"Entity: <b>{entity_name}</b>")
        else:
            self.lbl_entity.setText("Entity: <i>None</i>")

        if project_name:
            self.lbl_project.setText(f"Project: <b>{project_name}</b>")
        else:
            self.lbl_project.setText("Project: <i>None</i>")

        if status:
            self.lbl_status.setText(f"Status: {status}")
