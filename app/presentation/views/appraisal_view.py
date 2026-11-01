"""Desktop GUI View for Lender Appraisal, Financial Ratios, Break-Even, Sensitivity, and Cross-Statement Validation."""

from decimal import Decimal
from typing import Dict, List, Optional
import uuid

from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QFont
from PySide6.QtWidgets import (
    QComboBox,
    QFrame,
    QGridLayout,
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

from app.application.dtos.appraisal_dto import (
    AppraisalReportDTO,
    ProjectLifetimeReturnsDTO,
    RatioMetricRowDTO,
    SensitivityRowDTO,
    ValidationIssueDTO,
)
from app.application.services.appraisal_service import AppraisalService
from app.application.services.project_service import ProjectService
from app.common.money import format_inr


class AppraisalView(QWidget):
    """Interactive GUI for appraisal metrics, ratio analysis, sensitivity matrix, and validation audit."""

    def __init__(
        self,
        project_service: ProjectService,
        appraisal_service: AppraisalService,
        parent: Optional[QWidget] = None,
    ) -> None:
        super().__init__(parent)
        self.project_service = project_service
        self.appraisal_service = appraisal_service

        self.current_project_id: Optional[uuid.UUID] = None
        self.current_scenario_id: Optional[uuid.UUID] = None
        self.current_report: Optional[AppraisalReportDTO] = None

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(14)

        # Header Bar
        header = QHBoxLayout()
        title = QLabel("Lender Appraisal & Cross-Statement Validation")
        title.setStyleSheet("font-size: 20px; font-weight: bold; color: #202124;")
        header.addWidget(title)
        header.addStretch()

        self.cmb_projects = QComboBox()
        self.cmb_projects.setMinimumWidth(260)
        self.cmb_projects.currentIndexChanged.connect(self._on_project_changed)
        header.addWidget(QLabel("Project:"))
        header.addWidget(self.cmb_projects)

        self.btn_evaluate = QPushButton("⚡ Evaluate Appraisal")
        self.btn_evaluate.setStyleSheet(
            "background-color: #1a73e8; color: white; padding: 7px 16px; font-weight: bold; border-radius: 4px;"
        )
        self.btn_evaluate.clicked.connect(self._on_evaluate_appraisal)
        header.addWidget(self.btn_evaluate)
        layout.addLayout(header)

        # Top KPI Summary Cards
        kpi_layout = QHBoxLayout()
        kpi_layout.setSpacing(12)

        self.card_returns = self._create_kpi_card("Project Returns", "NPV: - | IRR: -", "Payback: -")
        self.card_dscr = self._create_kpi_card("Lender DSCR Coverage", "Gross DSCR: -", "CFADS DSCR: -")
        self.card_solvency = self._create_kpi_card("Solvency & Liquidity", "Current Ratio: -", "Debt-Equity: -")
        self.card_audit = self._create_kpi_card("Audit Integrity", "Status: Not Evaluated", "Errors: 0 | Warnings: 0")

        kpi_layout.addWidget(self.card_returns)
        kpi_layout.addWidget(self.card_dscr)
        kpi_layout.addWidget(self.card_solvency)
        kpi_layout.addWidget(self.card_audit)
        layout.addLayout(kpi_layout)

        # Sub-tabs for Details
        self.tabs = QTabWidget()
        self.tabs.setStyleSheet("""
            QTabBar::tab {
                font-weight: bold;
                padding: 8px 16px;
                font-size: 13px;
            }
            QTabBar::tab:selected {
                color: #1a73e8;
                border-bottom: 2px solid #1a73e8;
            }
        """)

        # Tab 1: Financial Ratios
        self.tab_ratios = QWidget()
        ratios_layout = QVBoxLayout(self.tab_ratios)
        self.tbl_ratios = QTableWidget()
        self._format_table(self.tbl_ratios)
        ratios_layout.addWidget(self.tbl_ratios)
        self.tabs.addTab(self.tab_ratios, "📊 Financial Ratios & DSCR")

        # Tab 2: Break-Even Analysis
        self.tab_bep = QWidget()
        bep_layout = QVBoxLayout(self.tab_bep)
        self.tbl_bep = QTableWidget()
        self._format_table(self.tbl_bep)
        bep_layout.addWidget(self.tbl_bep)
        self.tabs.addTab(self.tab_bep, "🎯 Break-Even Analysis")

        # Tab 3: Sensitivity Matrix
        self.tab_sensitivity = QWidget()
        sens_layout = QVBoxLayout(self.tab_sensitivity)
        self.tbl_sensitivity = QTableWidget()
        self._format_table(self.tbl_sensitivity)
        sens_layout.addWidget(self.tbl_sensitivity)
        self.tabs.addTab(self.tab_sensitivity, "🔀 Sensitivity Matrix")

        # Tab 4: Audit & Cross-Statement Validation
        self.tab_validation = QWidget()
        val_layout = QVBoxLayout(self.tab_validation)

        self.lbl_val_banner = QLabel("Select a project and click 'Evaluate Appraisal' to audit statements.")
        self.lbl_val_banner.setStyleSheet(
            "background-color: #f1f3f4; color: #3c4043; padding: 10px; font-weight: bold; border-radius: 4px;"
        )
        val_layout.addWidget(self.lbl_val_banner)

        self.tbl_validation = QTableWidget()
        self._format_table(self.tbl_validation)
        val_layout.addWidget(self.tbl_validation)
        self.tabs.addTab(self.tab_validation, "🛡️ Audit & Invariant Rules")

        layout.addWidget(self.tabs)

    def _create_kpi_card(self, title: str, line1: str, line2: str) -> QFrame:
        frame = QFrame()
        frame.setStyleSheet("""
            QFrame {
                background-color: #ffffff;
                border: 1px solid #dadce0;
                border-radius: 6px;
                padding: 10px;
            }
        """)
        vbox = QVBoxLayout(frame)
        vbox.setContentsMargins(10, 8, 10, 8)
        vbox.setSpacing(4)

        lbl_title = QLabel(title)
        lbl_title.setStyleSheet("font-size: 11px; font-weight: bold; color: #5f6368; text-transform: uppercase;")
        lbl_line1 = QLabel(line1)
        lbl_line1.setStyleSheet("font-size: 14px; font-weight: bold; color: #202124;")
        lbl_line2 = QLabel(line2)
        lbl_line2.setStyleSheet("font-size: 12px; color: #70757a;")

        vbox.addWidget(lbl_title)
        vbox.addWidget(lbl_line1)
        vbox.addWidget(lbl_line2)

        # Store references to labels
        frame.lbl_title = lbl_title  # type: ignore
        frame.lbl_line1 = lbl_line1  # type: ignore
        frame.lbl_line2 = lbl_line2  # type: ignore
        return frame

    def _format_table(self, table: QTableWidget) -> None:
        table.setAlternatingRowColors(True)
        table.setSelectionBehavior(QTableWidget.SelectRows)
        table.verticalHeader().setVisible(False)
        table.horizontalHeader().setStretchLastSection(True)
        table.setStyleSheet("""
            QTableWidget {
                background-color: #ffffff;
                alternate-background-color: #f8f9fa;
                gridline-color: #dadce0;
                border: 1px solid #dadce0;
                font-size: 12px;
            }
            QHeaderView::section {
                background-color: #f1f3f4;
                color: #202124;
                font-weight: bold;
                padding: 6px;
                border: 1px solid #dadce0;
            }
        """)

    def refresh_projects_list(self) -> None:
        self.cmb_projects.blockSignals(True)
        self.cmb_projects.clear()
        projects = self.project_service.list_projects()
        for p in projects:
            self.cmb_projects.addItem(f"{p.project_name} ({p.project_code})", str(p.id))
        self.cmb_projects.blockSignals(False)

        if projects:
            self._on_project_changed(0)

    def _on_project_changed(self, index: int) -> None:
        if index < 0 or index >= self.cmb_projects.count():
            return
        proj_id_str = self.cmb_projects.itemData(index)
        if not proj_id_str:
            return
        self.current_project_id = uuid.UUID(proj_id_str)
        scenarios = self.project_service.list_scenarios(self.current_project_id)
        if scenarios:
            self.current_scenario_id = scenarios[0].id
        else:
            self.current_scenario_id = None

    def _on_evaluate_appraisal(self) -> None:
        if not self.current_scenario_id:
            QMessageBox.warning(self, "No Scenario", "Please select a valid project scenario.")
            return

        try:
            report = self.appraisal_service.evaluate_appraisal(self.current_scenario_id)
            self.current_report = report
            self._render_report(report)
        except Exception as e:
            QMessageBox.critical(self, "Appraisal Error", f"Failed to evaluate appraisal metrics:\n{str(e)}")

    def _render_report(self, report: AppraisalReportDTO) -> None:
        # 1. Update KPI Cards
        ret = report.lifetime_returns
        npv_text = f"NPV: {format_inr(ret.npv_rupees)}"
        irr_text = f"IRR: {ret.irr_pct:.2f}%" if ret.irr_pct else "IRR: N/A"
        payback_text = f"Payback: {ret.payback_years:.2f} yrs | PI: {ret.profitability_index or 'N/A'}"
        self.card_returns.lbl_line1.setText(f"{npv_text} | {irr_text}")  # type: ignore
        self.card_returns.lbl_line2.setText(payback_text)  # type: ignore

        gross_dscr_str = f"Avg Gross DSCR: {ret.average_gross_dscr:.2f}x" if ret.average_gross_dscr else "Avg Gross DSCR: N/A"
        cfads_dscr_str = f"Avg CFADS: {ret.average_net_cfads_dscr:.2f}x" if ret.average_net_cfads_dscr else "Avg CFADS: N/A"
        cum_dscr_str = f"Cumulative DSCR: {ret.cumulative_dscr:.2f}x" if ret.cumulative_dscr else "Cumulative: N/A"
        self.card_dscr.lbl_line1.setText(gross_dscr_str)  # type: ignore
        self.card_dscr.lbl_line2.setText(f"{cfads_dscr_str} | {cum_dscr_str}")  # type: ignore

        # Liquidity / Solvency card
        cr_row = next((r for r in report.ratio_rows if r.metric_code == "CURRENT_RATIO"), None)
        de_row = next((r for r in report.ratio_rows if r.metric_code == "DEBT_EQUITY"), None)
        cr_val = cr_row.period_values.get(1, "N/A") if cr_row else "N/A"
        de_val = de_row.period_values.get(1, "N/A") if de_row else "N/A"
        self.card_solvency.lbl_line1.setText(f"Current Ratio (Y1): {cr_val}")  # type: ignore
        self.card_solvency.lbl_line2.setText(f"Debt-Equity (Y1): {de_val}")  # type: ignore

        # Audit Card
        if report.error_count == 0 and report.warning_count == 0:
            self.card_audit.lbl_line1.setText("Status: PASSED ✓")  # type: ignore
            self.card_audit.lbl_line1.setStyleSheet("font-size: 14px; font-weight: bold; color: #1e8e3e;")  # type: ignore
            self.card_audit.lbl_line2.setText("Zero errors or warnings detected")  # type: ignore
            self.lbl_val_banner.setText("✓ All cross-statement accounting invariants and banking appraisal rules passed successfully.")
            self.lbl_val_banner.setStyleSheet("background-color: #e6f4ea; color: #137333; padding: 10px; font-weight: bold; border-radius: 4px;")
        elif report.error_count > 0:
            self.card_audit.lbl_line1.setText("Status: ERRORS DETECTED ❌")  # type: ignore
            self.card_audit.lbl_line1.setStyleSheet("font-size: 14px; font-weight: bold; color: #d93025;")  # type: ignore
            self.card_audit.lbl_line2.setText(f"Errors: {report.error_count} | Warnings: {report.warning_count}")  # type: ignore
            self.lbl_val_banner.setText(f"❌ {report.error_count} material accounting error(s) detected. Fix errors before final lender submission.")
            self.lbl_val_banner.setStyleSheet("background-color: #fce8e6; color: #c5221f; padding: 10px; font-weight: bold; border-radius: 4px;")
        else:
            self.card_audit.lbl_line1.setText("Status: ADVISORY WARNINGS ⚠️")  # type: ignore
            self.card_audit.lbl_line1.setStyleSheet("font-size: 14px; font-weight: bold; color: #e37400;")  # type: ignore
            self.card_audit.lbl_line2.setText(f"Warnings: {report.warning_count}")  # type: ignore
            self.lbl_val_banner.setText(f"⚠️ {report.warning_count} advisory warning(s) detected. Review benchmarks and override if appropriate.")
            self.lbl_val_banner.setStyleSheet("background-color: #fef7e0; color: #b06000; padding: 10px; font-weight: bold; border-radius: 4px;")

        # 2. Render Ratios Table
        self._populate_ratio_table(
            table=self.tbl_ratios,
            rows=[r for r in report.ratio_rows if r.category != "BREAK_EVEN"],
            period_headers=report.period_headers,
        )

        # 3. Render Break-Even Table
        self._populate_ratio_table(
            table=self.tbl_bep,
            rows=[r for r in report.ratio_rows if r.category == "BREAK_EVEN"],
            period_headers=report.period_headers,
        )

        # 4. Render Sensitivity Table
        self._populate_sensitivity_table(report.sensitivity_rows)

        # 5. Render Validation Table
        self._populate_validation_table(report.validation_issues)

    def _populate_ratio_table(
        self,
        table: QTableWidget,
        rows: List[RatioMetricRowDTO],
        period_headers: List[str],
    ) -> None:
        table.clear()
        col_headers = ["Particulars / Metric", "Benchmark"] + period_headers
        table.setColumnCount(len(col_headers))
        table.setRowCount(len(rows))
        table.setHorizontalHeaderLabels(col_headers)

        table.setColumnWidth(0, 260)
        table.setColumnWidth(1, 140)

        for r_idx, row in enumerate(rows):
            # Particulars
            item_name = QTableWidgetItem(row.metric_name)
            item_name.setFont(QFont("Segoe UI", 9, QFont.Bold if "DSCR" in row.metric_name or "Ratio" in row.metric_name else QFont.Normal))
            table.setItem(r_idx, 0, item_name)

            # Benchmark
            item_bench = QTableWidgetItem(row.benchmark_text)
            item_bench.setTextAlignment(Qt.AlignCenter)
            table.setItem(r_idx, 1, item_bench)

            # Period columns
            for seq in range(1, len(period_headers) + 1):
                col_idx = seq + 1
                val_text = row.period_values.get(seq, "-")
                item_val = QTableWidgetItem(val_text)
                item_val.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)

                # Color warning if status is WARNING
                if row.status == "WARNING":
                    item_val.setForeground(QColor("#d93025"))
                table.setItem(r_idx, col_idx, item_val)

    def _populate_sensitivity_table(self, rows: List[SensitivityRowDTO]) -> None:
        self.tbl_sensitivity.clear()
        headers = ["Parameter", "Variation %", "Avg DSCR", "Project IRR %", "Avg PAT (₹)", "Y1 BEP %"]
        self.tbl_sensitivity.setColumnCount(len(headers))
        self.tbl_sensitivity.setRowCount(len(rows))
        self.tbl_sensitivity.setHorizontalHeaderLabels(headers)

        self.tbl_sensitivity.setColumnWidth(0, 260)
        self.tbl_sensitivity.setColumnWidth(1, 100)

        for r_idx, s in enumerate(rows):
            item_param = QTableWidgetItem(s.parameter_name)
            if s.variation_pct == Decimal("0.0"):
                item_param.setFont(QFont("Segoe UI", 9, QFont.Bold))
            self.tbl_sensitivity.setItem(r_idx, 0, item_param)

            var_text = f"{s.variation_pct:+.1f}%" if s.variation_pct != 0 else "Base"
            item_var = QTableWidgetItem(var_text)
            item_var.setTextAlignment(Qt.AlignCenter)
            self.tbl_sensitivity.setItem(r_idx, 1, item_var)

            item_dscr = QTableWidgetItem(s.average_dscr)
            item_dscr.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            self.tbl_sensitivity.setItem(r_idx, 2, item_dscr)

            item_irr = QTableWidgetItem(s.irr_pct)
            item_irr.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            self.tbl_sensitivity.setItem(r_idx, 3, item_irr)

            item_pat = QTableWidgetItem(format_inr(s.avg_pat_rupees))
            item_pat.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            self.tbl_sensitivity.setItem(r_idx, 4, item_pat)

            item_bep = QTableWidgetItem(f"{s.first_year_bep_pct:.2f}%")
            item_bep.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            self.tbl_sensitivity.setItem(r_idx, 5, item_bep)

    def _populate_validation_table(self, issues: List[ValidationIssueDTO]) -> None:
        self.tbl_validation.clear()
        headers = ["Severity", "Rule Code", "Scope", "Message", "Period", "Expected", "Actual", "Suggested Action"]
        self.tbl_validation.setColumnCount(len(headers))
        self.tbl_validation.setRowCount(len(issues))
        self.tbl_validation.setHorizontalHeaderLabels(headers)

        self.tbl_validation.setColumnWidth(0, 100)
        self.tbl_validation.setColumnWidth(1, 120)
        self.tbl_validation.setColumnWidth(2, 130)
        self.tbl_validation.setColumnWidth(3, 300)
        self.tbl_validation.setColumnWidth(7, 300)

        for r_idx, issue in enumerate(issues):
            # Severity
            item_sev = QTableWidgetItem(issue.severity)
            item_sev.setTextAlignment(Qt.AlignCenter)
            item_sev.setFont(QFont("Segoe UI", 9, QFont.Bold))
            if issue.severity == "ERROR":
                item_sev.setForeground(QColor("#d93025"))
            elif issue.severity == "WARNING":
                item_sev.setForeground(QColor("#e37400"))
            else:
                item_sev.setForeground(QColor("#1a73e8"))
            self.tbl_validation.setItem(r_idx, 0, item_sev)

            self.tbl_validation.setItem(r_idx, 1, QTableWidgetItem(issue.rule_code))
            self.tbl_validation.setItem(r_idx, 2, QTableWidgetItem(issue.scope_code))
            self.tbl_validation.setItem(r_idx, 3, QTableWidgetItem(issue.message))

            period_text = f"Y{issue.period_sequence}" if issue.period_sequence else "All"
            item_p = QTableWidgetItem(period_text)
            item_p.setTextAlignment(Qt.AlignCenter)
            self.tbl_validation.setItem(r_idx, 4, item_p)

            self.tbl_validation.setItem(r_idx, 5, QTableWidgetItem(issue.expected_value or "-"))
            self.tbl_validation.setItem(r_idx, 6, QTableWidgetItem(issue.actual_value or "-"))
            self.tbl_validation.setItem(r_idx, 7, QTableWidgetItem(issue.suggested_action or "-"))
