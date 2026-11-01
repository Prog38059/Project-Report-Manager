"""Project list and comprehensive Project Inputs workspace view."""

from decimal import Decimal
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
    QDialog,
    QFormLayout,
    QComboBox,
    QFrame,
)

from app.application.dtos.project_dto import ProjectResponseDTO
from app.application.dtos.project_cost_dto import CostItemDTO, CostSummaryDTO
from app.application.dtos.funding_dto import FundingSourceDTO, FundingReconciliationDTO
from app.application.services.project_service import ProjectService
from app.application.services.client_service import ClientService
from app.application.services.entity_service import EntityService
from app.application.services.project_cost_service import ProjectCostService
from app.application.services.funding_service import FundingService
from app.application.services.revenue_service import RevenueService
from app.application.services.expense_service import ExpenseService
from app.application.services.template_service import TemplateService
from app.application.services.historical_service import HistoricalService
from app.common.money import format_inr
from app.presentation.views.project_wizard import ProjectWizardDialog


class AddCostItemDialog(QDialog):
    """Dialog to add a project cost item."""

    def __init__(self, cost_service: ProjectCostService, scenario_id: uuid.UUID, parent=None):
        super().__init__(parent)
        self.cost_service = cost_service
        self.scenario_id = scenario_id
        self.setWindowTitle("Add Project Cost Item")
        self.resize(460, 360)

        layout = QVBoxLayout(self)
        form = QFormLayout()

        self.cmb_head = QComboBox()
        self.heads = self.cost_service.list_cost_heads()
        for h in self.heads:
            self.cmb_head.addItem(f"{h.head_name} ({h.category_code})", h.id)
        form.addRow("Cost Head *:", self.cmb_head)

        self.txt_desc = QLineEdit()
        self.txt_desc.setPlaceholderText("e.g. CNC Milling Machine 5-Axis")
        form.addRow("Description *:", self.txt_desc)

        self.txt_basic = QLineEdit()
        self.txt_basic.setPlaceholderText("e.g. 5000000.00")
        form.addRow("Basic Amount (₹) *:", self.txt_basic)

        self.txt_gst_rate = QLineEdit("18.0")
        form.addRow("GST Rate (%) :", self.txt_gst_rate)

        self.txt_itc_pct = QLineEdit("100.0")
        form.addRow("Eligible ITC (%) :", self.txt_itc_pct)

        self.txt_supplier = QLineEdit()
        form.addRow("Supplier / Vendor :", self.txt_supplier)

        layout.addLayout(form)

        btns = QHBoxLayout()
        btn_cancel = QPushButton("Cancel")
        btn_cancel.clicked.connect(self.reject)
        btn_save = QPushButton("Save Item")
        btn_save.setStyleSheet("background-color: #1a73e8; color: white; font-weight: bold;")
        btn_save.clicked.connect(self._save)
        btns.addStretch()
        btns.addWidget(btn_cancel)
        btns.addWidget(btn_save)
        layout.addLayout(btns)

    def _save(self):
        desc = self.txt_desc.text().strip()
        if not desc:
            QMessageBox.warning(self, "Validation", "Description is required.")
            return
        try:
            basic = Decimal(self.txt_basic.text().strip())
            gst_rate = Decimal(self.txt_gst_rate.text().strip()) if self.txt_gst_rate.text().strip() else None
            itc_pct = Decimal(self.txt_itc_pct.text().strip()) if self.txt_itc_pct.text().strip() else None
        except Exception:
            QMessageBox.warning(self, "Validation", "Amounts and rates must be valid numbers.")
            return

        head_id = self.cmb_head.currentData()
        self.cost_service.save_item(
            scenario_id=self.scenario_id,
            cost_head_id=head_id,
            description=desc,
            basic_rupees=basic,
            gst_rate_pct=gst_rate,
            itc_eligibility_pct=itc_pct,
            supplier_name=self.txt_supplier.text().strip() or None,
        )
        self.accept()


class AddFundingSourceDialog(QDialog):
    """Dialog to add a funding source line."""

    def __init__(self, funding_service: FundingService, scenario_id: uuid.UUID, parent=None):
        super().__init__(parent)
        self.funding_service = funding_service
        self.scenario_id = scenario_id
        self.setWindowTitle("Add Means of Finance (Funding Source)")
        self.resize(450, 300)

        layout = QVBoxLayout(self)
        form = QFormLayout()

        self.cmb_head = QComboBox()
        self.heads = self.funding_service.list_funding_heads()
        for h in self.heads:
            self.cmb_head.addItem(f"{h.funding_name} ({h.funding_category})", h.id)
        form.addRow("Funding Head *:", self.cmb_head)

        self.txt_name = QLineEdit()
        self.txt_name.setPlaceholderText("e.g. Promoter Equity Contribution / SBI Term Loan")
        form.addRow("Source Name *:", self.txt_name)

        self.txt_amount = QLineEdit()
        self.txt_amount.setPlaceholderText("e.g. 2500000.00")
        form.addRow("Amount (₹) *:", self.txt_amount)

        self.cmb_status = QComboBox()
        self.cmb_status.addItems(["PROPOSED", "COMMITTED", "RECEIVED"])
        form.addRow("Status :", self.cmb_status)

        layout.addLayout(form)

        btns = QHBoxLayout()
        btn_cancel = QPushButton("Cancel")
        btn_cancel.clicked.connect(self.reject)
        btn_save = QPushButton("Save Source")
        btn_save.setStyleSheet("background-color: #1a73e8; color: white; font-weight: bold;")
        btn_save.clicked.connect(self._save)
        btns.addStretch()
        btns.addWidget(btn_cancel)
        btns.addWidget(btn_save)
        layout.addLayout(btns)

    def _save(self):
        name = self.txt_name.text().strip()
        if not name:
            QMessageBox.warning(self, "Validation", "Source name is required.")
            return
        try:
            amt = Decimal(self.txt_amount.text().strip())
        except Exception:
            QMessageBox.warning(self, "Validation", "Amount must be a valid number.")
            return

        head_id = self.cmb_head.currentData()
        self.funding_service.save_source(
            scenario_id=self.scenario_id,
            funding_head_id=head_id,
            source_name=name,
            amount_rupees=amt,
            status_code=self.cmb_status.currentText(),
        )
        self.accept()


class ProjectView(QWidget):
    """View managing projects, 7-year projection horizon, and Phase 2 project input workspaces."""

    project_selected = Signal(object)  # Emits ProjectResponseDTO

    def __init__(
        self,
        client_service: ClientService,
        entity_service: EntityService,
        project_service: ProjectService,
        project_cost_service: Optional[ProjectCostService] = None,
        funding_service: Optional[FundingService] = None,
        revenue_service: Optional[RevenueService] = None,
        expense_service: Optional[ExpenseService] = None,
        template_service: Optional[TemplateService] = None,
        historical_service: Optional[HistoricalService] = None,
        parent: Optional[QWidget] = None,
    ) -> None:
        super().__init__(parent)
        self.client_service = client_service
        self.entity_service = entity_service
        self.project_service = project_service
        self.project_cost_service = project_cost_service
        self.funding_service = funding_service
        self.revenue_service = revenue_service
        self.expense_service = expense_service
        self.template_service = template_service
        self.historical_service = historical_service

        self.current_project: Optional[ProjectResponseDTO] = None
        self.current_scenario_id: Optional[uuid.UUID] = None

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(14)

        # Header bar
        header = QHBoxLayout()
        title = QLabel("Projects & Inputs Workspace")
        title.setStyleSheet("font-size: 20px; font-weight: bold; color: #202124;")
        header.addWidget(title)
        header.addStretch()

        btn_new_wizard = QPushButton("🚀 New Project Wizard")
        btn_new_wizard.setStyleSheet("background-color: #1a73e8; color: white; padding: 6px 14px; font-weight: bold;")
        btn_new_wizard.clicked.connect(self.open_wizard)
        header.addWidget(btn_new_wizard)
        layout.addLayout(header)

        # Splitter: Left Project List, Right Details & Workspaces
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

        # Right Panel: Tabs for Inputs and Projections
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)
        right_layout.setContentsMargins(0, 0, 0, 0)

        self.lbl_selected_title = QLabel("Select a project to inspect inputs and projections")
        self.lbl_selected_title.setStyleSheet("font-size: 14px; font-weight: bold; color: #3c4043;")
        right_layout.addWidget(self.lbl_selected_title)

        self.tabs = QTabWidget()

        # Tab 1: Projection Periods (Dynamic)
        tab_periods = QWidget()
        tab_per_layout = QVBoxLayout(tab_periods)
        self.table_periods = QTableWidget(0, 5)
        self.table_periods.setHorizontalHeaderLabels(["Seq", "Period Label", "FY Label", "Start Date", "End Date"])
        self.table_periods.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table_periods.setSelectionBehavior(QTableWidget.SelectRows)
        self.table_periods.setEditTriggers(QTableWidget.NoEditTriggers)
        tab_per_layout.addWidget(self.table_periods)
        self.tabs.addTab(tab_periods, "📅 Projection Periods")

        # Tab 2: Project Cost
        self.tab_cost = QWidget()
        tab_cost_layout = QVBoxLayout(self.tab_cost)
        cost_bar = QHBoxLayout()
        self.btn_add_cost = QPushButton("➕ Add Cost Item")
        self.btn_add_cost.clicked.connect(self._on_add_cost_item)
        cost_bar.addWidget(self.btn_add_cost)
        cost_bar.addStretch()
        self.lbl_cost_summary = QLabel("Total Cost: ₹0.00 | Cash Outflow: ₹0.00")
        self.lbl_cost_summary.setStyleSheet("font-weight: bold; color: #1a73e8;")
        cost_bar.addWidget(self.lbl_cost_summary)
        tab_cost_layout.addLayout(cost_bar)

        self.table_cost = QTableWidget(0, 7)
        self.table_cost.setHorizontalHeaderLabels([
            "Head", "Description", "Basic (₹)", "GST %", "Eligible ITC (₹)", "Capitalised (₹)", "Cash Req (₹)"
        ])
        self.table_cost.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table_cost.setSelectionBehavior(QTableWidget.SelectRows)
        self.table_cost.setEditTriggers(QTableWidget.NoEditTriggers)
        tab_cost_layout.addWidget(self.table_cost)
        self.tabs.addTab(self.tab_cost, "🏗 Project Cost")

        # Tab 3: Means of Finance (Funding)
        self.tab_funding = QWidget()
        tab_fund_layout = QVBoxLayout(self.tab_funding)
        fund_bar = QHBoxLayout()
        self.btn_add_funding = QPushButton("➕ Add Funding Source")
        self.btn_add_funding.clicked.connect(self._on_add_funding_source)
        fund_bar.addWidget(self.btn_add_funding)
        fund_bar.addStretch()

        self.lbl_funding_recon = QLabel("Reconciliation: N/A")
        self.lbl_funding_recon.setStyleSheet("font-weight: bold; padding: 4px 8px; border-radius: 4px;")
        fund_bar.addWidget(self.lbl_funding_recon)
        tab_fund_layout.addLayout(fund_bar)

        self.table_funding = QTableWidget(0, 4)
        self.table_funding.setHorizontalHeaderLabels(["Funding Head", "Source Name", "Amount (₹)", "Status"])
        self.table_funding.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table_funding.setSelectionBehavior(QTableWidget.SelectRows)
        self.table_funding.setEditTriggers(QTableWidget.NoEditTriggers)
        tab_fund_layout.addWidget(self.table_funding)
        self.tabs.addTab(self.tab_funding, "💰 Means of Finance")

        # Tab 4: Revenue Streams
        self.tab_revenue = QWidget()
        tab_rev_layout = QVBoxLayout(self.tab_revenue)
        self.table_revenue = QTableWidget(0, 5)
        self.table_revenue.setHorizontalHeaderLabels(["Code", "Stream Name", "Method", "GST Treatment", "Rate %"])
        self.table_revenue.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table_revenue.setSelectionBehavior(QTableWidget.SelectRows)
        self.table_revenue.setEditTriggers(QTableWidget.NoEditTriggers)
        tab_rev_layout.addWidget(self.table_revenue)
        self.tabs.addTab(self.tab_revenue, "📈 Revenue Streams")

        # Tab 5: Expense Heads
        self.tab_expense = QWidget()
        tab_exp_layout = QVBoxLayout(self.tab_expense)
        self.table_expense = QTableWidget(0, 5)
        self.table_expense.setHorizontalHeaderLabels(["Code", "Expense Head", "Group", "Cost Behaviour", "Method"])
        self.table_expense.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table_expense.setSelectionBehavior(QTableWidget.SelectRows)
        self.table_expense.setEditTriggers(QTableWidget.NoEditTriggers)
        tab_exp_layout.addWidget(self.table_expense)
        self.tabs.addTab(self.tab_expense, "📉 Operating Expenses")

        # Tab 6: Historical Statements (Hidden by default!)
        self.tab_historical = QWidget()
        tab_hist_layout = QVBoxLayout(self.tab_historical)
        self.table_historical = QTableWidget(0, 5)
        self.table_historical.setHorizontalHeaderLabels(["Statement", "Period", "Line Code", "Line Label", "Amount (₹)"])
        self.table_historical.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table_historical.setSelectionBehavior(QTableWidget.SelectRows)
        self.table_historical.setEditTriggers(QTableWidget.NoEditTriggers)
        tab_hist_layout.addWidget(self.table_historical)

        # Scenarios Tab
        tab_scenarios = QWidget()
        tab_scen_layout = QVBoxLayout(tab_scenarios)
        self.table_scenarios = QTableWidget(0, 4)
        self.table_scenarios.setHorizontalHeaderLabels(["Code", "Name", "Type", "Default"])
        self.table_scenarios.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table_scenarios.setSelectionBehavior(QTableWidget.SelectRows)
        self.table_scenarios.setEditTriggers(QTableWidget.NoEditTriggers)
        tab_scen_layout.addWidget(self.table_scenarios)
        self.tabs.addTab(tab_scenarios, "⚙ Scenarios")

        right_layout.addWidget(self.tabs)

        splitter.addWidget(left_panel)
        splitter.addWidget(right_panel)
        splitter.setStretchFactor(0, 3)
        splitter.setStretchFactor(1, 7)
        layout.addWidget(splitter)

        self.refresh()

    def refresh(self) -> None:
        self.table_projects.setRowCount(0)
        self.table_periods.setRowCount(0)
        self.table_cost.setRowCount(0)
        self.table_funding.setRowCount(0)
        self.table_revenue.setRowCount(0)
        self.table_expense.setRowCount(0)
        self.table_historical.setRowCount(0)
        self.table_scenarios.setRowCount(0)
        self.current_project = None
        self.current_scenario_id = None
        self.lbl_selected_title.setText("Select a project to inspect inputs and projections")

        # Ensure historical tab is not visible initially
        idx = self.tabs.indexOf(self.tab_historical)
        if idx != -1:
            self.tabs.removeTab(idx)

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

        # Get default scenario
        scenarios = self.project_service.list_scenarios(project.id)
        default_scen = next((s for s in scenarios if s.is_default), scenarios[0] if scenarios else None)
        self.current_scenario_id = default_scen.id if default_scen else None

        # Manage Historical tab visibility per ADR-003 and spec:
        # Strictly hidden unless historical_data_enabled == True
        idx = self.tabs.indexOf(self.tab_historical)
        if project.historical_data_enabled:
            if idx == -1:
                self.tabs.addTab(self.tab_historical, "📜 Historical Statements")
            self.refresh_historical()
        else:
            if idx != -1:
                self.tabs.removeTab(idx)

        self.refresh_periods()
        self.refresh_scenarios()
        self.refresh_costs()
        self.refresh_funding()
        self.refresh_revenue()
        self.refresh_expenses()

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

    def refresh_costs(self) -> None:
        self.table_cost.setRowCount(0)
        if not self.project_cost_service or not self.current_scenario_id:
            return
        items = self.project_cost_service.list_items(self.current_scenario_id)
        summary = self.project_cost_service.get_cost_summary(self.current_scenario_id)
        self.lbl_cost_summary.setText(
            f"Total Capitalised: {format_inr(summary.total_capitalised_rupees)} | Gross Cash Outflow: {format_inr(summary.total_cash_requirement_rupees)}"
        )

        for i in items:
            row = self.table_cost.rowCount()
            self.table_cost.insertRow(row)
            self.table_cost.setItem(row, 0, QTableWidgetItem(i.cost_head_name))
            self.table_cost.setItem(row, 1, QTableWidgetItem(i.description))
            self.table_cost.setItem(row, 2, QTableWidgetItem(format_inr(i.basic_amount_rupees)))
            self.table_cost.setItem(row, 3, QTableWidgetItem(f"{i.gst_rate_pct}%" if i.gst_rate_pct else "0%"))
            self.table_cost.setItem(row, 4, QTableWidgetItem(format_inr(i.eligible_itc_rupees)))
            self.table_cost.setItem(row, 5, QTableWidgetItem(format_inr(i.capitalised_amount_rupees)))
            self.table_cost.setItem(row, 6, QTableWidgetItem(format_inr(i.project_cash_requirement_rupees)))

    def refresh_funding(self) -> None:
        self.table_funding.setRowCount(0)
        if not self.funding_service or not self.current_scenario_id:
            return
        sources = self.funding_service.list_sources(self.current_scenario_id)
        for s in sources:
            row = self.table_funding.rowCount()
            self.table_funding.insertRow(row)
            self.table_funding.setItem(row, 0, QTableWidgetItem(s.funding_head_name))
            self.table_funding.setItem(row, 1, QTableWidgetItem(s.source_name))
            self.table_funding.setItem(row, 2, QTableWidgetItem(format_inr(s.amount_rupees)))
            self.table_funding.setItem(row, 3, QTableWidgetItem(s.status_code))

        # Reconcile against total cash requirement
        if self.project_cost_service:
            cost_summary = self.project_cost_service.get_cost_summary(self.current_scenario_id)
            recon = self.funding_service.get_reconciliation(self.current_scenario_id, cost_summary.total_cash_requirement_rupees)
            if recon.is_balanced:
                self.lbl_funding_recon.setText(f"✓ Balanced: Total Uses = Total Sources = {format_inr(recon.total_funding_sources_rupees)} (D/E: {recon.debt_equity_ratio})")
                self.lbl_funding_recon.setStyleSheet("background-color: #e6f4ea; color: #137333; font-weight: bold; padding: 4px 8px; border-radius: 4px;")
            elif recon.funding_gap_rupees > Decimal("0"):
                self.lbl_funding_recon.setText(f"⚠ Unfunded Gap: {format_inr(recon.funding_gap_rupees)} deficit (Total Uses: {format_inr(recon.total_project_cost_rupees)})")
                self.lbl_funding_recon.setStyleSheet("background-color: #fce8e6; color: #c5221f; font-weight: bold; padding: 4px 8px; border-radius: 4px;")
            else:
                self.lbl_funding_recon.setText(f"ℹ Funding Surplus: {format_inr(abs(recon.funding_gap_rupees))} (Total Sources: {format_inr(recon.total_funding_sources_rupees)})")
                self.lbl_funding_recon.setStyleSheet("background-color: #fef7e0; color: #b06000; font-weight: bold; padding: 4px 8px; border-radius: 4px;")

    def refresh_revenue(self) -> None:
        self.table_revenue.setRowCount(0)
        if not self.revenue_service or not self.current_scenario_id:
            return
        streams = self.revenue_service.list_streams(self.current_scenario_id)
        for s in streams:
            row = self.table_revenue.rowCount()
            self.table_revenue.insertRow(row)
            self.table_revenue.setItem(row, 0, QTableWidgetItem(s.stream_code))
            self.table_revenue.setItem(row, 1, QTableWidgetItem(s.stream_name))
            self.table_revenue.setItem(row, 2, QTableWidgetItem(s.method_code))
            self.table_revenue.setItem(row, 3, QTableWidgetItem(s.gst_treatment_code))
            self.table_revenue.setItem(row, 4, QTableWidgetItem(f"{s.gst_rate_pct}%" if s.gst_rate_pct else "0%"))

    def refresh_expenses(self) -> None:
        self.table_expense.setRowCount(0)
        if not self.expense_service:
            return
        heads = self.expense_service.list_expense_heads()
        for h in heads:
            row = self.table_expense.rowCount()
            self.table_expense.insertRow(row)
            self.table_expense.setItem(row, 0, QTableWidgetItem(h.expense_code))
            self.table_expense.setItem(row, 1, QTableWidgetItem(h.expense_name))
            self.table_expense.setItem(row, 2, QTableWidgetItem(h.expense_group))
            self.table_expense.setItem(row, 3, QTableWidgetItem(h.default_cost_behaviour))
            self.table_expense.setItem(row, 4, QTableWidgetItem(h.default_projection_method))

    def refresh_historical(self) -> None:
        self.table_historical.setRowCount(0)
        if not self.historical_service or not self.current_project:
            return
        lines = self.historical_service.list_lines(self.current_project.id)
        for l in lines:
            row = self.table_historical.rowCount()
            self.table_historical.insertRow(row)
            self.table_historical.setItem(row, 0, QTableWidgetItem(l.statement_type))
            self.table_historical.setItem(row, 1, QTableWidgetItem(l.period_label))
            self.table_historical.setItem(row, 2, QTableWidgetItem(l.line_code))
            self.table_historical.setItem(row, 3, QTableWidgetItem(l.line_label))
            self.table_historical.setItem(row, 4, QTableWidgetItem(format_inr(l.amount_rupees)))

    def _on_add_cost_item(self) -> None:
        if not self.current_scenario_id or not self.project_cost_service:
            QMessageBox.information(self, "Select Project", "Please select a project first.")
            return
        dlg = AddCostItemDialog(self.project_cost_service, self.current_scenario_id, self)
        if dlg.exec():
            self.refresh_costs()
            self.refresh_funding()

    def _on_add_funding_source(self) -> None:
        if not self.current_scenario_id or not self.funding_service:
            QMessageBox.information(self, "Select Project", "Please select a project first.")
            return
        dlg = AddFundingSourceDialog(self.funding_service, self.current_scenario_id, self)
        if dlg.exec():
            self.refresh_funding()

    def open_wizard(self) -> None:
        wizard = ProjectWizardDialog(self.client_service, self.entity_service, self.project_service, self)
        if wizard.exec():
            self.refresh()
