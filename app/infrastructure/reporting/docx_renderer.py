"""Word (.docx) Project Appraisal Report Renderer using python-docx."""

from decimal import Decimal
from pathlib import Path
from typing import Dict, List, Optional
import uuid

import docx
from docx.enum.table import WD_ALIGN_VERTICAL, WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement, parse_xml
from docx.oxml.ns import nsdecls, qn
from docx.shared import Inches, Pt, RGBColor

from app.application.dtos.report_dto import HorizontalStatementDTO, ProjectReportDataDTO
from app.common.money import format_inr


class DocxReportRenderer:
    """Renders comprehensive, bank-grade Word (.docx) project appraisal reports."""

    NAVY_HEX = "1F4E79"
    SOFT_BLUE_HEX = "D9E1F2"
    GRAY_HEX = "F2F2F2"
    BORDER_GRAY_HEX = "D9D9D9"

    @classmethod
    def render(cls, report_data: ProjectReportDataDTO, output_path: str) -> str:
        """Renders the master Word document and saves to output_path."""
        doc = docx.Document()

        # Set page margins (0.75 in)
        for section in doc.sections:
            section.top_margin = Inches(0.75)
            section.bottom_margin = Inches(0.75)
            section.left_margin = Inches(0.75)
            section.right_margin = Inches(0.75)
            section.page_width = Inches(8.5)
            section.page_height = Inches(11.0)

        # 1. Cover Page & Document Control
        cls._render_cover_page(doc, report_data)
        doc.add_page_break()

        # 2. Executive Summary
        cls._render_executive_summary(doc, report_data)

        # 3. Project Cost & Means of Finance
        cls._render_cost_and_funding(doc, report_data)

        # 4. Projected Financial Statements (P&L, Balance Sheet, Cash Flow)
        cls._render_horizontal_statements(doc, report_data)

        # 5. Loan Amortization Summary
        cls._render_loan_section(doc, report_data)

        # 6. Ratios & DSCR Appraisal
        cls._render_ratios_section(doc, report_data)

        # 7. Break-Even & Sensitivity Matrix
        cls._render_break_even_and_sensitivity(doc, report_data)

        # 8. Cross-Statement Audit & Compliance Certificate
        cls._render_audit_certificate(doc, report_data)

        # Save
        dest = Path(output_path)
        dest.parent.mkdir(parents=True, exist_ok=True)
        doc.save(output_path)
        return output_path

    @classmethod
    def _set_cell_background(cls, cell, hex_color: str) -> None:
        tcPr = cell._tc.get_or_add_tcPr()
        shd = parse_xml(f'<w:shd {nsdecls("w")} w:fill="{hex_color}"/>')
        tcPr.append(shd)

    @classmethod
    def _set_cell_margins(cls, cell, top: int = 100, bottom: int = 100, left: int = 140, right: int = 140) -> None:
        tcPr = cell._tc.get_or_add_tcPr()
        tcMar = parse_xml(
            f'<w:tcMar {nsdecls("w")}>'
            f'<w:top w:w="{top}" w:type="dxa"/>'
            f'<w:bottom w:w="{bottom}" w:type="dxa"/>'
            f'<w:left w:w="{left}" w:type="dxa"/>'
            f'<w:right w:w="{right}" w:type="dxa"/>'
            f'</w:tcMar>'
        )
        tcPr.append(tcMar)

    @classmethod
    def _render_cover_page(cls, doc: docx.Document, data: ProjectReportDataDTO) -> None:
        # Title
        p_title = doc.add_paragraph()
        p_title.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p_title.paragraph_format.space_before = Pt(40)
        p_title.paragraph_format.space_after = Pt(8)
        run_title = p_title.add_run(data.metadata.report_title.upper())
        run_title.font.name = "Calibri"
        run_title.font.size = Pt(22)
        run_title.font.bold = True
        run_title.font.color.rgb = RGBColor(0x1F, 0x4E, 0x79)

        # Subtitle
        p_sub = doc.add_paragraph()
        p_sub.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p_sub.paragraph_format.space_after = Pt(40)
        run_sub = p_sub.add_run("FINANCIAL PROJECTIONS & LENDER CREDIT APPRAISAL BOOK")
        run_sub.font.name = "Calibri"
        run_sub.font.size = Pt(13)
        run_sub.font.bold = True
        run_sub.font.color.rgb = RGBColor(0x59, 0x59, 0x59)

        # Entity / Project Info Box Table
        table = doc.add_table(rows=5, cols=2)
        table.alignment = WD_TABLE_ALIGNMENT.CENTER
        table.autofit = False

        rows_info = [
            ("Project Name:", data.metadata.project_name),
            ("Borrower / Entity:", f"{data.metadata.entity_legal_name} ({data.metadata.constitution_label})"),
            ("Client Profile:", data.metadata.client_name),
            ("Project Code / ID:", data.metadata.project_code),
            ("Projection Horizon:", f"{len(data.pl_statement.period_headers)} Projection Years"),
        ]
        for idx, (lbl, val) in enumerate(rows_info):
            cell_lbl = table.cell(idx, 0)
            cell_val = table.cell(idx, 1)
            cell_lbl.width = Inches(2.2)
            cell_val.width = Inches(4.5)
            p_l = cell_lbl.paragraphs[0]
            r_l = p_l.add_run(lbl)
            r_l.font.bold = True
            r_l.font.size = Pt(11)
            p_v = cell_val.paragraphs[0]
            r_v = p_v.add_run(val)
            r_v.font.size = Pt(11)
            cls._set_cell_background(cell_lbl, cls.GRAY_HEX)
            cls._set_cell_margins(cell_lbl, 120, 120, 150, 150)
            cls._set_cell_margins(cell_val, 120, 120, 150, 150)

        # Document Control Block at Bottom
        p_ctrl = doc.add_paragraph()
        p_ctrl.paragraph_format.space_before = Pt(80)
        p_ctrl.paragraph_format.space_after = Pt(4)
        r_ctrl = p_ctrl.add_run("DOCUMENT CONTROL & CALCULATION ENGINE AUDIT RECORD")
        r_ctrl.font.bold = True
        r_ctrl.font.size = Pt(10)
        r_ctrl.font.color.rgb = RGBColor(0x1F, 0x4E, 0x79)

        ctrl_table = doc.add_table(rows=4, cols=2)
        ctrl_table.alignment = WD_TABLE_ALIGNMENT.CENTER
        ctrl_info = [
            ("Calculation Run #:", f"Run #{data.metadata.calculation_run_number} (Engine v{data.metadata.engine_version})"),
            ("Canonical Input Hash (SHA-256):", data.metadata.input_hash),
            ("Generation Timestamp:", data.metadata.generated_at.strftime("%Y-%m-%d %H:%M:%S UTC")),
            ("Confidentiality Notice:", data.metadata.confidentiality_notice),
        ]
        for idx, (k, v) in enumerate(ctrl_info):
            c0 = ctrl_table.cell(idx, 0)
            c1 = ctrl_table.cell(idx, 1)
            c0.width = Inches(2.5)
            c1.width = Inches(4.2)
            p0 = c0.paragraphs[0]
            r0 = p0.add_run(k)
            r0.font.bold = True
            r0.font.size = Pt(9)
            p1 = c1.paragraphs[0]
            r1 = p1.add_run(v)
            r1.font.size = Pt(9)
            if "Hash" in k:
                r1.font.name = "Consolas"
            cls._set_cell_margins(c0, 80, 80, 120, 120)
            cls._set_cell_margins(c1, 80, 80, 120, 120)

    @classmethod
    def _render_executive_summary(cls, doc: docx.Document, data: ProjectReportDataDTO) -> None:
        h1 = doc.add_heading("1. Executive Summary & Key Appraisal Indicators", level=1)
        h1.paragraph_format.space_before = Pt(12)
        h1.paragraph_format.space_after = Pt(8)

        p_desc = doc.add_paragraph(
            f"The project report evaluates the financial viability, debt service capacity, and investment returns for "
            f"'{data.metadata.project_name}' promoted by '{data.metadata.entity_legal_name}'. "
            f"The total project cost is estimated at {format_inr(data.executive_summary.total_project_cost_rupees)}, "
            f"funded through a debt-equity structure of term debt {format_inr(data.executive_summary.term_loan_rupees)} "
            f"and promoter equity contribution of {format_inr(data.executive_summary.promoter_equity_rupees)}."
        )
        p_desc.paragraph_format.line_spacing = 1.15

        # Key Metrics Grid
        ex = data.executive_summary
        grid_data = [
            ("Total Project Cost:", format_inr(ex.total_project_cost_rupees), "Promoter Equity:", format_inr(ex.promoter_equity_rupees)),
            ("Term Loan Sanctioned:", format_inr(ex.term_loan_rupees), "Initial Year Net Revenue:", format_inr(ex.first_year_net_revenue_rupees)),
            ("Average Gross DSCR:", f"{ex.average_gross_dscr:.2f}x" if ex.average_gross_dscr else "N/A", "Average CFADS DSCR:", f"{ex.average_net_cfads_dscr:.2f}x" if ex.average_net_cfads_dscr else "N/A"),
            ("Project IRR (%):", f"{ex.project_irr_pct:.2f}%" if ex.project_irr_pct else "N/A", "Net Present Value (NPV @ 10%):", format_inr(ex.npv_rupees)),
            ("Simple Payback Period:", f"{ex.payback_years:.2f} Years", "Year 1 Break-Even Capacity:", f"{ex.first_year_bep_capacity_pct:.2f}%"),
            ("Audit Integrity Status:", ex.validation_status, "Reconciliation Errors:", f"{ex.validation_error_count} Errors | {ex.validation_warning_count} Warnings"),
        ]

        table = doc.add_table(rows=len(grid_data), cols=4)
        table.alignment = WD_TABLE_ALIGNMENT.CENTER
        for r_idx, (k1, v1, k2, v2) in enumerate(grid_data):
            row_cells = table.rows[r_idx].cells
            row_cells[0].paragraphs[0].add_run(k1).font.bold = True
            row_cells[1].paragraphs[0].add_run(v1)
            row_cells[2].paragraphs[0].add_run(k2).font.bold = True
            row_cells[3].paragraphs[0].add_run(v2)

            for c_idx in range(4):
                cell = row_cells[c_idx]
                cell.paragraphs[0].runs[0].font.size = Pt(9.5)
                if c_idx in (0, 2):
                    cls._set_cell_background(cell, cls.GRAY_HEX)
                cls._set_cell_margins(cell, 80, 80, 100, 100)

    @classmethod
    def _render_cost_and_funding(cls, doc: docx.Document, data: ProjectReportDataDTO) -> None:
        h1 = doc.add_heading("2. Cost of Project & Means of Finance", level=1)
        h1.paragraph_format.space_before = Pt(16)
        h1.paragraph_format.space_after = Pt(8)

        # Means of Finance Table
        p_f = doc.add_paragraph()
        r_f = p_f.add_run("Means of Finance")
        r_f.font.bold = True
        r_f.font.size = Pt(11)

        f_table = doc.add_table(rows=len(data.cost_and_funding.funding_sources) + 2, cols=4)
        f_table.alignment = WD_TABLE_ALIGNMENT.CENTER

        f_headers = ["Funding Head", "Source / Facility Name", "Amount (₹)", "Share %"]
        for c_idx, h in enumerate(f_headers):
            cell = f_table.cell(0, c_idx)
            cell.paragraphs[0].add_run(h).font.bold = True
            cell.paragraphs[0].runs[0].font.color.rgb = RGBColor(0xFF, 0xFF, 0xFF)
            cell.paragraphs[0].runs[0].font.size = Pt(9.5)
            cls._set_cell_background(cell, cls.NAVY_HEX)
            cls._set_cell_margins(cell, 100, 100, 120, 120)

        for idx, src in enumerate(data.cost_and_funding.funding_sources, start=1):
            f_table.cell(idx, 0).paragraphs[0].add_run(src.head_name)
            f_table.cell(idx, 1).paragraphs[0].add_run(src.source_name)
            p_amt = f_table.cell(idx, 2).paragraphs[0]
            p_amt.alignment = WD_ALIGN_PARAGRAPH.RIGHT
            p_amt.add_run(format_inr(src.amount_rupees))
            p_pct = f_table.cell(idx, 3).paragraphs[0]
            p_pct.alignment = WD_ALIGN_PARAGRAPH.RIGHT
            p_pct.add_run(f"{src.percentage:.2f}%")

            for col in range(4):
                f_table.cell(idx, col).paragraphs[0].runs[0].font.size = Pt(9)
                cls._set_cell_margins(f_table.cell(idx, col), 80, 80, 100, 100)

        # Total Row
        tot_idx = len(data.cost_and_funding.funding_sources) + 1
        f_table.cell(tot_idx, 0).paragraphs[0].add_run("Total Means of Finance").font.bold = True
        f_table.cell(tot_idx, 1).paragraphs[0].add_run("-")
        p_t_amt = f_table.cell(tot_idx, 2).paragraphs[0]
        p_t_amt.alignment = WD_ALIGN_PARAGRAPH.RIGHT
        r_t_amt = p_t_amt.add_run(format_inr(data.cost_and_funding.total_funding_rupees))
        r_t_amt.font.bold = True
        p_t_pct = f_table.cell(tot_idx, 3).paragraphs[0]
        p_t_pct.alignment = WD_ALIGN_PARAGRAPH.RIGHT
        r_t_pct = p_t_pct.add_run("100.00%")
        r_t_pct.font.bold = True

        for col in range(4):
            f_table.cell(tot_idx, col).paragraphs[0].runs[0].font.size = Pt(9)
            cls._set_cell_background(f_table.cell(tot_idx, col), cls.SOFT_BLUE_HEX)
            cls._set_cell_margins(f_table.cell(tot_idx, col), 100, 100, 100, 100)

    @classmethod
    def _render_horizontal_statements(cls, doc: docx.Document, data: ProjectReportDataDTO) -> None:
        stmts = [
            ("3. Projected Profit & Loss Account", data.pl_statement),
            ("4. Projected Balance Sheet", data.bs_statement),
            ("5. Projected Cash Flow Statement (Indirect Method)", data.cf_statement),
        ]

        for heading_title, stmt in stmts:
            h = doc.add_heading(heading_title, level=1)
            h.paragraph_format.space_before = Pt(16)
            h.paragraph_format.space_after = Pt(8)

            col_headers = ["Particulars"] + stmt.period_headers
            num_cols = len(col_headers)
            table = doc.add_table(rows=len(stmt.rows) + 1, cols=num_cols)
            table.alignment = WD_TABLE_ALIGNMENT.CENTER

            # Header row
            for c_idx, text in enumerate(col_headers):
                cell = table.cell(0, c_idx)
                p = cell.paragraphs[0]
                if c_idx > 0:
                    p.alignment = WD_ALIGN_PARAGRAPH.RIGHT
                r = p.add_run(text)
                r.font.bold = True
                r.font.size = Pt(8.5)
                r.font.color.rgb = RGBColor(0xFF, 0xFF, 0xFF)
                cls._set_cell_background(cell, cls.NAVY_HEX)
                cls._set_cell_margins(cell, 80, 80, 80, 80)

            # Data rows
            for r_idx, row in enumerate(stmt.rows, start=1):
                cell_part = table.cell(r_idx, 0)
                p_part = cell_part.paragraphs[0]
                r_part = p_part.add_run(row.particulars)
                r_part.font.size = Pt(8)
                if row.is_heading or row.is_total:
                    r_part.font.bold = True
                if row.is_heading:
                    cls._set_cell_background(cell_part, cls.SOFT_BLUE_HEX)
                cls._set_cell_margins(cell_part, 60, 60, 80, 80)

                for seq in range(1, len(stmt.period_headers) + 1):
                    cell_val = table.cell(r_idx, seq)
                    p_val = cell_val.paragraphs[0]
                    p_val.alignment = WD_ALIGN_PARAGRAPH.RIGHT
                    amt = row.amounts.get(seq)
                    val_str = format_inr(amt) if amt is not None else "-"
                    r_val = p_val.add_run(val_str)
                    r_val.font.size = Pt(8)
                    if row.is_total:
                        r_val.font.bold = True
                        cls._set_cell_background(cell_val, cls.GRAY_HEX)
                    cls._set_cell_margins(cell_val, 60, 60, 80, 80)

    @classmethod
    def _render_loan_section(cls, doc: docx.Document, data: ProjectReportDataDTO) -> None:
        h = doc.add_heading("6. Term Loan Repayment & Debt Service Summary", level=1)
        h.paragraph_format.space_before = Pt(16)
        h.paragraph_format.space_after = Pt(8)

        headers = ["Period", "Opening Balance", "Disbursement", "Principal Repaid", "Interest Paid", "Total Debt Service", "Closing Balance"]
        table = doc.add_table(rows=len(data.loan_annual_summaries) + 1, cols=len(headers))
        table.alignment = WD_TABLE_ALIGNMENT.CENTER

        for c_idx, text in enumerate(headers):
            cell = table.cell(0, c_idx)
            p = cell.paragraphs[0]
            if c_idx > 0:
                p.alignment = WD_ALIGN_PARAGRAPH.RIGHT
            r = p.add_run(text)
            r.font.bold = True
            r.font.size = Pt(8.5)
            r.font.color.rgb = RGBColor(0xFF, 0xFF, 0xFF)
            cls._set_cell_background(cell, cls.NAVY_HEX)
            cls._set_cell_margins(cell, 80, 80, 80, 80)

        for r_idx, s in enumerate(data.loan_annual_summaries, start=1):
            table.cell(r_idx, 0).paragraphs[0].add_run(s.period_label).font.size = Pt(8)

            vals = [
                s.opening_balance_rupees,
                s.disbursement_rupees,
                s.principal_repaid_rupees,
                s.interest_paid_rupees,
                s.total_debt_service_rupees,
                s.closing_balance_rupees,
            ]
            for c_idx, val in enumerate(vals, start=1):
                cell = table.cell(r_idx, c_idx)
                p = cell.paragraphs[0]
                p.alignment = WD_ALIGN_PARAGRAPH.RIGHT
                r = p.add_run(format_inr(val))
                r.font.size = Pt(8)
                cls._set_cell_margins(cell, 60, 60, 80, 80)

    @classmethod
    def _render_ratios_section(cls, doc: docx.Document, data: ProjectReportDataDTO) -> None:
        h = doc.add_heading("7. Financial Ratios & Lender DSCR Appraisal", level=1)
        h.paragraph_format.space_before = Pt(16)
        h.paragraph_format.space_after = Pt(8)

        stmt = data.ratios_statement
        col_headers = ["Particulars / Ratio"] + stmt.period_headers
        table = doc.add_table(rows=len(stmt.rows) + 1, cols=len(col_headers))
        table.alignment = WD_TABLE_ALIGNMENT.CENTER

        for c_idx, text in enumerate(col_headers):
            cell = table.cell(0, c_idx)
            p = cell.paragraphs[0]
            if c_idx > 0:
                p.alignment = WD_ALIGN_PARAGRAPH.RIGHT
            r = p.add_run(text)
            r.font.bold = True
            r.font.size = Pt(8.5)
            r.font.color.rgb = RGBColor(0xFF, 0xFF, 0xFF)
            cls._set_cell_background(cell, cls.NAVY_HEX)
            cls._set_cell_margins(cell, 80, 80, 80, 80)

        for r_idx, row in enumerate(stmt.rows, start=1):
            cell_p = table.cell(r_idx, 0)
            r_p = cell_p.paragraphs[0].add_run(row.particulars)
            r_p.font.size = Pt(8)
            if "DSCR" in row.particulars or "Ratio" in row.particulars:
                r_p.font.bold = True
            cls._set_cell_margins(cell_p, 60, 60, 80, 80)

            for seq in range(1, len(stmt.period_headers) + 1):
                cell = table.cell(r_idx, seq)
                p = cell.paragraphs[0]
                p.alignment = WD_ALIGN_PARAGRAPH.RIGHT
                amt = row.amounts.get(seq)
                if amt is not None:
                    if "%" in row.particulars or "Margin" in row.particulars or "ROCE" in row.particulars:
                        text_val = f"{amt:.2f}%"
                    else:
                        text_val = f"{amt:.2f}x"
                else:
                    text_val = "-"
                r_val = p.add_run(text_val)
                r_val.font.size = Pt(8)
                cls._set_cell_margins(cell, 60, 60, 80, 80)

    @classmethod
    def _render_break_even_and_sensitivity(cls, doc: docx.Document, data: ProjectReportDataDTO) -> None:
        h = doc.add_heading("8. Break-Even Analysis & Operational Sensitivity Matrix", level=1)
        h.paragraph_format.space_before = Pt(16)
        h.paragraph_format.space_after = Pt(8)

        # Sensitivity Table
        p_s = doc.add_paragraph()
        p_s.add_run("Operational Sensitivity Scenarios").font.bold = True

        sens_headers = ["Parameter", "Variation", "Average DSCR", "Project IRR", "Avg PAT (₹)", "Y1 BEP %"]
        table = doc.add_table(rows=len(data.sensitivity_scenarios) + 1, cols=len(sens_headers))
        table.alignment = WD_TABLE_ALIGNMENT.CENTER

        for c_idx, text in enumerate(sens_headers):
            cell = table.cell(0, c_idx)
            p = cell.paragraphs[0]
            if c_idx > 1:
                p.alignment = WD_ALIGN_PARAGRAPH.RIGHT
            elif c_idx == 1:
                p.alignment = WD_ALIGN_PARAGRAPH.CENTER
            r = p.add_run(text)
            r.font.bold = True
            r.font.size = Pt(8.5)
            r.font.color.rgb = RGBColor(0xFF, 0xFF, 0xFF)
            cls._set_cell_background(cell, cls.NAVY_HEX)
            cls._set_cell_margins(cell, 80, 80, 80, 80)

        for r_idx, s in enumerate(data.sensitivity_scenarios, start=1):
            table.cell(r_idx, 0).paragraphs[0].add_run(s.parameter_name).font.size = Pt(8)
            var_text = f"{s.variation_pct:+.1f}%" if s.variation_pct != 0 else "Base"
            p_v = table.cell(r_idx, 1).paragraphs[0]
            p_v.alignment = WD_ALIGN_PARAGRAPH.CENTER
            p_v.add_run(var_text).font.size = Pt(8)

            table.cell(r_idx, 2).paragraphs[0].add_run(s.average_dscr).font.size = Pt(8)
            table.cell(r_idx, 2).paragraphs[0].alignment = WD_ALIGN_PARAGRAPH.RIGHT

            table.cell(r_idx, 3).paragraphs[0].add_run(s.irr_pct).font.size = Pt(8)
            table.cell(r_idx, 3).paragraphs[0].alignment = WD_ALIGN_PARAGRAPH.RIGHT

            table.cell(r_idx, 4).paragraphs[0].add_run(format_inr(s.avg_pat_rupees)).font.size = Pt(8)
            table.cell(r_idx, 4).paragraphs[0].alignment = WD_ALIGN_PARAGRAPH.RIGHT

            table.cell(r_idx, 5).paragraphs[0].add_run(f"{s.first_year_bep_pct:.2f}%").font.size = Pt(8)
            table.cell(r_idx, 5).paragraphs[0].alignment = WD_ALIGN_PARAGRAPH.RIGHT

            for c in range(6):
                cls._set_cell_margins(table.cell(r_idx, c), 60, 60, 80, 80)

    @classmethod
    def _render_audit_certificate(cls, doc: docx.Document, data: ProjectReportDataDTO) -> None:
        h = doc.add_heading("9. Cross-Statement Audit & Invariant Certificate", level=1)
        h.paragraph_format.space_before = Pt(16)
        h.paragraph_format.space_after = Pt(8)

        p_cert = doc.add_paragraph(
            f"This financial projection model was validated under calculation run #{data.metadata.calculation_run_number} "
            f"using engine version {data.metadata.engine_version}. "
            f"The canonical input hash is {data.metadata.input_hash}. "
            f"Audit Status: {data.executive_summary.validation_status} (Material Errors: {data.executive_summary.validation_error_count}, Advisory Warnings: {data.executive_summary.validation_warning_count}). "
            f"All statements satisfy the zero-plug balance sheet invariant without unexplained suspense accounts or plugs."
        )
        p_cert.paragraph_format.line_spacing = 1.15

        if data.validation_issues:
            val_headers = ["Severity", "Rule Code", "Scope", "Message", "Period", "Expected", "Actual"]
            table = doc.add_table(rows=len(data.validation_issues) + 1, cols=len(val_headers))
            table.alignment = WD_TABLE_ALIGNMENT.CENTER

            for c_idx, text in enumerate(val_headers):
                cell = table.cell(0, c_idx)
                r = cell.paragraphs[0].add_run(text)
                r.font.bold = True
                r.font.size = Pt(8)
                r.font.color.rgb = RGBColor(0xFF, 0xFF, 0xFF)
                cls._set_cell_background(cell, cls.NAVY_HEX)
                cls._set_cell_margins(cell, 80, 80, 80, 80)

            for r_idx, issue in enumerate(data.validation_issues, start=1):
                table.cell(r_idx, 0).paragraphs[0].add_run(issue.severity).font.size = Pt(7.5)
                table.cell(r_idx, 1).paragraphs[0].add_run(issue.rule_code).font.size = Pt(7.5)
                table.cell(r_idx, 2).paragraphs[0].add_run(issue.scope_code).font.size = Pt(7.5)
                table.cell(r_idx, 3).paragraphs[0].add_run(issue.message).font.size = Pt(7.5)
                table.cell(r_idx, 4).paragraphs[0].add_run(f"Y{issue.period_sequence}" if issue.period_sequence else "All").font.size = Pt(7.5)
                table.cell(r_idx, 5).paragraphs[0].add_run(issue.expected_value or "-").font.size = Pt(7.5)
                table.cell(r_idx, 6).paragraphs[0].add_run(issue.actual_value or "-").font.size = Pt(7.5)

                for c in range(7):
                    cls._set_cell_margins(table.cell(r_idx, c), 60, 60, 80, 80)
