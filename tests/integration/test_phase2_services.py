"""Integration tests for Phase 2 services (Costs, Funding, Revenue, Expenses, Templates, Historical)."""

from decimal import Decimal
import pytest
from datetime import date
from pathlib import Path
from alembic.config import Config
from alembic import command

from app.config import AppConfig
from app.infrastructure.database.connection import DatabaseManager
from app.infrastructure.security.encryption import EncryptionService
from app.application.services.client_service import ClientService
from app.application.services.entity_service import EntityService
from app.application.services.project_service import ProjectService
from app.application.services.project_cost_service import ProjectCostService
from app.application.services.funding_service import FundingService
from app.application.services.revenue_service import RevenueService
from app.application.services.expense_service import ExpenseService
from app.application.services.template_service import TemplateService
from app.application.services.historical_service import HistoricalService
from app.application.dtos.client_dto import CreateClientDTO
from app.application.dtos.entity_dto import CreateEntityDTO
from app.application.dtos.project_dto import CreateProjectDTO
from app.common.types import ConstitutionCode, ProjectNatureCode


@pytest.fixture
def phase2_services(test_config: AppConfig, encryption_service: EncryptionService):
    # Ensure migrations are applied on fresh database
    alembic_ini_path = Path(__file__).resolve().parent.parent.parent / "alembic.ini"
    alembic_cfg = Config(str(alembic_ini_path))
    alembic_cfg.set_main_option("sqlalchemy.url", test_config.sqlite_url)
    command.upgrade(alembic_cfg, "head")

    test_db = DatabaseManager.from_config(test_config)
    try:
        client_service = ClientService(test_db)
        entity_service = EntityService(test_db, encryption_service)
        project_service = ProjectService(test_db)
        cost_service = ProjectCostService(test_db)
        funding_service = FundingService(test_db)
        rev_service = RevenueService(test_db)
        exp_service = ExpenseService(test_db)
        template_service = TemplateService(test_db)
        hist_service = HistoricalService(test_db)

        # Create baseline client, entity, and project
        client = client_service.create_client(CreateClientDTO(client_code="C-P2", display_name="Phase 2 Client"))
        entity = entity_service.create_entity(CreateEntityDTO(client_id=client.id, constitution_code=ConstitutionCode.PRIVATE_LIMITED, legal_name="Apex Industries Pvt Ltd"))
        project = project_service.create_project(CreateProjectDTO(
            entity_id=entity.id,
            project_code="PRJ-P2-01",
            project_name="Precision Component Plant",
            project_nature_code=ProjectNatureCode.NEW,
            projection_year_count=7,
            projection_start_financial_year=2026,
        ))
        scenarios = project_service.list_scenarios(project.id)
        scenario_id = scenarios[0].id

        yield {
            "project": project,
            "project_service": project_service,
            "scenario_id": scenario_id,
            "cost_service": cost_service,
            "funding_service": funding_service,
            "rev_service": rev_service,
            "exp_service": exp_service,
            "template_service": template_service,
            "hist_service": hist_service,
        }
    finally:
        test_db.engine.dispose()


def test_project_cost_and_funding_reconciliation_workflow(phase2_services):
    """Test full cycle of adding costs, funding sources, and verifying gap reconciliation."""
    cost_service: ProjectCostService = phase2_services["cost_service"]
    funding_service: FundingService = phase2_services["funding_service"]
    scenario_id = phase2_services["scenario_id"]

    # 1. Check cost heads loaded from migration
    cost_heads = cost_service.list_cost_heads()
    assert len(cost_heads) >= 10
    plant_head = next(h for h in cost_heads if h.head_code == "PLANT_MACHINERY")
    land_head = next(h for h in cost_heads if h.head_code == "LAND")

    # 2. Add Cost Items
    # Item 1: Plant & Machinery (10 Lakhs + 18% GST with full ITC)
    item1 = cost_service.save_item(
        scenario_id=scenario_id,
        cost_head_id=plant_head.id,
        description="CNC Lathe Machine",
        basic_rupees=Decimal("1000000.00"),
        gst_rate_pct=Decimal("18.0"),
        itc_eligibility_pct=Decimal("100.0"),
        supplier_name="Ace Micromatic",
    )
    assert item1.basic_amount_rupees == Decimal("1000000.00")
    assert item1.capitalised_amount_rupees == Decimal("1000000.00")
    assert item1.project_cash_requirement_rupees == Decimal("1180000.00")

    # Item 2: Land (5 Lakhs, no GST)
    item2 = cost_service.save_item(
        scenario_id=scenario_id,
        cost_head_id=land_head.id,
        description="Industrial Plot 1 Acre",
        basic_rupees=Decimal("500000.00"),
    )
    assert item2.capitalised_amount_rupees == Decimal("500000.00")
    assert item2.project_cash_requirement_rupees == Decimal("500000.00")

    # Verify summary
    summary = cost_service.get_cost_summary(scenario_id)
    assert summary.total_basic_rupees == Decimal("1500000.00")
    assert summary.total_cash_requirement_rupees == Decimal("1680000.00")

    # 3. Add Funding Sources
    funding_heads = funding_service.list_funding_heads()
    assert len(funding_heads) >= 6
    equity_head = next(h for h in funding_heads if h.funding_code == "PROMOTER_EQUITY")
    loan_head = next(h for h in funding_heads if h.funding_code == "TERM_LOAN_BANK")

    # Add Promoter Equity: 6,80,000
    funding_service.save_source(
        scenario_id=scenario_id,
        funding_head_id=equity_head.id,
        source_name="Promoter Capital",
        amount_rupees=Decimal("680000.00"),
    )
    # Add Bank Term Loan: 10,00,000
    funding_service.save_source(
        scenario_id=scenario_id,
        funding_head_id=loan_head.id,
        source_name="Bank Term Loan",
        amount_rupees=Decimal("1000000.00"),
    )

    # 4. Reconcile funding
    recon = funding_service.get_reconciliation(scenario_id, summary.total_cash_requirement_rupees)
    assert recon.total_project_cost_rupees == Decimal("1680000.00")
    assert recon.total_funding_sources_rupees == Decimal("1680000.00")
    assert recon.funding_gap_rupees == Decimal("0.00")
    assert recon.is_balanced is True
    assert recon.debt_equity_ratio == "1.47 : 1"


def test_starter_industry_templates_and_revenue_streams(phase2_services):
    """Test loading templates, applying a template to a scenario, and calculating revenue forecast."""
    template_service: TemplateService = phase2_services["template_service"]
    rev_service: RevenueService = phase2_services["rev_service"]
    scenario_id = phase2_services["scenario_id"]
    project = phase2_services["project"]

    # 1. Verify 10 starter templates
    templates = template_service.list_templates()
    assert len(templates) == 10
    manufacturing = template_service.get_template("IND_MANUFACTURING")
    assert manufacturing is not None
    assert manufacturing.industry_name == "Manufacturing"
    assert len(manufacturing.fields) >= 1

    # 2. Apply starter template to scenario
    template_service.apply_starter_template(scenario_id, "IND_MANUFACTURING")
    streams = rev_service.list_streams(scenario_id)
    assert len(streams) == 1
    assert streams[0].stream_code == "REV_MAIN_PROD"
    assert streams[0].method_code == "CAPACITY_UTILISATION_PRICE"

    # 3. List multi-year forecasts across 7 projection periods
    forecasts = rev_service.list_forecasts_for_stream(streams[0].id, project.id)
    assert len(forecasts) == 7
    assert forecasts[0].period_sequence == 1
    assert forecasts[6].period_sequence == 7


def test_historical_statements_service(phase2_services):
    """Test historical statement line persistence."""
    hist_service: HistoricalService = phase2_services["hist_service"]
    project_service = phase2_services["project_service"]
    project = phase2_services["project"]
    periods = project_service.list_periods(project.id)
    period_id = periods[0].id

    line = hist_service.save_line(
        project_id=project.id,
        period_id=period_id,
        statement_type="PL",
        line_code="HIST_REV_OPERATIONS",
        line_label="Revenue from Operations (Audited FY25)",
        amount_rupees=Decimal("7500000.00"),
    )
    assert line.line_code == "HIST_REV_OPERATIONS"
    assert line.amount_rupees == Decimal("7500000.00")

    lines = hist_service.list_lines(project.id)
    assert len(lines) == 1
