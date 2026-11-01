"""Client management view and creation dialog."""

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
    QDialog,
    QFormLayout,
    QComboBox,
    QTextEdit,
    QMessageBox,
)

from app.application.dtos.client_dto import CreateClientDTO, ClientResponseDTO
from app.application.services.client_service import ClientService


class ClientDialog(QDialog):
    """Dialog to create or edit a client."""

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Add Client")
        self.setFixedWidth(400)

        layout = QVBoxLayout(self)
        form_layout = QFormLayout()

        self.txt_code = QLineEdit()
        self.txt_code.setPlaceholderText("e.g. CLT-0001")
        self.txt_name = QLineEdit()
        self.txt_name.setPlaceholderText("Client display / trade name")
        self.cmb_category = QComboBox()
        self.cmb_category.addItems(["PERSON", "BUSINESS", "OTHER"])

        self.txt_phone = QLineEdit()
        self.txt_email = QLineEdit()
        self.txt_address = QTextEdit()
        self.txt_address.setMaximumHeight(60)
        self.txt_notes = QTextEdit()
        self.txt_notes.setMaximumHeight(60)

        form_layout.addRow("Client Code *:", self.txt_code)
        form_layout.addRow("Display Name *:", self.txt_name)
        form_layout.addRow("Category:", self.cmb_category)
        form_layout.addRow("Phone:", self.txt_phone)
        form_layout.addRow("Email:", self.txt_email)
        form_layout.addRow("Address:", self.txt_address)
        form_layout.addRow("Notes:", self.txt_notes)

        layout.addLayout(form_layout)

        btn_box = QHBoxLayout()
        btn_save = QPushButton("Save Client")
        btn_save.clicked.connect(self.accept)
        btn_cancel = QPushButton("Cancel")
        btn_cancel.clicked.connect(self.reject)

        btn_box.addStretch()
        btn_box.addWidget(btn_cancel)
        btn_box.addWidget(btn_save)
        layout.addLayout(btn_box)

    def get_dto(self) -> CreateClientDTO:
        return CreateClientDTO(
            client_code=self.txt_code.text(),
            display_name=self.txt_name.text(),
            client_category=self.cmb_category.currentText(),
            phone=self.txt_phone.text() or None,
            email=self.txt_email.text() or None,
            address_text=self.txt_address.toPlainText() or None,
            notes=self.txt_notes.toPlainText() or None,
        )


class ClientView(QWidget):
    """List and manage clients."""

    client_selected = Signal(object)  # Emits ClientResponseDTO

    def __init__(self, client_service: ClientService, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.client_service = client_service
        self.clients_cache: List[ClientResponseDTO] = []

        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)

        # Header bar
        header_layout = QHBoxLayout()
        title = QLabel("Clients")
        title.setStyleSheet("font-size: 20px; font-weight: bold; color: #202124;")
        header_layout.addWidget(title)
        header_layout.addStretch()

        btn_add = QPushButton("+ Add Client")
        btn_add.setStyleSheet("background-color: #1a73e8; color: white; padding: 6px 14px; font-weight: bold;")
        btn_add.clicked.connect(self.open_add_dialog)
        header_layout.addWidget(btn_add)
        layout.addLayout(header_layout)

        # Search Bar
        self.txt_search = QLineEdit()
        self.txt_search.setPlaceholderText("🔍 Search clients by name or code...")
        self.txt_search.textChanged.connect(self.filter_clients)
        layout.addWidget(self.txt_search)

        # Table
        self.table = QTableWidget(0, 5)
        self.table.setHorizontalHeaderLabels(["Code", "Display Name", "Category", "Phone", "Email"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.itemSelectionChanged.connect(self._on_row_selected)
        layout.addWidget(self.table)

        self.refresh()

    def refresh(self) -> None:
        self.clients_cache = self.client_service.list_clients()
        self.populate_table(self.clients_cache)

    def populate_table(self, clients: List[ClientResponseDTO]) -> None:
        self.table.setRowCount(0)
        for client in clients:
            row = self.table.rowCount()
            self.table.insertRow(row)

            item_code = QTableWidgetItem(client.client_code)
            item_code.setData(Qt.UserRole, client)
            self.table.setItem(row, 0, item_code)
            self.table.setItem(row, 1, QTableWidgetItem(client.display_name))
            self.table.setItem(row, 2, QTableWidgetItem(client.client_category))
            self.table.setItem(row, 3, QTableWidgetItem(client.phone or "-"))
            self.table.setItem(row, 4, QTableWidgetItem(client.email or "-"))

    def filter_clients(self, text: str) -> None:
        query = text.strip().lower()
        if not query:
            self.populate_table(self.clients_cache)
            return

        filtered = [
            c for c in self.clients_cache
            if query in c.client_code.lower() or query in c.display_name.lower()
        ]
        self.populate_table(filtered)

    def _on_row_selected(self) -> None:
        selected_items = self.table.selectedItems()
        if selected_items:
            client_dto = self.table.item(selected_items[0].row(), 0).data(Qt.UserRole)
            self.client_selected.emit(client_dto)

    def open_add_dialog(self) -> None:
        dialog = ClientDialog(self)
        if dialog.exec():
            dto = dialog.get_dto()
            try:
                self.client_service.create_client(dto)
                self.refresh()
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to save client: {e}")
