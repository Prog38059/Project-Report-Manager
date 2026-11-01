"""Legal Entity management view and constitution-aware dialogs."""

from datetime import date
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
    QTabWidget,
    QMessageBox,
)

from app.application.dtos.entity_dto import (
    CreateEntityDTO,
    EntityResponseDTO,
    EntityMemberDTO,
)
from app.application.dtos.client_dto import ClientResponseDTO
from app.application.services.client_service import ClientService
from app.application.services.entity_service import EntityService
from app.common.types import ConstitutionCode, MemberRoleCode
from app.domain.entities.legal_entity import (
    HUFDetails,
    ProprietorshipDetails,
    PartnershipDetails,
    LLPDetails,
    CompanyDetails,
)
from app.presentation.widgets.sensitive_field import SensitiveFieldWidget


class EntityDialog(QDialog):
    """Dialog to create an entity with constitution-specific details."""

    def __init__(self, client_id: uuid.UUID, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.client_id = client_id
        self.setWindowTitle("Add Legal Entity")
        self.setFixedWidth(460)

        layout = QVBoxLayout(self)
        form_layout = QFormLayout()

        self.cmb_constitution = QComboBox()
        for const in ConstitutionCode:
            self.cmb_constitution.addItem(const.value, const)

        self.txt_legal_name = QLineEdit()
        self.txt_legal_name.setPlaceholderText("e.g. Acme Industries LLP")
        self.txt_trade_name = QLineEdit()
        self.txt_desc = QTextEdit()
        self.txt_desc.setMaximumHeight(60)

        form_layout.addRow("Constitution *:", self.cmb_constitution)
        form_layout.addRow("Legal Name *:", self.txt_legal_name)
        form_layout.addRow("Trade Name:", self.txt_trade_name)
        form_layout.addRow("Business Description:", self.txt_desc)

        layout.addLayout(form_layout)

        btn_box = QHBoxLayout()
        btn_save = QPushButton("Save Entity")
        btn_save.clicked.connect(self.accept)
        btn_cancel = QPushButton("Cancel")
        btn_cancel.clicked.connect(self.reject)

        btn_box.addStretch()
        btn_box.addWidget(btn_cancel)
        btn_box.addWidget(btn_save)
        layout.addLayout(btn_box)

    def get_dto(self) -> CreateEntityDTO:
        const_code = self.cmb_constitution.currentData()
        return CreateEntityDTO(
            client_id=self.client_id,
            constitution_code=const_code,
            legal_name=self.txt_legal_name.text(),
            trade_name=self.txt_trade_name.text() or None,
            business_description=self.txt_desc.toPlainText() or None,
        )


class MemberDialog(QDialog):
    """Dialog to add a member (Director, Partner, Karta, etc.) to an entity."""

    def __init__(self, entity_id: uuid.UUID, constitution: ConstitutionCode, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.entity_id = entity_id
        self.setWindowTitle("Add Entity Member")
        self.setFixedWidth(420)

        layout = QVBoxLayout(self)
        form_layout = QFormLayout()

        self.txt_name = QLineEdit()
        self.cmb_role = QComboBox()

        # Suggest relevant roles based on constitution
        if constitution == ConstitutionCode.PARTNERSHIP:
            self.cmb_role.addItem("PARTNER", MemberRoleCode.PARTNER)
        elif constitution == ConstitutionCode.LLP:
            self.cmb_role.addItem("DESIGNATED_PARTNER", MemberRoleCode.DESIGNATED_PARTNER)
            self.cmb_role.addItem("PARTNER", MemberRoleCode.PARTNER)
        elif constitution == ConstitutionCode.HUF:
            self.cmb_role.addItem("KARTA", MemberRoleCode.KARTA)
            self.cmb_role.addItem("COPARCENER", MemberRoleCode.COPARCENER)
        elif constitution == ConstitutionCode.PROPRIETORSHIP:
            self.cmb_role.addItem("PROPRIETOR", MemberRoleCode.PROPRIETOR)
        elif constitution == ConstitutionCode.PRIVATE_LIMITED:
            self.cmb_role.addItem("DIRECTOR", MemberRoleCode.DIRECTOR)
            self.cmb_role.addItem("SHAREHOLDER", MemberRoleCode.SHAREHOLDER)
            self.cmb_role.addItem("PROMOTER", MemberRoleCode.PROMOTER)
        else:
            self.cmb_role.addItem("INDIVIDUAL_APPLICANT", MemberRoleCode.INDIVIDUAL_APPLICANT)

        self.txt_pan = SensitiveFieldWidget("PAN (e.g. ABCDE1234F)")
        self.txt_phone = QLineEdit()
        self.txt_email = QLineEdit()
        self.txt_profit_share = QLineEdit()
        self.txt_profit_share.setPlaceholderText("e.g. 50.0")

        form_layout.addRow("Full Name *:", self.txt_name)
        form_layout.addRow("Role *:", self.cmb_role)
        form_layout.addRow("PAN:", self.txt_pan)
        form_layout.addRow("Phone:", self.txt_phone)
        form_layout.addRow("Email:", self.txt_email)
        form_layout.addRow("Profit Share %:", self.txt_profit_share)

        layout.addLayout(form_layout)

        btn_box = QHBoxLayout()
        btn_save = QPushButton("Save Member")
        btn_save.clicked.connect(self.accept)
        btn_cancel = QPushButton("Cancel")
        btn_cancel.clicked.connect(self.reject)

        btn_box.addStretch()
        btn_box.addWidget(btn_cancel)
        btn_box.addWidget(btn_save)
        layout.addLayout(btn_box)

    def get_dto(self) -> EntityMemberDTO:
        return EntityMemberDTO(
            entity_id=self.entity_id,
            full_name=self.txt_name.text(),
            role_code=self.cmb_role.currentData(),
            pan_plaintext=self.txt_pan.text() or None,
            contact_phone=self.txt_phone.text() or None,
            contact_email=self.txt_email.text() or None,
            profit_share_pct=self.txt_profit_share.text() or None,
        )


class EntityView(QWidget):
    """View managing entities for selected client, with member register and constitution info."""

    entity_selected = Signal(object)  # Emits EntityResponseDTO

    def __init__(
        self,
        client_service: ClientService,
        entity_service: EntityService,
        parent: Optional[QWidget] = None,
    ) -> None:
        super().__init__(parent)
        self.client_service = client_service
        self.entity_service = entity_service
        self.current_client: Optional[ClientResponseDTO] = None
        self.current_entity: Optional[EntityResponseDTO] = None

        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)

        # Header bar with Client Selector
        header = QHBoxLayout()
        title = QLabel("Entities & Members")
        title.setStyleSheet("font-size: 20px; font-weight: bold; color: #202124;")
        header.addWidget(title)
        header.addStretch()

        header.addWidget(QLabel("Select Client:"))
        self.cmb_client_selector = QComboBox()
        self.cmb_client_selector.setMinimumWidth(200)
        self.cmb_client_selector.currentIndexChanged.connect(self._on_client_changed)
        header.addWidget(self.cmb_client_selector)

        self.btn_add_entity = QPushButton("+ Add Entity")
        self.btn_add_entity.setStyleSheet("background-color: #1a73e8; color: white; padding: 6px 14px; font-weight: bold;")
        self.btn_add_entity.clicked.connect(self.open_add_entity_dialog)
        header.addWidget(self.btn_add_entity)

        layout.addLayout(header)

        # Tabs: Entities List and Selected Entity Members
        self.tabs = QTabWidget()

        # Tab 1: Entities Table
        tab_entities = QWidget()
        tab_ent_layout = QVBoxLayout(tab_entities)
        self.table_entities = QTableWidget(0, 4)
        self.table_entities.setHorizontalHeaderLabels(["Legal Name", "Constitution", "Trade Name", "Created"])
        self.table_entities.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table_entities.setSelectionBehavior(QTableWidget.SelectRows)
        self.table_entities.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table_entities.itemSelectionChanged.connect(self._on_entity_selected)
        tab_ent_layout.addWidget(self.table_entities)
        self.tabs.addTab(tab_entities, "Entities")

        # Tab 2: Members
        tab_members = QWidget()
        tab_mem_layout = QVBoxLayout(tab_members)

        mem_header = QHBoxLayout()
        self.lbl_selected_entity = QLabel("Members for: <i>Select an entity above</i>")
        mem_header.addWidget(self.lbl_selected_entity)
        mem_header.addStretch()

        self.btn_add_member = QPushButton("+ Add Member")
        self.btn_add_member.clicked.connect(self.open_add_member_dialog)
        self.btn_add_member.setEnabled(False)
        mem_header.addWidget(self.btn_add_member)
        tab_mem_layout.addLayout(mem_header)

        self.table_members = QTableWidget(0, 5)
        self.table_members.setHorizontalHeaderLabels(["Name", "Role", "PAN", "Phone", "Profit/Share %"])
        self.table_members.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table_members.setSelectionBehavior(QTableWidget.SelectRows)
        self.table_members.setEditTriggers(QTableWidget.NoEditTriggers)
        tab_mem_layout.addWidget(self.table_members)

        self.tabs.addTab(tab_members, "Entity Members")
        layout.addWidget(self.tabs)

        self.refresh_clients()

    def refresh_clients(self) -> None:
        self.cmb_client_selector.clear()
        clients = self.client_service.list_clients()
        for c in clients:
            self.cmb_client_selector.addItem(f"{c.display_name} ({c.client_code})", c)

    def _on_client_changed(self) -> None:
        client = self.cmb_client_selector.currentData()
        self.current_client = client
        self.refresh_entities()

    def refresh_entities(self) -> None:
        self.table_entities.setRowCount(0)
        self.table_members.setRowCount(0)
        self.current_entity = None
        self.btn_add_member.setEnabled(False)
        self.lbl_selected_entity.setText("Members for: <i>Select an entity above</i>")

        if not self.current_client:
            return

        entities = self.entity_service.list_entities_for_client(self.current_client.id)
        for ent in entities:
            row = self.table_entities.rowCount()
            self.table_entities.insertRow(row)

            item = QTableWidgetItem(ent.legal_name)
            item.setData(Qt.UserRole, ent)
            self.table_entities.setItem(row, 0, item)
            self.table_entities.setItem(row, 1, QTableWidgetItem(ent.constitution_code.value))
            self.table_entities.setItem(row, 2, QTableWidgetItem(ent.trade_name or "-"))
            self.table_entities.setItem(row, 3, QTableWidgetItem(ent.created_at.strftime("%Y-%m-%d")))

    def _on_entity_selected(self) -> None:
        items = self.table_entities.selectedItems()
        if not items:
            return
        entity: EntityResponseDTO = self.table_entities.item(items[0].row(), 0).data(Qt.UserRole)
        self.current_entity = entity
        self.lbl_selected_entity.setText(f"Members for: <b>{entity.legal_name}</b> ({entity.constitution_code.value})")
        self.btn_add_member.setEnabled(True)
        self.entity_selected.emit(entity)
        self.refresh_members()

    def refresh_members(self) -> None:
        self.table_members.setRowCount(0)
        if not self.current_entity:
            return

        # Fetch members with decrypted PAN for display
        members = self.entity_service.list_members(self.current_entity.id, decrypt_pan=True)
        for m in members:
            row = self.table_members.rowCount()
            self.table_members.insertRow(row)

            # Masked PAN in table display
            masked_pan = m.pan_encrypted
            if masked_pan and len(masked_pan) >= 5:
                masked_pan = "X" * (len(masked_pan) - 4) + masked_pan[-4:]

            self.table_members.setItem(row, 0, QTableWidgetItem(m.full_name))
            self.table_members.setItem(row, 1, QTableWidgetItem(m.role_code.value))
            self.table_members.setItem(row, 2, QTableWidgetItem(masked_pan or "-"))
            self.table_members.setItem(row, 3, QTableWidgetItem(m.contact_phone or "-"))
            self.table_members.setItem(row, 4, QTableWidgetItem(m.profit_share_pct or m.shareholding_pct or "-"))

    def open_add_entity_dialog(self) -> None:
        if not self.current_client:
            QMessageBox.warning(self, "No Client", "Please create or select a client first.")
            return

        dialog = EntityDialog(self.current_client.id, self)
        if dialog.exec():
            dto = dialog.get_dto()
            try:
                self.entity_service.create_entity(dto)
                self.refresh_entities()
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to save entity: {e}")

    def open_add_member_dialog(self) -> None:
        if not self.current_entity:
            return
        dialog = MemberDialog(self.current_entity.id, self.current_entity.constitution_code, self)
        if dialog.exec():
            dto = dialog.get_dto()
            try:
                self.entity_service.add_member(dto)
                self.refresh_members()
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to add member: {e}")
