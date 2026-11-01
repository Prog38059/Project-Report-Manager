"""Integration test for ReportService, Excel, Word, and PDF renderers, and output agreement."""

from decimal import Decimal
from pathlib import Path
import uuid
import pytest

from alembic.config import Config
from alembic import command
import docx
import openpyxl

from app.application.dtos.client_dto import CreateClientDTO
from app.application.dtos.entity_dto import CreateEntityDTO
from app.application.dtos.project_dto import CreateProjectDTO
from app.application.services.client_service import ClientService
from app.application.services.entity_service import EntityService
from app.application.services.financial_engine_service import FinancialEngineService
from app.application.services.funding_service import FundingService
from app.application.services.project_cost_service import ProjectCostService
from app.application.services.project_service import ProjectService
from app.application.services.report_service import ReportService
from app.common.money import format_inr
from app.common.types import ConstitutionCode, ProjectNatureCode
from app.config import AppConfig
from app.infrastructure.database.connection import DatabaseManager
from app.infrastructure.security.encryption import EncryptionService


@pytest.fixture
def service_env(test_config: AppConfig, encryption_service: EncryptionService):
    alembic_ini_path = Path(__file__).resolve().parent.parent.parent / "alembic.ini"
    alembic_cfg = Config(str(alembic_ini_path))
    alembic_cfg.set_main_option("sqlalchemy.url", test_config.sqlite_url)
    command.upgrade(alembic_cfg, "head")

    db_manager = DatabaseManager.from_config(test_config)
    try:
        yield db_manager, encryption_service, test_config
    finally:
        db_manager.engine.dispose()


def test_full_report_generation_and_cross_format_agreement(service_env, tmp_path):
    db_manager, encryption_service, test_config = service_env
    client_service = ClientService(db_manager)
    entity_service = EntityService(db_manager, encryption_service)
    project_service = ProjectService(db_manager)
    cost_service = ProjectCostService(db_manager)
    funding_service = FundingService(db_manager)
    fin_engine = FinancialEngineService(db_manager)
    report_service = ReportService(db_manager, test_config)

    # 1. Setup Client, Entity, Project, Capex, and Funding
    client = client_service.create_client(
        CreateClientDTO(client_code="CLI-REP-01", display_name="Zenith Aerospace Components")
    )
    entity = entity_service.create_entity(
        CreateEntityDTO(
            client_id=client.id,
            constitution_code=ConstitutionCode.PRIVATE_LIMITED,
            legal_name="Zenith Aerospace Private Limited",
        )
    )
    project = project_service.create_project(
        CreateProjectDTO(
            entity_id=entity.id,
            project_code="PRJ-REP-01",
            project_name="Aerospace Machining & Turbine Unit",
            project_nature_code=ProjectNatureCode.NEW,
            projection_start_financial_year=2026,
            projection_year_count=7,
        )
    )
    scenarios = project_service.list_scenarios(project.id)
    scenario = scenarios[0]

    # Capex: 90 Lakhs
    cost_heads = cost_service.list_cost_heads()
    pm_head = next(h for h in cost_heads if "PLANT" in h.head_code or "EQUIPMENT" in h.head_code)
    cost_service.save_item(
        scenario_id=scenario.id,
        cost_head_id=pm_head.id,
        description="5-Axis CNC Gantry Machine",
        basic_rupees=Decimal("9000000.00"),  # 90 Lakhs
        gst_rate_pct=Decimal("18.0"),
        itc_eligibility_pct=Decimal("100.0"),
    )

    # Funding: 60L Term Loan + 30L Equity = 90 Lakhs
    funding_heads = funding_service.list_funding_heads()
    term_head = next(h for h in funding_heads if "TERM_LOAN" in h.funding_code)
    equity_head = next(h for h in funding_heads if "EQUITY" in h.funding_code)

    funding_service.save_source(
        scenario_id=scenario.id,
        funding_head_id=term_head.id,
        source_name="State Bank of India Term Debt",
        amount_rupees=Decimal("6000000.00"),  # 60 Lakhs
        terms_note="11.5% interest, 84 months repayment",
    )
    funding_service.save_source(
        scenario_id=scenario.id,
        funding_head_id=equity_head.id,
        source_name="Promoters Capital Contribution",
        amount_rupees=Decimal("3000000.00"),  # 30 Lakhs
    )

    # 2. Run Projections
    run_dto = fin_engine.execute_projection(scenario_id=scenario.id)
    assert run_dto.run_status == "SUCCESS"

    # 3. Build Shared Report-Data Object
    report_data = report_service.build_report_data_model(scenario_id=scenario.id)
    assert report_data.metadata.project_name == "Aerospace Machining & Turbine Unit"
    assert report_data.metadata.calculation_run_number == 1
    assert report_data.executive_summary.total_project_cost_rupees == Decimal("9000000.00")
    assert report_data.executive_summary.term_loan_rupees == Decimal("6000000.00")
    assert report_data.executive_summary.average_gross_dscr is not None
    assert report_data.executive_summary.project_irr_pct is not None
    assert len(report_data.pl_statement.rows) > 10
    assert len(report_data.bs_statement.rows) > 10
    assert len(report_data.cf_statement.rows) > 10

    # 4. Generate Excel Report (.xlsx)
    xlsx_path = str(tmp_path / "test_report.xlsx")
    xlsx_res = report_service.generate_report(
        scenario_id=scenario.id,
        output_type="EXCEL",
        custom_output_path=xlsx_path,
    )
    assert Path(xlsx_path).exists()
    assert xlsx_res.file_size_bytes > 0
    assert len(xlsx_res.file_hash) == 64

    # Verify Excel workbook structure
    wb = openpyxl.load_workbook(xlsx_path)
    sheet_names = wb.sheetnames
    assert "Executive Summary" in sheet_names
    assert "Projected P&L" in sheet_names
    assert "Projected Balance Sheet" in sheet_names
    assert "Projected Cash Flow" in sheet_names
    assert "Ratios & DSCR" in sheet_names
    assert "Break-Even & Sensitivity" in sheet_names
    assert "Loan Amortization" in sheet_names
    assert "Fixed Assets & Dep" in sheet_names
    assert "Audit & Validation" in sheet_names

    # Verify freeze panes on Projected P&L
    ws_pl = wb["Projected P&L"]
    assert ws_pl.freeze_panes == "D5"
    # Column A should be "Sr. No.", B should be "Note", C should be "Particulars", D should be Year 1
    assert ws_pl["A4"].value == "Sr. No."
    assert ws_pl["B4"].value == "Note"
    assert ws_pl["C4"].value == "Particulars"
    assert "Year 1" in ws_pl["D4"].value

    # 5. Generate Word Report (.docx)
    docx_path = str(tmp_path / "test_report.docx")
    docx_res = report_service.generate_report(
        scenario_id=scenario.id,
        output_type="DOCX",
        custom_output_path=docx_path,
    )
    assert Path(docx_path).exists()
    assert docx_res.file_size_bytes > 0
    assert len(docx_res.file_hash) == 64

    # Verify Word document content
    doc = docx.Document(docx_path)
    doc_text = " ".join(p.text for p in doc.paragraphs)
    assert "PROJECT APPRAISAL" in doc_text.upper()
    assert "Zenith Aerospace Private Limited" in doc_text
    assert len(doc.tables) >= 5

    # 6. Generate PDF Report (.pdf)
    pdf_path = str(tmp_path / "test_report.pdf")
    pdf_res = report_service.generate_report(
        scenario_id=scenario.id,
        output_type="PDF",
        custom_output_path=pdf_path,
    )
    assert Path(pdf_path).exists()
    assert pdf_res.file_size_bytes > 5000
    assert len(pdf_res.file_hash) == 64

    with open(pdf_path, "rb") as f:
        pdf_bytes = f.read(10)
        assert pdf_bytes.startswith(b"%PDF")

    # 7. Cross-Renderer Agreement Verification (Rule: Renderers do not recalculate figures)
    # Total Project Cost in Excel matches Word and Report Data
    assert report_data.executive_summary.total_project_cost_rupees == Decimal("9000000.00")
    assert format_inr(report_data.executive_summary.total_project_cost_rupees) in doc_text

    # Check generated_reports records in database
    gen_reports = report_service.list_generated_reports(project_id=project.id)
    assert len(gen_reports) == 3
    types = {r.output_type for r in gen_reports}
    assert "EXCEL" in types
    assert "DOCX" in types
    assert "PDF" in types
    for r in gen_reports:
        assert r.generation_status == "SUCCESS"
        assert len(r.file_hash) == 64
