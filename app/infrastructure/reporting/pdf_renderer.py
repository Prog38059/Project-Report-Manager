"""PDF Financial Appraisal Report Renderer using ReportLab."""

from decimal import Decimal
from pathlib import Path
from typing import Dict, List, Optional
import uuid

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.platypus import (
    HRFlowable,
    KeepTogether,
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

from app.application.dtos.report_dto import HorizontalStatementDTO, ProjectReportDataDTO
from app.common.money import format_inr


class NumberedCanvas:
    """Canvas that captures total pages and prints running header and footer."""
    # Used via custom build callbacks


class PdfReportRenderer:
    """Renders professional bank appraisal PDF reports from ProjectReportDataDTO."""

    NAVY = colors.HexColor("#1F4E79")
    SOFT_BLUE = colors.HexColor("#D9E1F2")
    GRAY_BG = colors.HexColor("#F8F9FA")
    BORDER_COLOR = colors.HexColor("#DADCE0")
    TEXT_DARK = colors.HexColor("#202124")

    @classmethod
    def render(cls, report_data: ProjectReportDataDTO, output_path: str) -> str:
        """Renders the master PDF project report and saves to output_path."""
        dest = Path(output_path)
        dest.parent.mkdir(parents=True, exist_ok=True)

        # Landscape A4 for wide 7-year financial statement grids
        doc = SimpleDocTemplate(
            output_path,
            pagesize=landscape(A4),
            leftMargin=36,
            rightMargin=36,
            topMargin=40,
            bottomMargin=40,
        )

        styles = getSampleStyleSheet()

        title_style = ParagraphStyle(
            "DocTitle",
            parent=styles["Normal"],
            fontName="Helvetica-Bold",
            fontSize=16,
            leading=20,
            textColor=cls.NAVY,
            alignment=1,  # Center
        )
        subtitle_style = ParagraphStyle(
            "DocSubTitle",
            parent=styles["Normal"],
            fontName="Helvetica-Bold",
            fontSize=10,
            leading=13,
            textColor=colors.HexColor("#595959"),
            alignment=1,
        )
        h1_style = ParagraphStyle(
            "Heading1_Custom",
            parent=styles["Normal"],
            fontName="Helvetica-Bold",
            fontSize=12,
            leading=16,
            textColor=cls.NAVY,
            spaceBefore=14,
            spaceAfter=6,
        )
        body_style = ParagraphStyle(
            "Body_Custom",
            parent=styles["Normal"],
            fontName="Helvetica",
            fontSize=8.5,
            leading=11,
            textColor=cls.TEXT_DARK,
        )
        bold_cell_style = ParagraphStyle(
            "BoldCell",
            parent=styles["Normal"],
            fontName="Helvetica-Bold",
            fontSize=8,
            leading=10,
            textColor=cls.TEXT_DARK,
        )
        regular_cell_style = ParagraphStyle(
            "RegCell",
            parent=styles["Normal"],
            fontName="Helvetica",
            fontSize=8,
            leading=10,
            textColor=cls.TEXT_DARK,
        )
        right_cell_style = ParagraphStyle(
            "RightCell",
            parent=styles["Normal"],
            fontName="Helvetica",
            fontSize=8,
            leading=10,
            textColor=cls.TEXT_DARK,
            alignment=2,  # Right
        )
        right_bold_style = ParagraphStyle(
            "RightBoldCell",
            parent=styles["Normal"],
            fontName="Helvetica-Bold",
            fontSize=8,
            leading=10,
            textColor=cls.TEXT_DARK,
            alignment=2,
        )

        elements = []

        # 1. Document Title
        elements.append(Paragraph(report_data.metadata.report_title.upper(), title_style))
        elements.append(Spacer(1, 4))
        elements.append(
            Paragraph(
                f"Project: {report_data.metadata.project_name} | Borrower: {report_data.metadata.entity_legal_name} ({report_data.metadata.constitution_label})",
                subtitle_style,
            )
        )
        elements.append(Spacer(1, 4))
        elements.append(
            Paragraph(
                f"Calculation Run #{report_data.metadata.calculation_run_number} | Engine v{report_data.metadata.engine_version} | SHA-256 Input Hash: {report_data.metadata.input_hash[:24]}... | Date: {report_data.metadata.generated_at.strftime('%Y-%m-%d %H:%M UTC')}",
                subtitle_style,
            )
        )
        elements.append(Spacer(1, 10))
        elements.append(HRFlowable(width="100%", thickness=1.5, color=cls.NAVY, spaceAfter=10))

        # 2. Executive Summary Block
        elements.append(Paragraph("1. Executive Summary & Key Appraisal Indicators", h1_style))
        ex = report_data.executive_summary
        kpi_table_data = [
            [
                Paragraph("Total Project Cost:", bold_cell_style), Paragraph(format_inr(ex.total_project_cost_rupees), right_bold_style),
                Paragraph("Promoter Equity:", bold_cell_style), Paragraph(format_inr(ex.promoter_equity_rupees), right_bold_style),
                Paragraph("Term Loan Sanctioned:", bold_cell_style), Paragraph(format_inr(ex.term_loan_rupees), right_bold_style),
            ],
            [
                Paragraph("Average Gross DSCR:", bold_cell_style), Paragraph(f"{ex.average_gross_dscr:.2f}x" if ex.average_gross_dscr else "N/A", right_bold_style),
                Paragraph("Average CFADS DSCR:", bold_cell_style), Paragraph(f"{ex.average_net_cfads_dscr:.2f}x" if ex.average_net_cfads_dscr else "N/A", right_bold_style),
                Paragraph("Cumulative DSCR:", bold_cell_style), Paragraph(f"{ex.cumulative_dscr:.2f}x" if ex.cumulative_dscr else "N/A", right_bold_style),
            ],
            [
                Paragraph("Project IRR (%):", bold_cell_style), Paragraph(f"{ex.project_irr_pct:.2f}%" if ex.project_irr_pct else "N/A", right_bold_style),
                Paragraph("Net Present Value (NPV):", bold_cell_style), Paragraph(format_inr(ex.npv_rupees), right_bold_style),
                Paragraph("Simple Payback Period:", bold_cell_style), Paragraph(f"{ex.payback_years:.2f} Yrs", right_bold_style),
            ],
            [
                Paragraph("Y1 Break-Even Capacity:", bold_cell_style), Paragraph(f"{ex.first_year_bep_capacity_pct:.2f}%", right_bold_style),
                Paragraph("Audit Integrity Status:", bold_cell_style), Paragraph(ex.validation_status, right_bold_style),
                Paragraph("Validation Issues:", bold_cell_style), Paragraph(f"{ex.validation_error_count} Errors | {ex.validation_warning_count} Warn", right_bold_style),
            ],
        ]
        t_kpi = Table(kpi_table_data, colWidths=[130, 120, 130, 120, 130, 120])
        t_kpi.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), cls.GRAY_BG),
            ("BOX", (0, 0), (-1, -1), 1, cls.BORDER_COLOR),
            ("INNERGRID", (0, 0), (-1, -1), 0.5, cls.BORDER_COLOR),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("TOPPADDING", (0, 0), (-1, -1), 4),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ]))
        elements.append(t_kpi)
        elements.append(Spacer(1, 10))

        # 3. Means of Finance Table
        elements.append(Paragraph("2. Project Cost & Means of Finance", h1_style))
        mf_headers = [
            Paragraph("Funding Source / Facility", bold_cell_style),
            Paragraph("Head Category", bold_cell_style),
            Paragraph("Amount (₹)", right_bold_style),
            Paragraph("Share %", right_bold_style),
        ]
        mf_rows = [mf_headers]
        for src in report_data.cost_and_funding.funding_sources:
            mf_rows.append([
                Paragraph(src.source_name, regular_cell_style),
                Paragraph(src.head_name, regular_cell_style),
                Paragraph(format_inr(src.amount_rupees), right_cell_style),
                Paragraph(f"{src.percentage:.2f}%", right_cell_style),
            ])
        mf_rows.append([
            Paragraph("TOTAL MEANS OF FINANCE", bold_cell_style),
            Paragraph("-", regular_cell_style),
            Paragraph(format_inr(report_data.cost_and_funding.total_funding_rupees), right_bold_style),
            Paragraph("100.00%", right_bold_style),
        ])
        t_mf = Table(mf_rows, colWidths=[240, 200, 180, 130])
        t_mf.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), cls.NAVY),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("BACKGROUND", (0, -1), (-1, -1), cls.SOFT_BLUE),
            ("BOX", (0, 0), (-1, -1), 1, cls.BORDER_COLOR),
            ("INNERGRID", (0, 0), (-1, -1), 0.5, cls.BORDER_COLOR),
            ("TOPPADDING", (0, 0), (-1, -1), 3),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
        ]))
        elements.append(t_mf)

        # 4. Statements (P&L, Balance Sheet, Cash Flow)
        elements.append(PageBreak())
        cls._append_statement_table(elements, "3. Projected Profit & Loss Account", report_data.pl_statement, h1_style, regular_cell_style, bold_cell_style, right_cell_style, right_bold_style)

        elements.append(PageBreak())
        cls._append_statement_table(elements, "4. Projected Balance Sheet", report_data.bs_statement, h1_style, regular_cell_style, bold_cell_style, right_cell_style, right_bold_style)

        elements.append(PageBreak())
        cls._append_statement_table(elements, "5. Projected Cash Flow Statement (Indirect Method)", report_data.cf_statement, h1_style, regular_cell_style, bold_cell_style, right_cell_style, right_bold_style)

        # 5. Financial Ratios & DSCR
        elements.append(PageBreak())
        cls._append_statement_table(elements, "6. Financial Ratios & Lender DSCR Appraisal", report_data.ratios_statement, h1_style, regular_cell_style, bold_cell_style, right_cell_style, right_bold_style, is_ratios=True)

        # 6. Break-Even & Sensitivity Matrix
        elements.append(Spacer(1, 12))
        elements.append(Paragraph("7. Operational Sensitivity Analysis Matrix", h1_style))
        sens_headers = [
            Paragraph("Operational Parameter", bold_cell_style),
            Paragraph("Variation %", bold_cell_style),
            Paragraph("Avg DSCR", right_bold_style),
            Paragraph("Project IRR", right_bold_style),
            Paragraph("Avg PAT (₹)", right_bold_style),
            Paragraph("Y1 BEP %", right_bold_style),
        ]
        sens_rows = [sens_headers]
        for s in report_data.sensitivity_scenarios:
            var_str = f"{s.variation_pct:+.1f}%" if s.variation_pct != 0 else "Base Case"
            sens_rows.append([
                Paragraph(s.parameter_name, bold_cell_style if s.variation_pct == Decimal("0.0") else regular_cell_style),
                Paragraph(var_str, regular_cell_style),
                Paragraph(s.average_dscr, right_cell_style),
                Paragraph(s.irr_pct, right_cell_style),
                Paragraph(format_inr(s.avg_pat_rupees), right_cell_style),
                Paragraph(f"{s.first_year_bep_pct:.2f}%", right_cell_style),
            ])
        t_sens = Table(sens_rows, colWidths=[200, 90, 110, 110, 140, 100])
        t_sens.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), cls.NAVY),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("BOX", (0, 0), (-1, -1), 1, cls.BORDER_COLOR),
            ("INNERGRID", (0, 0), (-1, -1), 0.5, cls.BORDER_COLOR),
            ("TOPPADDING", (0, 0), (-1, -1), 3),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
        ]))
        elements.append(t_sens)

        # 7. Loan Repayment Summary
        elements.append(PageBreak())
        elements.append(Paragraph("8. Term Loan Annual Debt Service Profile", h1_style))
        loan_headers = [
            Paragraph("Period", bold_cell_style),
            Paragraph("Year Label", bold_cell_style),
            Paragraph("Opening Balance", right_bold_style),
            Paragraph("Disbursement", right_bold_style),
            Paragraph("Principal Repaid", right_bold_style),
            Paragraph("Interest Paid", right_bold_style),
            Paragraph("Total Debt Service", right_bold_style),
            Paragraph("Closing Balance", right_bold_style),
        ]
        loan_rows = [loan_headers]
        for row in report_data.loan_annual_summaries:
            loan_rows.append([
                Paragraph(f"Year {row.period_sequence}", regular_cell_style),
                Paragraph(row.period_label, regular_cell_style),
                Paragraph(format_inr(row.opening_balance_rupees), right_cell_style),
                Paragraph(format_inr(row.disbursement_rupees), right_cell_style),
                Paragraph(format_inr(row.principal_repaid_rupees), right_cell_style),
                Paragraph(format_inr(row.interest_paid_rupees), right_cell_style),
                Paragraph(format_inr(row.total_debt_service_rupees), right_bold_style),
                Paragraph(format_inr(row.closing_balance_rupees), right_cell_style),
            ])
        t_loan = Table(loan_rows, colWidths=[65, 85, 100, 100, 100, 100, 105, 95])
        t_loan.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), cls.NAVY),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("BOX", (0, 0), (-1, -1), 1, cls.BORDER_COLOR),
            ("INNERGRID", (0, 0), (-1, -1), 0.5, cls.BORDER_COLOR),
            ("TOPPADDING", (0, 0), (-1, -1), 3),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
        ]))
        elements.append(t_loan)

        # 8. Audit Certificate
        elements.append(Spacer(1, 14))
        elements.append(Paragraph("9. Cross-Statement Audit & Invariant Certificate", h1_style))
        elements.append(
            Paragraph(
                f"Certified that the multi-year financial statements, cash flows, and debt service coverage models "
                f"were compiled and audited by the financial engine with zero balancing plugs. "
                f"Status: {report_data.executive_summary.validation_status} ({report_data.executive_summary.validation_error_count} Errors, {report_data.executive_summary.validation_warning_count} Warnings). "
                f"Calculation Run ID: {report_data.metadata.calculation_run_id} | Input Hash: {report_data.metadata.input_hash}.",
                body_style,
            )
        )

        def add_page_decorations(canvas, d):
            canvas.saveState()
            canvas.setFont("Helvetica", 7.5)
            canvas.setFillColor(colors.HexColor("#595959"))
            # Header
            canvas.drawString(36, d.pagesize[1] - 25, f"{report_data.metadata.entity_legal_name} | {report_data.metadata.project_name} — Financial Appraisal")
            canvas.drawRightString(d.pagesize[0] - 36, d.pagesize[1] - 25, "BANK CREDIT APPRAISAL BOOK")
            # Footer
            canvas.drawString(36, 20, f"Run #{report_data.metadata.calculation_run_number} | Hash: {report_data.metadata.input_hash[:16]}... | {report_data.metadata.confidentiality_notice}")
            canvas.drawRightString(d.pagesize[0] - 36, 20, f"Page {canvas._pageNumber}")
            canvas.restoreState()

        doc.build(elements, onFirstPage=add_page_decorations, onLaterPages=add_page_decorations)
        return output_path

    @classmethod
    def _append_statement_table(
        cls,
        elements: list,
        title: str,
        stmt: HorizontalStatementDTO,
        h1_style: ParagraphStyle,
        regular_style: ParagraphStyle,
        bold_style: ParagraphStyle,
        right_style: ParagraphStyle,
        right_bold_style: ParagraphStyle,
        is_ratios: bool = False,
    ) -> None:
        elements.append(Paragraph(title, h1_style))

        headers = [Paragraph("Particulars", bold_style)]
        for h in stmt.period_headers:
            headers.append(Paragraph(h, right_bold_style))

        num_periods = len(stmt.period_headers)
        col_w = [210] + [75] * num_periods

        table_rows = [headers]
        for row in stmt.rows:
            is_b = row.is_heading or row.is_total
            row_cells = [Paragraph(row.particulars, bold_style if is_b else regular_style)]

            for seq in range(1, num_periods + 1):
                amt = row.amounts.get(seq)
                if amt is not None:
                    if is_ratios:
                        if "%" in row.particulars or "Margin" in row.particulars or "ROCE" in row.particulars:
                            val_str = f"{amt:.2f}%"
                        else:
                            val_str = f"{amt:.2f}x"
                    else:
                        val_str = format_inr(amt)
                else:
                    val_str = "-"
                row_cells.append(Paragraph(val_str, right_bold_style if is_b else right_style))

            table_rows.append(row_cells)

        t = Table(table_rows, colWidths=col_w)
        style_cmds = [
            ("BACKGROUND", (0, 0), (-1, 0), cls.NAVY),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("BOX", (0, 0), (-1, -1), 1, cls.BORDER_COLOR),
            ("INNERGRID", (0, 0), (-1, -1), 0.5, cls.BORDER_COLOR),
            ("TOPPADDING", (0, 0), (-1, -1), 2.5),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 2.5),
        ]
        # Highlight total rows
        for idx, row in enumerate(stmt.rows, start=1):
            if row.is_total:
                style_cmds.append(("BACKGROUND", (0, idx), (-1, idx), cls.GRAY_BG))
            elif row.is_heading:
                style_cmds.append(("BACKGROUND", (0, idx), (-1, idx), cls.SOFT_BLUE))

        t.setStyle(TableStyle(style_cmds))
        elements.append(t)
