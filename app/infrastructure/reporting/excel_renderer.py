"""Excel Financial Model Renderer using openpyxl."""

from decimal import Decimal
from pathlib import Path
from typing import Dict, List, Optional
import uuid

import openpyxl
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from openpyxl.utils import get_column_letter

from app.application.dtos.report_dto import HorizontalStatementDTO, ProjectReportDataDTO
from app.common.money import format_inr


class ExcelReportRenderer:
    """Renders comprehensive, audit-ready multi-sheet Excel financial models from ProjectReportDataDTO."""

    # Color Palette
    HEADER_FILL = PatternFill(start_color="1F4E79", end_color="1F4E79", fill_type="solid")  # Navy Blue
    HEADER_FONT = Font(name="Calibri", size=11, bold=True, color="FFFFFF")
    SUBHEADER_FILL = PatternFill(start_color="D9E1F2", end_color="D9E1F2", fill_type="solid")  # Soft Blue
    SUBHEADER_FONT = Font(name="Calibri", size=10, bold=True, color="1F4E79")
    TITLE_FONT = Font(name="Calibri", size=14, bold=True, color="1F4E79")
    BOLD_FONT = Font(name="Calibri", size=10, bold=True, color="000000")
    NORMAL_FONT = Font(name="Calibri", size=10, bold=False, color="000000")
    MUTED_FONT = Font(name="Calibri", size=9, italic=True, color="595959")

    # Borders
    THIN_SIDE = Side(border_style="thin", color="D9D9D9")
    THICK_TOP = Side(border_style="thin", color="000000")
    DOUBLE_BOTTOM = Side(border_style="double", color="000000")
    CELL_BORDER = Border(left=THIN_SIDE, right=THIN_SIDE, top=THIN_SIDE, bottom=THIN_SIDE)
    TOTAL_BORDER = Border(top=THICK_TOP, bottom=DOUBLE_BOTTOM, left=THIN_SIDE, right=THIN_SIDE)

    # Number Formats
    CURRENCY_FORMAT = '₹ #,##0.00;[Red](₹ #,##0.00);"-"'
    PERCENT_FORMAT = '0.00%'
    RATIO_FORMAT = '0.00"x"'
    INT_FORMAT = '#,##0'

    @classmethod
    def render(cls, report_data: ProjectReportDataDTO, output_path: str) -> str:
        """Renders the master Excel workbook and saves to output_path."""
        wb = openpyxl.Workbook()
        wb.remove(wb.active)  # Remove default sheet

        # 1. Executive Summary Sheet
        cls._render_summary_sheet(wb, report_data)

        # 2. Projected Financial Statements (Horizontal A:C and D:J)
        cls._render_horizontal_statement_sheet(wb, "Projected P&L", report_data.pl_statement, report_data)
        cls._render_horizontal_statement_sheet(wb, "Projected Balance Sheet", report_data.bs_statement, report_data)
        cls._render_horizontal_statement_sheet(wb, "Projected Cash Flow", report_data.cf_statement, report_data)

        # 3. Appraisal Ratios & DSCR
        cls._render_horizontal_statement_sheet(wb, "Ratios & DSCR", report_data.ratios_statement, report_data)

        # 4. Break-Even & Sensitivity Analysis
        cls._render_break_even_and_sensitivity_sheet(wb, report_data)

        # 5. Loan Amortization Schedules
        cls._render_loan_schedule_sheet(wb, report_data)

        # 6. Fixed Assets & Depreciation
        cls._render_asset_schedule_sheet(wb, report_data)

        # 7. Audit & Validation Issues
        cls._render_validation_sheet(wb, report_data)

        # Ensure directory exists and save
        dest = Path(output_path)
        dest.parent.mkdir(parents=True, exist_ok=True)
        wb.save(output_path)
        return output_path

    @classmethod
    def _render_summary_sheet(cls, wb: openpyxl.Workbook, data: ProjectReportDataDTO) -> None:
        ws = wb.create_sheet(title="Executive Summary")
        ws.views.sheetView[0].showGridLines = True

        # Document Header
        ws["A1"] = data.metadata.report_title.upper()
        ws["A1"].font = cls.TITLE_FONT
        ws["A2"] = f"Project: {data.metadata.project_name} | Entity: {data.metadata.entity_legal_name} ({data.metadata.constitution_label})"
        ws["A2"].font = cls.BOLD_FONT
        ws["A3"] = f"Run #{data.metadata.calculation_run_number} | Engine v{data.metadata.engine_version} | Input Hash: {data.metadata.input_hash[:16]}... | Generated: {data.metadata.generated_at.strftime('%Y-%m-%d %H:%M UTC')}"
        ws["A3"].font = cls.MUTED_FONT

        # KPI Summary Cards Block
        ws["A5"] = "KEY PROJECT & APPRAISAL PARAMETERS"
        ws["A5"].font = cls.SUBHEADER_FONT
        ws["A5"].fill = cls.SUBHEADER_FILL

        ex = data.executive_summary
        kpis = [
            ("Total Project Cost", float(ex.total_project_cost_rupees), cls.CURRENCY_FORMAT),
            ("Promoter Equity Contribution", float(ex.promoter_equity_rupees), cls.CURRENCY_FORMAT),
            ("Term Loan Finance", float(ex.term_loan_rupees), cls.CURRENCY_FORMAT),
            ("Initial Year Net Revenue", float(ex.first_year_net_revenue_rupees), cls.CURRENCY_FORMAT),
            ("Terminal Year Net Revenue", float(ex.terminal_year_net_revenue_rupees), cls.CURRENCY_FORMAT),
            ("Average Gross DSCR", float(ex.average_gross_dscr) if ex.average_gross_dscr else 0.0, cls.RATIO_FORMAT),
            ("Average Net CFADS DSCR", float(ex.average_net_cfads_dscr) if ex.average_net_cfads_dscr else 0.0, cls.RATIO_FORMAT),
            ("Cumulative DSCR", float(ex.cumulative_dscr) if ex.cumulative_dscr else 0.0, cls.RATIO_FORMAT),
            ("Project IRR (%)", float(ex.project_irr_pct / Decimal("100")) if ex.project_irr_pct else 0.0, cls.PERCENT_FORMAT),
            ("Net Present Value (NPV @ 10%)", float(ex.npv_rupees), cls.CURRENCY_FORMAT),
            ("Simple Payback Period", f"{ex.payback_years:.2f} Years", None),
            ("Break-Even Capacity Utilization", float(ex.first_year_bep_capacity_pct / Decimal("100")), cls.PERCENT_FORMAT),
            ("Audit Integrity Status", f"{ex.validation_status} (Errors: {ex.validation_error_count}, Warnings: {ex.validation_warning_count})", None),
        ]

        curr_row = 6
        for label, val, num_fmt in kpis:
            ws.cell(row=curr_row, column=1, value=label).font = cls.BOLD_FONT
            val_cell = ws.cell(row=curr_row, column=2, value=val)
            val_cell.font = cls.NORMAL_FONT
            if num_fmt:
                val_cell.number_format = num_fmt
            ws.cell(row=curr_row, column=1).border = cls.CELL_BORDER
            ws.cell(row=curr_row, column=2).border = cls.CELL_BORDER
            curr_row += 1

        # Means of Finance & Cost Table
        curr_row += 2
        ws.cell(row=curr_row, column=1, value="PROJECT COST & MEANS OF FINANCE SUMMARY").font = cls.SUBHEADER_FONT
        ws.cell(row=curr_row, column=1).fill = cls.SUBHEADER_FILL

        curr_row += 1
        headers = ["Cost Component", "Amount (₹)", "Funding Source", "Amount (₹)", "Share %"]
        for c_idx, h in enumerate(headers, start=1):
            cell = ws.cell(row=curr_row, column=c_idx, value=h)
            cell.font = cls.HEADER_FONT
            cell.fill = cls.HEADER_FILL
            cell.alignment = Alignment(horizontal="center")

        cf = data.cost_and_funding
        max_len = max(len(cf.cost_items), len(cf.funding_sources))
        start_data_row = curr_row + 1

        for i in range(max_len):
            r = start_data_row + i
            cost_item = cf.cost_items[i] if i < len(cf.cost_items) else None
            fund_item = cf.funding_sources[i] if i < len(cf.funding_sources) else None

            # Cost
            if cost_item:
                ws.cell(row=r, column=1, value=cost_item.description).font = cls.NORMAL_FONT
                c_val = ws.cell(row=r, column=2, value=float(cost_item.capitalised_rupees))
                c_val.font = cls.NORMAL_FONT
                c_val.number_format = cls.CURRENCY_FORMAT
            # Funding
            if fund_item:
                ws.cell(row=r, column=3, value=fund_item.source_name).font = cls.NORMAL_FONT
                f_val = ws.cell(row=r, column=4, value=float(fund_item.amount_rupees))
                f_val.font = cls.NORMAL_FONT
                f_val.number_format = cls.CURRENCY_FORMAT
                p_val = ws.cell(row=r, column=5, value=float(fund_item.percentage / Decimal("100")))
                p_val.font = cls.NORMAL_FONT
                p_val.number_format = cls.PERCENT_FORMAT

            for col in range(1, 6):
                ws.cell(row=r, column=col).border = cls.CELL_BORDER

        # Totals Row
        tot_row = start_data_row + max_len
        ws.cell(row=tot_row, column=1, value="TOTAL COST").font = cls.BOLD_FONT
        t_cost = ws.cell(row=tot_row, column=2, value=float(cf.total_cost_rupees))
        t_cost.font = cls.BOLD_FONT
        t_cost.number_format = cls.CURRENCY_FORMAT

        ws.cell(row=tot_row, column=3, value="TOTAL MEANS OF FINANCE").font = cls.BOLD_FONT
        t_fund = ws.cell(row=tot_row, column=4, value=float(cf.total_funding_rupees))
        t_fund.font = cls.BOLD_FONT
        t_fund.number_format = cls.CURRENCY_FORMAT

        t_pct = ws.cell(row=tot_row, column=5, value=1.0)
        t_pct.font = cls.BOLD_FONT
        t_pct.number_format = cls.PERCENT_FORMAT

        for col in range(1, 6):
            ws.cell(row=tot_row, column=col).border = cls.TOTAL_BORDER

        # Autofit column widths
        ws.column_dimensions["A"].width = 38
        ws.column_dimensions["B"].width = 24
        ws.column_dimensions["C"].width = 36
        ws.column_dimensions["D"].width = 24
        ws.column_dimensions["E"].width = 16

    @classmethod
    def _render_horizontal_statement_sheet(
        cls,
        wb: openpyxl.Workbook,
        sheet_title: str,
        statement: HorizontalStatementDTO,
        data: ProjectReportDataDTO,
    ) -> None:
        """Renders standard horizontal statement layout (Columns A:C and D:J) with freeze panes."""
        ws = wb.create_sheet(title=sheet_title)
        ws.views.sheetView[0].showGridLines = True
        ws.page_setup.orientation = ws.ORIENTATION_LANDSCAPE
        ws.page_setup.paperSize = ws.PAPERSIZE_A4

        # Title block
        ws["A1"] = statement.title.upper()
        ws["A1"].font = cls.TITLE_FONT
        ws["A2"] = f"Entity: {data.metadata.entity_legal_name} | Project: {data.metadata.project_name} | Currency: INR (₹)"
        ws["A2"].font = cls.MUTED_FONT

        # Header Row (Row 4)
        col_headers = ["Sr. No.", "Note", "Particulars"] + statement.period_headers
        header_row = 4
        for c_idx, h in enumerate(col_headers, start=1):
            cell = ws.cell(row=header_row, column=c_idx, value=h)
            cell.font = cls.HEADER_FONT
            cell.fill = cls.HEADER_FILL
            cell.alignment = Alignment(horizontal="center" if c_idx <= 2 or c_idx > 3 else "left", vertical="center")
            cell.border = cls.CELL_BORDER

        # Freeze Panes at Column D and below Header Row
        ws.freeze_panes = "D5"

        # Populate Rows
        curr_row = 5
        num_periods = len(statement.period_headers)

        for row_dto in statement.rows:
            is_hdr = row_dto.is_heading
            is_tot = row_dto.is_total

            c_sr = ws.cell(row=curr_row, column=1, value=row_dto.sr_no)
            c_sr.alignment = Alignment(horizontal="center")
            c_note = ws.cell(row=curr_row, column=2, value=row_dto.note_ref)
            c_note.alignment = Alignment(horizontal="center")
            c_part = ws.cell(row=curr_row, column=3, value=row_dto.particulars)

            font_to_use = cls.BOLD_FONT if (is_hdr or is_tot) else cls.NORMAL_FONT
            c_sr.font = font_to_use
            c_note.font = font_to_use
            c_part.font = font_to_use

            border_to_use = cls.TOTAL_BORDER if is_tot else cls.CELL_BORDER
            c_sr.border = border_to_use
            c_note.border = border_to_use
            c_part.border = border_to_use

            if is_hdr:
                c_part.fill = cls.SUBHEADER_FILL

            for seq in range(1, num_periods + 1):
                col_idx = 3 + seq
                amt = row_dto.amounts.get(seq)
                cell_amt = ws.cell(row=curr_row, column=col_idx)
                if amt is not None:
                    # Check if percent or ratio
                    if "%" in row_dto.particulars or "Margin" in row_dto.particulars or "ROCE" in row_dto.particulars or "RONW" in row_dto.particulars:
                        cell_amt.value = float(amt / Decimal("100"))
                        cell_amt.number_format = cls.PERCENT_FORMAT
                    elif "Ratio" in row_dto.particulars or "DSCR" in row_dto.particulars or "Coverage" in row_dto.particulars or "Index" in row_dto.particulars:
                        cell_amt.value = float(amt)
                        cell_amt.number_format = cls.RATIO_FORMAT
                    else:
                        cell_amt.value = float(amt)
                        cell_amt.number_format = cls.CURRENCY_FORMAT
                else:
                    cell_amt.value = "-"
                    cell_amt.alignment = Alignment(horizontal="center")

                cell_amt.font = font_to_use
                cell_amt.border = border_to_use

            curr_row += 1

        # Column widths
        ws.column_dimensions["A"].width = 10
        ws.column_dimensions["B"].width = 10
        ws.column_dimensions["C"].width = 38
        for seq in range(1, num_periods + 1):
            col_letter = get_column_letter(3 + seq)
            ws.column_dimensions[col_letter].width = 18

    @classmethod
    def _render_break_even_and_sensitivity_sheet(cls, wb: openpyxl.Workbook, data: ProjectReportDataDTO) -> None:
        ws = wb.create_sheet(title="Break-Even & Sensitivity")
        ws.views.sheetView[0].showGridLines = True
        ws.page_setup.orientation = ws.ORIENTATION_LANDSCAPE

        # 1. Break-Even Statement Table
        ws["A1"] = "BREAK-EVEN ANALYSIS (7-YEAR HORIZONTAL)"
        ws["A1"].font = cls.TITLE_FONT

        bep_stmt = data.break_even_statement
        col_headers = ["Sr. No.", "Note", "Particulars"] + bep_stmt.period_headers
        header_row = 3
        for c_idx, h in enumerate(col_headers, start=1):
            cell = ws.cell(row=header_row, column=c_idx, value=h)
            cell.font = cls.HEADER_FONT
            cell.fill = cls.HEADER_FILL
            cell.alignment = Alignment(horizontal="center" if c_idx <= 2 or c_idx > 3 else "left")
            cell.border = cls.CELL_BORDER

        curr_row = 4
        num_periods = len(bep_stmt.period_headers)
        for row_dto in bep_stmt.rows:
            ws.cell(row=curr_row, column=1, value=row_dto.sr_no).border = cls.CELL_BORDER
            ws.cell(row=curr_row, column=2, value=row_dto.note_ref).border = cls.CELL_BORDER
            ws.cell(row=curr_row, column=3, value=row_dto.particulars).font = cls.BOLD_FONT if row_dto.is_total else cls.NORMAL_FONT
            ws.cell(row=curr_row, column=3).border = cls.CELL_BORDER

            for seq in range(1, num_periods + 1):
                col_idx = 3 + seq
                amt = row_dto.amounts.get(seq)
                cell_amt = ws.cell(row=curr_row, column=col_idx)
                if amt is not None:
                    if "%" in row_dto.particulars:
                        cell_amt.value = float(amt / Decimal("100"))
                        cell_amt.number_format = cls.PERCENT_FORMAT
                    else:
                        cell_amt.value = float(amt)
                        cell_amt.number_format = cls.CURRENCY_FORMAT
                else:
                    cell_amt.value = "-"
                cell_amt.font = cls.NORMAL_FONT
                cell_amt.border = cls.CELL_BORDER

            curr_row += 1

        # 2. Operational Sensitivity Analysis Matrix
        curr_row += 2
        ws.cell(row=curr_row, column=1, value="OPERATIONAL SENSITIVITY ANALYSIS MATRIX").font = cls.TITLE_FONT

        curr_row += 1
        sens_headers = ["Operational Parameter", "Variation %", "Average DSCR", "Project IRR %", "Avg Annual PAT (₹)", "Y1 Break-Even %"]
        for c_idx, h in enumerate(sens_headers, start=1):
            cell = ws.cell(row=curr_row, column=c_idx, value=h)
            cell.font = cls.HEADER_FONT
            cell.fill = cls.HEADER_FILL
            cell.alignment = Alignment(horizontal="center")
            cell.border = cls.CELL_BORDER

        curr_row += 1
        for s in data.sensitivity_scenarios:
            ws.cell(row=curr_row, column=1, value=s.parameter_name).font = cls.BOLD_FONT if s.variation_pct == Decimal("0.0") else cls.NORMAL_FONT
            var_cell = ws.cell(row=curr_row, column=2, value=float(s.variation_pct / Decimal("100")))
            var_cell.number_format = cls.PERCENT_FORMAT
            var_cell.alignment = Alignment(horizontal="center")

            dscr_cell = ws.cell(row=curr_row, column=3, value=s.average_dscr)
            dscr_cell.alignment = Alignment(horizontal="right")

            irr_cell = ws.cell(row=curr_row, column=4, value=s.irr_pct)
            irr_cell.alignment = Alignment(horizontal="right")

            pat_cell = ws.cell(row=curr_row, column=5, value=float(s.avg_pat_rupees))
            pat_cell.number_format = cls.CURRENCY_FORMAT

            bep_cell = ws.cell(row=curr_row, column=6, value=float(s.first_year_bep_pct / Decimal("100")))
            bep_cell.number_format = cls.PERCENT_FORMAT

            for col in range(1, 7):
                ws.cell(row=curr_row, column=col).border = cls.CELL_BORDER
            curr_row += 1

        # Column widths
        ws.column_dimensions["A"].width = 10
        ws.column_dimensions["B"].width = 14
        ws.column_dimensions["C"].width = 36
        for seq in range(1, 8):
            ws.column_dimensions[get_column_letter(3 + seq)].width = 18

    @classmethod
    def _render_loan_schedule_sheet(cls, wb: openpyxl.Workbook, data: ProjectReportDataDTO) -> None:
        ws = wb.create_sheet(title="Loan Amortization")
        ws.views.sheetView[0].showGridLines = True

        ws["A1"] = "TERM LOAN REPAYMENT SCHEDULE & DEBT SERVICE"
        ws["A1"].font = cls.TITLE_FONT

        # 1. Annual Summary Table
        ws["A3"] = "ANNUAL DEBT SERVICE SUMMARY"
        ws["A3"].font = cls.SUBHEADER_FONT
        ws["A3"].fill = cls.SUBHEADER_FILL

        ann_headers = ["Period", "Year Label", "Opening Balance", "Disbursement", "Principal Repaid", "Interest Paid", "Total Debt Service", "Closing Balance"]
        for c_idx, h in enumerate(ann_headers, start=1):
            cell = ws.cell(row=4, column=c_idx, value=h)
            cell.font = cls.HEADER_FONT
            cell.fill = cls.HEADER_FILL
            cell.alignment = Alignment(horizontal="center")
            cell.border = cls.CELL_BORDER

        curr_row = 5
        for row in data.loan_annual_summaries:
            ws.cell(row=curr_row, column=1, value=f"Year {row.period_sequence}").alignment = Alignment(horizontal="center")
            ws.cell(row=curr_row, column=2, value=row.period_label).alignment = Alignment(horizontal="center")

            cols_val = [
                row.opening_balance_rupees,
                row.disbursement_rupees,
                row.principal_repaid_rupees,
                row.interest_paid_rupees,
                row.total_debt_service_rupees,
                row.closing_balance_rupees,
            ]
            for i, val in enumerate(cols_val, start=3):
                c = ws.cell(row=curr_row, column=i, value=float(val))
                c.number_format = cls.CURRENCY_FORMAT
                c.font = cls.NORMAL_FONT

            for c_idx in range(1, 9):
                ws.cell(row=curr_row, column=c_idx).border = cls.CELL_BORDER
            curr_row += 1

        # 2. Monthly Schedule
        curr_row += 2
        ws.cell(row=curr_row, column=1, value="MONTHLY AMORTIZATION SCHEDULE (84 MONTHS)").font = cls.SUBHEADER_FONT
        ws.cell(row=curr_row, column=1).fill = cls.SUBHEADER_FILL

        curr_row += 1
        m_headers = ["Month #", "Due Date", "Opening Balance", "Disbursement", "Principal", "Interest", "Total EMI", "Closing Balance"]
        for c_idx, h in enumerate(m_headers, start=1):
            cell = ws.cell(row=curr_row, column=c_idx, value=h)
            cell.font = cls.HEADER_FONT
            cell.fill = cls.HEADER_FILL
            cell.alignment = Alignment(horizontal="center")
            cell.border = cls.CELL_BORDER

        curr_row += 1
        for m in data.loan_monthly_installments:
            ws.cell(row=curr_row, column=1, value=m.installment_number).alignment = Alignment(horizontal="center")
            ws.cell(row=curr_row, column=2, value=str(m.due_date)).alignment = Alignment(horizontal="center")

            vals = [
                m.opening_balance_rupees,
                m.disbursement_rupees,
                m.principal_rupees,
                m.interest_rupees,
                m.payment_rupees,
                m.closing_balance_rupees,
            ]
            for i, val in enumerate(vals, start=3):
                c = ws.cell(row=curr_row, column=i, value=float(val))
                c.number_format = cls.CURRENCY_FORMAT

            for col in range(1, 9):
                ws.cell(row=curr_row, column=col).border = cls.CELL_BORDER
            curr_row += 1

        for c_idx in range(1, 9):
            ws.column_dimensions[get_column_letter(c_idx)].width = 18

    @classmethod
    def _render_asset_schedule_sheet(cls, wb: openpyxl.Workbook, data: ProjectReportDataDTO) -> None:
        ws = wb.create_sheet(title="Fixed Assets & Dep")
        ws.views.sheetView[0].showGridLines = True

        ws["A1"] = "FIXED ASSETS & DEPRECIATION SCHEDULE (COMPANIES ACT SLM)"
        ws["A1"].font = cls.TITLE_FONT

        headers = ["Period", "Year Label", "Opening Gross", "Additions", "Disposals", "Closing Gross", "Depreciation", "Accumulated Dep", "Closing Net Block"]
        for c_idx, h in enumerate(headers, start=1):
            cell = ws.cell(row=3, column=c_idx, value=h)
            cell.font = cls.HEADER_FONT
            cell.fill = cls.HEADER_FILL
            cell.alignment = Alignment(horizontal="center")
            cell.border = cls.CELL_BORDER

        curr_row = 4
        for a in data.asset_schedules:
            ws.cell(row=curr_row, column=1, value=f"Year {a.period_sequence}").alignment = Alignment(horizontal="center")
            ws.cell(row=curr_row, column=2, value=a.period_label).alignment = Alignment(horizontal="center")

            vals = [
                a.opening_gross_rupees,
                a.additions_rupees,
                a.disposals_rupees,
                a.closing_gross_rupees,
                a.depreciation_rupees,
                a.accumulated_depreciation_rupees,
                a.closing_nbv_rupees,
            ]
            for i, val in enumerate(vals, start=3):
                c = ws.cell(row=curr_row, column=i, value=float(val))
                c.number_format = cls.CURRENCY_FORMAT

            for col in range(1, 10):
                ws.cell(row=curr_row, column=col).border = cls.CELL_BORDER
            curr_row += 1

        for col in range(1, 10):
            ws.column_dimensions[get_column_letter(col)].width = 18

    @classmethod
    def _render_validation_sheet(cls, wb: openpyxl.Workbook, data: ProjectReportDataDTO) -> None:
        ws = wb.create_sheet(title="Audit & Validation")
        ws.views.sheetView[0].showGridLines = True

        ws["A1"] = "CROSS-STATEMENT AUDIT & INVARIANT VERIFICATION CERTIFICATE"
        ws["A1"].font = cls.TITLE_FONT
        ws["A2"] = f"Calculation Run: #{data.metadata.calculation_run_number} | Engine Hash: {data.metadata.input_hash} | Status: {data.executive_summary.validation_status}"
        ws["A2"].font = cls.MUTED_FONT

        headers = ["Severity", "Rule Code", "Scope", "Message", "Period", "Expected", "Actual", "Suggested Action"]
        for c_idx, h in enumerate(headers, start=1):
            cell = ws.cell(row=4, column=c_idx, value=h)
            cell.font = cls.HEADER_FONT
            cell.fill = cls.HEADER_FILL
            cell.alignment = Alignment(horizontal="center")
            cell.border = cls.CELL_BORDER

        curr_row = 5
        if not data.validation_issues:
            ws.cell(row=curr_row, column=1, value="INFO").alignment = Alignment(horizontal="center")
            ws.cell(row=curr_row, column=2, value="VAL-AUDIT-000")
            ws.cell(row=curr_row, column=3, value="GENERAL")
            ws.cell(row=curr_row, column=4, value="All cross-statement accounting invariants and lender underwriting rules reconciled with zero errors or warnings.")
            ws.cell(row=curr_row, column=5, value="All")
            ws.cell(row=curr_row, column=6, value="0 errors")
            ws.cell(row=curr_row, column=7, value="0 errors")
            ws.cell(row=curr_row, column=8, value="Approved for lender submission")
            for col in range(1, 9):
                ws.cell(row=curr_row, column=col).border = cls.CELL_BORDER
        else:
            for issue in data.validation_issues:
                ws.cell(row=curr_row, column=1, value=issue.severity).alignment = Alignment(horizontal="center")
                ws.cell(row=curr_row, column=2, value=issue.rule_code)
                ws.cell(row=curr_row, column=3, value=issue.scope_code)
                ws.cell(row=curr_row, column=4, value=issue.message)
                ws.cell(row=curr_row, column=5, value=f"Year {issue.period_sequence}" if issue.period_sequence else "All").alignment = Alignment(horizontal="center")
                ws.cell(row=curr_row, column=6, value=issue.expected_value or "-")
                ws.cell(row=curr_row, column=7, value=issue.actual_value or "-")
                ws.cell(row=curr_row, column=8, value=issue.suggested_action or "-")
                for col in range(1, 9):
                    ws.cell(row=curr_row, column=col).border = cls.CELL_BORDER
                curr_row += 1

        ws.column_dimensions["A"].width = 12
        ws.column_dimensions["B"].width = 16
        ws.column_dimensions["C"].width = 18
        ws.column_dimensions["D"].width = 44
        ws.column_dimensions["E"].width = 12
        ws.column_dimensions["F"].width = 20
        ws.column_dimensions["G"].width = 20
        ws.column_dimensions["H"].width = 40
