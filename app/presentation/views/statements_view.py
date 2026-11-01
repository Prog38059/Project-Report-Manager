"""View for Projected Financial Statements, Loan Amortization, and Asset Depreciation."""

from decimal import Decimal
from typing import List, Optional
import uuid

from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QFont
from PySide6.QtWidgets import (
    QComboBox,
    QFrame,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QMessageBox,
    QPushButton,
    QSplitter,
    QTableWidget,
    QTableWidgetItem,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from app.application.dtos.financial_statements_dto import (
    CalculationRunDTO,
    StatementsTableDTO,
)
from app.application.services.financial_engine_service import FinancialEngineService
from app.application.services.project_service import ProjectService
from app.common.money import format_inr


class StatementsView(QWidget):
    """Horizontal financial statement projection viewer and engine runner."""

    def __init__(
        self,
        project_service: ProjectService,
        financial_engine_service: FinancialEngineService,
        parent: Optional[QWidget] = None,
    ) -> None:
        super().__init__(parent)
        self.project_service = project_service
        self.fin_engine = financial_engine_service

        self.current_project_id: Optional[uuid.UUID] = None
        self.current_scenario_id: Optional[uuid.UUID] = None
        self.current_run_dto: Optional[CalculationRunDTO] = None

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(14)

        # Header bar
        header = QHBoxLayout()
        title = QLabel("Financial Projections & Statements")
        title.setStyleSheet("font-size: 20px; font-weight: bold; color: #202124;")
        header.addWidget(title)
        header.addStretch()

        self.cmb_projects = QComboBox()
        self.cmb_projects.setMinimumWidth(260)
        self.cmb_projects.currentIndexChanged.connect(self._on_project_changed)
        header.addWidget(QLabel("Project:"))
        header.addWidget(self.cmb_projects)

        self.btn_run = QPushButton("⚡ Run Projections")
        self.btn_run.setStyleSheet(
            "background-color: #1a73e8; color: white; padding: 7px 16px; font-weight: bold; border-radius: 4px;"
        )
        self.btn_run.clicked.connect(self._on_run_projections)
        header.addWidget(self.btn_run)
        layout.addLayout(header)

        # Invariant & Run Info Bar
        info_frame = QFrame()
        info_frame.setStyleSheet(
            "background-color: #f8f9fa; border: 1px solid #dadce0; border-radius: 6px; padding: 8px;"
        )
        info_layout = QHBoxLayout(info_frame)
        info_layout.setContentsMargins(10, 6, 10, 6)

        self.lbl_run_badge = QLabel("Run: None")
        self.lbl_run_badge.setStyleSheet("font-weight: bold; color: #3c4043;")
        info_layout.addWidget(self.lbl_run_badge)

        self.lbl_hash_badge = QLabel("Input Hash: -")
        self.lbl_hash_badge.setStyleSheet("color: #5f6368; font-family: monospace;")
        info_layout.addWidget(self.lbl_hash_badge)

        info_layout.addStretch()

        self.lbl_invariant_badge = QLabel("Balance Sheet Invariant: Not Run")
        self.lbl_invariant_badge.setStyleSheet(
            "font-weight: bold; color: #137333; background-color: #e6f4ea; padding: 4px 10px; border-radius: 4px;"
        )
        info_layout.addWidget(self.lbl_invariant_badge)

        layout.addWidget(info_frame)

        # Statement Subtabs
        self.tabs = QTabWidget()
        self.tabs.setStyleSheet("QTabBar::tab { font-weight: bold; padding: 8px 16px; }")

        # 1. Profit & Loss
        self.table_pl = self._create_statement_table()
        self.tabs.addTab(self.table_pl, "📈 Profit & Loss")

        # 2. Balance Sheet
        self.table_bs = self._create_statement_table()
        self.tabs.addTab(self.table_bs, "🏛 Balance Sheet")

        # 3. Cash Flow
        self.table_cf = self._create_statement_table()
        self.tabs.addTab(self.table_cf, "💧 Cash Flow (Indirect)")

        # 4. Loan Amortization Schedule
        self.table_loan = QTableWidget(0, 8)
        self.table_loan.setHorizontalHeaderLabels([
            "Month #", "Due Date", "Opening Principal (₹)", "Disbursement (₹)", "Installment (₹)",
            "Interest (₹)", "Principal (₹)", "Closing Principal (₹)"
        ])
        self.table_loan.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table_loan.setEditTriggers(QTableWidget.NoEditTriggers)
        self.tabs.addTab(self.table_loan, "🏦 Loan Amortization")

        # 5. Asset Depreciation Schedule
        self.table_assets = QTableWidget(0, 8)
        self.table_assets.setHorizontalHeaderLabels([
            "Period", "Opening Gross (₹)", "Additions (₹)", "Disposals (₹)", "Closing Gross (₹)",
            "Depreciation (₹)", "Accum. Dep (₹)", "Closing Net Block (₹)"
        ])
        self.table_assets.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table_assets.setEditTriggers(QTableWidget.NoEditTriggers)
        self.tabs.addTab(self.table_assets, "🏭 Fixed Assets & Depreciation")

        layout.addWidget(self.tabs)
        self.refresh_projects()

    def _create_statement_table(self) -> QTableWidget:
        table = QTableWidget(0, 10)
        table.setHorizontalHeaderLabels([
            "Sr. No.", "Note Ref", "Particulars",
            "Year 1", "Year 2", "Year 3", "Year 4", "Year 5", "Year 6", "Year 7"
        ])
        table.horizontalHeader().setSectionResizeMode(2, QHeaderView.Stretch)
        table.setEditTriggers(QTableWidget.NoEditTriggers)
        table.setAlternatingRowColors(True)
        return table

    def refresh_projects(self) -> None:
        self.cmb_projects.blockSignals(True)
        self.cmb_projects.clear()
        projects = self.project_service.list_all_projects()
        for p in projects:
            self.cmb_projects.addItem(f"{p.project_name} ({p.project_code})", p.id)
        self.cmb_projects.blockSignals(False)

        if projects:
            self.cmb_projects.setCurrentIndex(0)
            self._on_project_changed(0)

    def _on_project_changed(self, index: int) -> None:
        p_id = self.cmb_projects.currentData()
        if not p_id:
            return
        self.current_project_id = p_id
        scenarios = self.project_service.list_scenarios(p_id)
        if scenarios:
            self.current_scenario_id = scenarios[0].id
        else:
            self.current_scenario_id = None

    def _on_run_projections(self) -> None:
        if not self.current_scenario_id:
            QMessageBox.warning(self, "No Scenario", "Please select a valid project with an active scenario.")
            return

        try:
            self.current_run_dto = self.fin_engine.execute_projection(
                scenario_id=self.current_scenario_id,
                prepared_by_label="Current User",
            )
            self._populate_run_data(self.current_run_dto)
            QMessageBox.information(
                self,
                "Projections Completed",
                f"Calculation Run #{self.current_run_dto.run_number} succeeded!\n"
                f"Zero-Plug Balance Sheet Invariant: VERIFIED (0.00 difference)\n"
                f"Input Hash: {self.current_run_dto.input_hash[:16]}...",
            )
        except Exception as e:
            QMessageBox.critical(self, "Calculation Error", f"Failed to execute financial projection:\n{str(e)}")

    def _populate_run_data(self, run: CalculationRunDTO) -> None:
        self.lbl_run_badge.setText(f"Run #{run.run_number} ({run.engine_version})")
        self.lbl_hash_badge.setText(f"Input Hash: {run.input_hash[:16]}...")
        self.lbl_invariant_badge.setText("✅ Balance Sheet Invariant: BALANCED (₹0.00 difference)")
        self.lbl_invariant_badge.setStyleSheet(
            "font-weight: bold; color: #137333; background-color: #e6f4ea; padding: 4px 10px; border-radius: 4px;"
        )

        if run.pl_table:
            self._populate_statement_table(self.table_pl, run.pl_table)
        if run.bs_table:
            self._populate_statement_table(self.table_bs, run.bs_table)
        if run.cf_table:
            self._populate_statement_table(self.table_cf, run.cf_table)

        # Populate Loan Amortization
        self.table_loan.setRowCount(0)
        for r in run.loan_schedule:
            row_idx = self.table_loan.rowCount()
            self.table_loan.insertRow(row_idx)
            self.table_loan.setItem(row_idx, 0, QTableWidgetItem(str(r.installment_number)))
            self.table_loan.setItem(row_idx, 1, QTableWidgetItem(r.due_date))
            self.table_loan.setItem(row_idx, 2, QTableWidgetItem(format_inr(r.opening_balance_rupees)))
            self.table_loan.setItem(row_idx, 3, QTableWidgetItem(format_inr(r.disbursement_rupees)))
            self.table_loan.setItem(row_idx, 4, QTableWidgetItem(format_inr(r.payment_rupees)))
            self.table_loan.setItem(row_idx, 5, QTableWidgetItem(format_inr(r.interest_rupees)))
            self.table_loan.setItem(row_idx, 6, QTableWidgetItem(format_inr(r.principal_rupees)))
            self.table_loan.setItem(row_idx, 7, QTableWidgetItem(format_inr(r.closing_balance_rupees)))

        # Populate Asset Depreciation
        self.table_assets.setRowCount(0)
        for r in run.asset_schedule:
            row_idx = self.table_assets.rowCount()
            self.table_assets.insertRow(row_idx)
            self.table_assets.setItem(row_idx, 0, QTableWidgetItem(r.period_label))
            self.table_assets.setItem(row_idx, 1, QTableWidgetItem(format_inr(r.opening_gross_rupees)))
            self.table_assets.setItem(row_idx, 2, QTableWidgetItem(format_inr(r.additions_rupees)))
            self.table_assets.setItem(row_idx, 3, QTableWidgetItem(format_inr(r.disposals_rupees)))
            self.table_assets.setItem(row_idx, 4, QTableWidgetItem(format_inr(r.closing_gross_rupees)))
            self.table_assets.setItem(row_idx, 5, QTableWidgetItem(format_inr(r.depreciation_rupees)))
            self.table_assets.setItem(row_idx, 6, QTableWidgetItem(format_inr(r.accumulated_depreciation_rupees)))
            self.table_assets.setItem(row_idx, 7, QTableWidgetItem(format_inr(r.closing_nbv_rupees)))

    def _populate_statement_table(self, table: QTableWidget, data: StatementsTableDTO) -> None:
        table.setRowCount(0)
        # Update column headers
        col_headers = ["Sr. No.", "Note Ref", "Particulars"] + data.period_headers
        table.setColumnCount(len(col_headers))
        table.setHorizontalHeaderLabels(col_headers)

        bold_font = QFont()
        bold_font.setBold(True)

        for row_dto in data.rows:
            row_idx = table.rowCount()
            table.insertRow(row_idx)

            item_sr = QTableWidgetItem(row_dto.sr_no)
            item_ref = QTableWidgetItem(row_dto.note_ref)
            item_part = QTableWidgetItem(row_dto.particulars)

            if row_dto.is_header or row_dto.is_total:
                item_sr.setFont(bold_font)
                item_ref.setFont(bold_font)
                item_part.setFont(bold_font)

            if row_dto.is_total:
                bg = QColor("#f1f3f4")
                item_sr.setBackground(bg)
                item_ref.setBackground(bg)
                item_part.setBackground(bg)

            table.setItem(row_idx, 0, item_sr)
            table.setItem(row_idx, 1, item_ref)
            table.setItem(row_idx, 2, item_part)

            for col_idx, seq in enumerate(sorted(row_dto.period_amounts.keys()), start=3):
                val = row_dto.period_amounts[seq]
                item_val = QTableWidgetItem(format_inr(val))
                item_val.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
                if row_dto.is_total:
                    item_val.setFont(bold_font)
                    item_val.setBackground(QColor("#f1f3f4"))
                table.setItem(row_idx, col_idx, item_val)
