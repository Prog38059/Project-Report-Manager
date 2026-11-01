"""Desktop GUI View for Multi-Format Report Generation and Export Management (Excel, Word, PDF)."""

from datetime import datetime
import os
from pathlib import Path
from typing import Dict, List, Optional
import uuid

from PySide6.QtCore import Qt, QUrl
from PySide6.QtGui import QColor, QDesktopServices, QFont
from PySide6.QtWidgets import (
    QComboBox,
    QFileDialog,
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
    QVBoxLayout,
    QWidget,
)

from app.application.dtos.report_dto import GeneratedReportResultDTO, ProjectReportDataDTO
from app.application.services.project_service import ProjectService
from app.application.services.report_service import ReportService
from app.common.money import format_inr


class ReportView(QWidget):
    """Interactive GUI for generating, exporting, and managing CMA and Project Reports."""

    def __init__(
        self,
        project_service: ProjectService,
        report_service: ReportService,
        parent: Optional[QWidget] = None,
    ) -> None:
        super().__init__(parent)
        self.project_service = project_service
        self.report_service = report_service

        self.current_project_id: Optional[uuid.UUID] = None
        self.current_scenario_id: Optional[uuid.UUID] = None
        self.current_report_data: Optional[ProjectReportDataDTO] = None

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(14)

        # 1. Header Bar
        header = QHBoxLayout()
        title = QLabel("📑 Reports & Multi-Format Export Engine")
        title.setStyleSheet("font-size: 20px; font-weight: bold; color: #202124;")
        header.addWidget(title)
        header.addStretch()

        self.cmb_projects = QComboBox()
        self.cmb_projects.setMinimumWidth(260)
        self.cmb_projects.currentIndexChanged.connect(self._on_project_changed)
        header.addWidget(QLabel("Project:"))
        header.addWidget(self.cmb_projects)

        self.btn_refresh = QPushButton("🔄 Refresh")
        self.btn_refresh.clicked.connect(self.refresh)
        header.addWidget(self.btn_refresh)
        layout.addLayout(header)

        # 2. Control & Options Panel
        ctrl_frame = QFrame()
        ctrl_frame.setStyleSheet("""
            QFrame {
                background-color: #f8f9fa;
                border: 1px solid #dadce0;
                border-radius: 6px;
                padding: 12px;
            }
        """)
        ctrl_layout = QGridLayout(ctrl_frame)
        ctrl_layout.setContentsMargins(12, 12, 12, 12)
        ctrl_layout.setHorizontalSpacing(16)
        ctrl_layout.setVerticalSpacing(10)

        # Row 0: Scenario and Template
        ctrl_layout.addWidget(QLabel("<b>Scenario:</b>"), 0, 0)
        self.cmb_scenarios = QComboBox()
        self.cmb_scenarios.setMinimumWidth(220)
        self.cmb_scenarios.currentIndexChanged.connect(self._on_scenario_changed)
        ctrl_layout.addWidget(self.cmb_scenarios, 0, 1)

        ctrl_layout.addWidget(QLabel("<b>Report Template:</b>"), 0, 2)
        self.cmb_templates = QComboBox()
        self.cmb_templates.setMinimumWidth(260)
        self.cmb_templates.addItem("Standard Bank CMA & Appraisal Book", "TMPL_CMA_BANK")
        self.cmb_templates.addItem("Detailed Project Report (DPR - Full)", "TMPL_DPR_FULL")
        self.cmb_templates.addItem("Executive Summary & Term Sheet", "TMPL_EXEC_SUMMARY")
        ctrl_layout.addWidget(self.cmb_templates, 0, 3)

        # Row 1: Action Buttons
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(10)

        self.btn_export_excel = QPushButton("📗 Export Excel (.xlsx)")
        self.btn_export_excel.setStyleSheet("""
            QPushButton {
                background-color: #1e7e34;
                color: white;
                font-weight: bold;
                padding: 8px 14px;
                border-radius: 4px;
            }
            QPushButton:hover { background-color: #155724; }
        """)
        self.btn_export_excel.clicked.connect(lambda: self._on_export("EXCEL"))
        btn_layout.addWidget(self.btn_export_excel)

        self.btn_export_docx = QPushButton("📘 Export Word (.docx)")
        self.btn_export_docx.setStyleSheet("""
            QPushButton {
                background-color: #0d6efd;
                color: white;
                font-weight: bold;
                padding: 8px 14px;
                border-radius: 4px;
            }
            QPushButton:hover { background-color: #0b5ed7; }
        """)
        self.btn_export_docx.clicked.connect(lambda: self._on_export("DOCX"))
        btn_layout.addWidget(self.btn_export_docx)

        self.btn_export_pdf = QPushButton("📕 Export PDF (.pdf)")
        self.btn_export_pdf.setStyleSheet("""
            QPushButton {
                background-color: #dc3545;
                color: white;
                font-weight: bold;
                padding: 8px 14px;
                border-radius: 4px;
            }
            QPushButton:hover { background-color: #b02a37; }
        """)
        self.btn_export_pdf.clicked.connect(lambda: self._on_export("PDF"))
        btn_layout.addWidget(self.btn_export_pdf)

        self.btn_export_all = QPushButton("🚀 Export All Formats (Bundle)")
        self.btn_export_all.setStyleSheet("""
            QPushButton {
                background-color: #6f42c1;
                color: white;
                font-weight: bold;
                padding: 8px 16px;
                border-radius: 4px;
            }
            QPushButton:hover { background-color: #59359a; }
        """)
        self.btn_export_all.clicked.connect(self._on_export_all)
        btn_layout.addWidget(self.btn_export_all)

        btn_layout.addStretch()
        ctrl_layout.addLayout(btn_layout, 1, 0, 1, 4)

        layout.addWidget(ctrl_frame)

        # 3. Report Preview Summary Card
        self.preview_card = QFrame()
        self.preview_card.setStyleSheet("""
            QFrame {
                background-color: #ffffff;
                border: 1px solid #e0e0e0;
                border-radius: 6px;
                padding: 14px;
            }
        """)
        p_layout = QGridLayout(self.preview_card)
        p_layout.setContentsMargins(10, 10, 10, 10)
        p_layout.setSpacing(10)

        self.lbl_proj_info = QLabel("<b>Project:</b> None Selected")
        self.lbl_cost_info = QLabel("<b>Project Cost:</b> -")
        self.lbl_funding_info = QLabel("<b>Means of Finance:</b> -")
        self.lbl_dscr_info = QLabel("<b>Average DSCR:</b> -")
        self.lbl_irr_info = QLabel("<b>Project IRR:</b> -")
        self.lbl_audit_info = QLabel("<b>Validation Audit:</b> -")

        p_layout.addWidget(self.lbl_proj_info, 0, 0)
        p_layout.addWidget(self.lbl_cost_info, 0, 1)
        p_layout.addWidget(self.lbl_funding_info, 0, 2)
        p_layout.addWidget(self.lbl_dscr_info, 1, 0)
        p_layout.addWidget(self.lbl_irr_info, 1, 1)
        p_layout.addWidget(self.lbl_audit_info, 1, 2)

        layout.addWidget(self.preview_card)

        # 4. Export History Table
        history_header = QLabel("Generated Reports & Audit Trail")
        history_header.setStyleSheet("font-size: 15px; font-weight: bold; color: #202124; margin-top: 6px;")
        layout.addWidget(history_header)

        self.table_history = QTableWidget()
        self.table_history.setColumnCount(6)
        self.table_history.setHorizontalHeaderLabels([
            "Generated At",
            "Format",
            "Template",
            "File Name",
            "Size",
            "SHA-256 Digest",
        ])
        self.table_history.horizontalHeader().setSectionResizeMode(QHeaderView.Interactive)
        self.table_history.horizontalHeader().setStretchLastSection(True)
        self.table_history.setAlternatingRowColors(True)
        self.table_history.setStyleSheet("""
            QTableWidget {
                background-color: white;
                border: 1px solid #dadce0;
                gridline-color: #f1f3f4;
            }
            QHeaderView::section {
                background-color: #f8f9fa;
                font-weight: bold;
                border: 1px solid #dadce0;
                padding: 6px;
            }
        """)
        self.table_history.doubleClicked.connect(self._on_row_double_clicked)
        layout.addWidget(self.table_history)

        self.refresh()

    def refresh(self) -> None:
        """Refreshes project list and current export view."""
        self.cmb_projects.blockSignals(True)
        self.cmb_projects.clear()

        projects = self.project_service.list_projects()
        for p in projects:
            self.cmb_projects.addItem(f"{p.project_code} — {p.project_name}", str(p.id))

        self.cmb_projects.blockSignals(False)

        if self.cmb_projects.count() > 0:
            self.cmb_projects.setCurrentIndex(0)
            self._on_project_changed(0)
        else:
            self.current_project_id = None
            self.current_scenario_id = None
            self._clear_display()

    def _on_project_changed(self, idx: int) -> None:
        if idx < 0:
            return
        data = self.cmb_projects.currentData()
        if not data:
            return

        self.current_project_id = uuid.UUID(data)
        self.cmb_scenarios.blockSignals(True)
        self.cmb_scenarios.clear()

        scenarios = self.project_service.list_scenarios(self.current_project_id)
        for s in scenarios:
            self.cmb_scenarios.addItem(s.scenario_name, str(s.id))

        self.cmb_scenarios.blockSignals(False)

        if self.cmb_scenarios.count() > 0:
            self.cmb_scenarios.setCurrentIndex(0)
            self._on_scenario_changed(0)
        else:
            self.current_scenario_id = None
            self._clear_display()

    def _on_scenario_changed(self, idx: int) -> None:
        if idx < 0:
            return
        data = self.cmb_scenarios.currentData()
        if not data:
            return
        self.current_scenario_id = uuid.UUID(data)
        self._load_scenario_preview()
        self._load_export_history()

    def _clear_display(self) -> None:
        self.lbl_proj_info.setText("<b>Project:</b> None")
        self.lbl_cost_info.setText("<b>Project Cost:</b> -")
        self.lbl_funding_info.setText("<b>Means of Finance:</b> -")
        self.lbl_dscr_info.setText("<b>Average DSCR:</b> -")
        self.lbl_irr_info.setText("<b>Project IRR:</b> -")
        self.lbl_audit_info.setText("<b>Validation Audit:</b> -")
        self.table_history.setRowCount(0)

    def _load_scenario_preview(self) -> None:
        if not self.current_scenario_id:
            return
        try:
            tmpl_code = self.cmb_templates.currentData() or "TMPL_CMA_BANK"
            self.current_report_data = self.report_service.build_report_data_model(
                scenario_id=self.current_scenario_id,
                template_code=tmpl_code,
            )
            data = self.current_report_data
            self.lbl_proj_info.setText(f"<b>Project:</b> {data.metadata.project_name} ({data.metadata.entity_legal_name})")
            self.lbl_cost_info.setText(f"<b>Project Cost:</b> ₹{format_inr(data.executive_summary.total_project_cost_rupees)}")
            self.lbl_funding_info.setText(
                f"<b>Means of Finance:</b> Debt ₹{format_inr(data.executive_summary.term_loan_rupees)} | Equity ₹{format_inr(data.executive_summary.promoter_equity_rupees)}"
            )
            dscr_text = f"{data.executive_summary.average_gross_dscr:.2f}x" if data.executive_summary.average_gross_dscr else "N/A"
            self.lbl_dscr_info.setText(f"<b>Average DSCR:</b> {dscr_text}")

            irr_text = f"{data.executive_summary.project_irr_pct:.2f}%" if data.executive_summary.project_irr_pct else "N/A"
            self.lbl_irr_info.setText(f"<b>Project IRR:</b> {irr_text}")

            audit = data.audit
            status_color = "#137333" if audit.passed else "#d93025"
            self.lbl_audit_info.setText(
                f"<b>Validation Audit:</b> <span style='color: {status_color}; font-weight: bold;'>{'PASSED' if audit.passed else 'FAILED'}</span> "
                f"(Errors: {audit.material_error_count}, Warnings: {audit.advisory_warning_count})"
            )
        except Exception as e:
            self.lbl_proj_info.setText("<b>Status:</b> No calculation run found. Please run projections first.")
            self.lbl_cost_info.setText("<b>Project Cost:</b> -")
            self.lbl_funding_info.setText("<b>Means of Finance:</b> -")
            self.lbl_dscr_info.setText("<b>Average DSCR:</b> -")
            self.lbl_irr_info.setText("<b>Project IRR:</b> -")
            self.lbl_audit_info.setText("<b>Validation Audit:</b> -")
            self.current_report_data = None

    def _load_export_history(self) -> None:
        if not self.current_scenario_id:
            self.table_history.setRowCount(0)
            return

        reports = self.report_service.list_generated_reports(self.current_scenario_id)
        self.table_history.setRowCount(len(reports))
        for r_idx, rep in enumerate(reports):
            # 0: Generated At
            item_dt = QTableWidgetItem(rep.generated_at.strftime("%Y-%m-%d %H:%M:%S") if rep.generated_at else "-")
            self.table_history.setItem(r_idx, 0, item_dt)

            # 1: Format
            item_fmt = QTableWidgetItem(rep.output_type)
            item_fmt.setTextAlignment(Qt.AlignCenter)
            if rep.output_type == "EXCEL":
                item_fmt.setForeground(QColor("#1e7e34"))
            elif rep.output_type == "DOCX":
                item_fmt.setForeground(QColor("#0d6efd"))
            elif rep.output_type == "PDF":
                item_fmt.setForeground(QColor("#dc3545"))
            self.table_history.setItem(r_idx, 1, item_fmt)

            # 2: Template
            self.table_history.setItem(r_idx, 2, QTableWidgetItem(rep.template_code or "-"))

            # 3: File Name
            f_name = Path(rep.file_path).name if rep.file_path else "-"
            item_name = QTableWidgetItem(f_name)
            item_name.setData(Qt.UserRole, rep.file_path)
            self.table_history.setItem(r_idx, 3, item_name)

            # 4: Size
            size_kb = f"{rep.file_size_bytes / 1024:.1f} KB" if rep.file_size_bytes else "0 KB"
            item_sz = QTableWidgetItem(size_kb)
            item_sz.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            self.table_history.setItem(r_idx, 4, item_sz)

            # 5: SHA-256 Digest
            item_hash = QTableWidgetItem((rep.file_hash[:16] + "...") if rep.file_hash else "-")
            item_hash.setToolTip(rep.file_hash or "")
            self.table_history.setItem(r_idx, 5, item_hash)

        self.table_history.resizeColumnsToContents()

    def _on_export(self, output_type: str) -> None:
        if not self.current_scenario_id:
            QMessageBox.warning(self, "Selection Required", "Please select a project and scenario to export.")
            return

        tmpl_code = self.cmb_templates.currentData() or "TMPL_CMA_BANK"

        # Ask file save dialog
        ext_map = {"EXCEL": ("Excel Workbook (*.xlsx)", ".xlsx"), "DOCX": ("Word Document (*.docx)", ".docx"), "PDF": ("PDF Document (*.pdf)", ".pdf")}
        filt, ext = ext_map.get(output_type, ("All Files (*.*)", ""))

        default_name = f"Project_Report_{output_type.lower()}_{datetime.now().strftime('%Y%m%d_%H%M%S')}{ext}"
        save_path, _ = QFileDialog.getSaveFileName(self, f"Export {output_type} Report", default_name, filt)
        if not save_path:
            return

        try:
            res = self.report_service.generate_report(
                scenario_id=self.current_scenario_id,
                template_code=tmpl_code,
                output_type=output_type,
                custom_output_path=save_path,
            )
            self._load_export_history()
            reply = QMessageBox.information(
                self,
                "Export Complete",
                f"Successfully generated {output_type} report!\n\n"
                f"Path: {res.file_path}\n"
                f"Size: {res.file_size_bytes / 1024:.1f} KB\n"
                f"SHA-256: {res.file_hash[:16]}...\n\n"
                f"Would you like to open the generated file now?",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.Yes,
            )
            if reply == QMessageBox.Yes:
                self._open_file(res.file_path)

        except Exception as e:
            QMessageBox.critical(self, "Export Error", f"Failed to generate report:\n{str(e)}")

    def _on_export_all(self) -> None:
        if not self.current_scenario_id:
            QMessageBox.warning(self, "Selection Required", "Please select a project and scenario to export.")
            return

        tmpl_code = self.cmb_templates.currentData() or "TMPL_CMA_BANK"
        folder = QFileDialog.getExistingDirectory(self, "Select Destination Folder for All Reports")
        if not folder:
            return

        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            xlsx_path = os.path.join(folder, f"Project_Report_CMA_{timestamp}.xlsx")
            docx_path = os.path.join(folder, f"Project_Report_DPR_{timestamp}.docx")
            pdf_path = os.path.join(folder, f"Project_Report_Appraisal_{timestamp}.pdf")

            self.report_service.generate_report(
                scenario_id=self.current_scenario_id,
                template_code=tmpl_code,
                output_type="EXCEL",
                custom_output_path=xlsx_path,
            )
            self.report_service.generate_report(
                scenario_id=self.current_scenario_id,
                template_code=tmpl_code,
                output_type="DOCX",
                custom_output_path=docx_path,
            )
            self.report_service.generate_report(
                scenario_id=self.current_scenario_id,
                template_code=tmpl_code,
                output_type="PDF",
                custom_output_path=pdf_path,
            )

            self._load_export_history()
            QMessageBox.information(
                self,
                "Export Bundle Complete",
                f"Successfully exported complete report package:\n\n"
                f"• {xlsx_path}\n"
                f"• {docx_path}\n"
                f"• {pdf_path}\n",
            )
        except Exception as e:
            QMessageBox.critical(self, "Export Error", f"Failed to generate bundle:\n{str(e)}")

    def _on_row_double_clicked(self, index) -> None:
        row = index.row()
        item = self.table_history.item(row, 3)
        if item:
            path = item.data(Qt.UserRole)
            if path and os.path.exists(path):
                self._open_file(path)

    def _open_file(self, file_path: str) -> None:
        try:
            if os.name == "nt":
                os.startfile(file_path)
            else:
                QDesktopServices.openUrl(QUrl.fromLocalFile(file_path))
        except Exception as e:
            QMessageBox.warning(self, "Open File Failed", f"Could not launch file:\n{str(e)}")
