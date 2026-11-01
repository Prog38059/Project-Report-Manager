"""Integration test for FinancialEngineService and complete calculation lifecycle."""

from decimal import Decimal
from pathlib import Path
import uuid
import pytest

from alembic.config import Config
from alembic import command

from app.application.dtos.client_dto import CreateClientDTO
from app.application.dtos.entity_dto import CreateEntityDTO
from app.application.dtos.project_dto import CreateProjectDTO
from app.application.services.client_service import ClientService
from app.application.services.entity_service import EntityService
from app.application.services.financial_engine_service import FinancialEngineService
from app.application.services.funding_service import FundingService
from app.application.services.project_cost_service import ProjectCostService
from app.application.services.project_service import ProjectService
from app.infrastructure.security.encryption import EncryptionService
from app.common.types import ConstitutionCode, ProjectNatureCode
from app.config import AppConfig
from app.infrastructure.database.connection import DatabaseManager


@pytest.fixture
def service_env(test_config: AppConfig, encryption_service: EncryptionService):
    alembic_ini_path = Path(__file__).resolve().parent.parent.parent / "alembic.ini"
    alembic_cfg = Config(str(alembic_ini_path))
    alembic_cfg.set_main_option("sqlalchemy.url", test_config.sqlite_url)
    command.upgrade(alembic_cfg, "head")

    db_manager = DatabaseManager.from_config(test_config)
    try:
        yield db_manager, encryption_service
    finally:
        db_manager.engine.dispose()


def test_full_financial_engine_projection_lifecycle(service_env):
    db_manager, encryption_service = service_env
    client_service = ClientService(db_manager)
    entity_service = EntityService(db_manager, encryption_service)
    project_service = ProjectService(db_manager)
    cost_service = ProjectCostService(db_manager)
    funding_service = FundingService(db_manager)
    fin_engine = FinancialEngineService(db_manager)

    # 1. Create Client, Entity (Private Limited), and Project
    client = client_service.create_client(
        CreateClientDTO(client_code="CLI-FIN-01", display_name="Precision Tech Corp")
    )
    entity = entity_service.create_entity(
        CreateEntityDTO(
            client_id=client.id,
            constitution_code=ConstitutionCode.PRIVATE_LIMITED,
            legal_name="Precision Dynamics Private Limited",
        )
    )
    project = project_service.create_project(
        CreateProjectDTO(
            entity_id=entity.id,
            project_code="PRJ-FIN-01",
            project_name="Advanced CNC Machining Unit",
            project_nature_code=ProjectNatureCode.NEW,
            projection_start_financial_year=2026,
            projection_year_count=7,
        )
    )

    scenarios = project_service.list_scenarios(project.id)
    scenario = scenarios[0]

    # 2. Add Project Costs (Capex)
    cost_heads = cost_service.list_cost_heads()
    pm_head = next(h for h in cost_heads if "PLANT" in h.head_code or "EQUIPMENT" in h.head_code)
    cost_service.save_item(
        scenario_id=scenario.id,
        cost_head_id=pm_head.id,
        description="CNC Milling and Turning Center",
        basic_rupees=Decimal("7500000.00"),  # 75 Lakhs
        gst_rate_pct=Decimal("18.0"),
        itc_eligibility_pct=Decimal("100.0"),
    )

    # 3. Add Funding (Term Loan 50L + Equity 25L)
    funding_heads = funding_service.list_funding_heads()
    term_debt_head = next(h for h in funding_heads if "TERM_LOAN" in h.funding_code)
    equity_head = next(h for h in funding_heads if "EQUITY" in h.funding_code)

    funding_service.save_source(
        scenario_id=scenario.id,
        funding_head_id=term_debt_head.id,
        source_name="State Bank of India Term Loan",
        amount_rupees=Decimal("5000000.00"),  # 50 Lakhs
        terms_note="11.5% interest, 84 months tenure",
    )
    funding_service.save_source(
        scenario_id=scenario.id,
        funding_head_id=equity_head.id,
        source_name="Promoter Paid-Up Equity",
        amount_rupees=Decimal("2500000.00"),  # 25 Lakhs
    )

    # 4. Execute Financial Projections via FinancialEngineService
    run_dto = fin_engine.execute_projection(
        scenario_id=scenario.id,
        prepared_by_label="Lead Financial Analyst",
        engine_version="1.0.0",
    )

    # 5. Verify Run and Snapshot
    assert run_dto.run_status == "SUCCESS"
    assert run_dto.run_number == 1
    assert run_dto.engine_version == "1.0.0"
    assert len(run_dto.input_hash) == 64
    assert run_dto.validation_error_count == 0

    # 6. Verify Tables Structure (Horizontal A:J Presentation)
    assert run_dto.pl_table is not None
    assert len(run_dto.pl_table.period_headers) == 7
    assert "Year 1" in run_dto.pl_table.period_headers[0]

    assert run_dto.bs_table is not None
    assert len(run_dto.bs_table.period_headers) == 7

    assert run_dto.cf_table is not None
    assert len(run_dto.cf_table.period_headers) == 7

    # 7. Verify Zero-Plug Balance Sheet Invariant in the Table
    bs_rows = {row.particulars: row for row in run_dto.bs_table.rows}
    total_assets_row = bs_rows["TOTAL ASSETS"]
    total_liab_row = bs_rows["TOTAL LIABILITIES & EQUITY"]

    for seq in range(1, 8):
        assets_val = total_assets_row.period_amounts[seq]
        liab_val = total_liab_row.period_amounts[seq]
        diff = assets_val - liab_val
        assert diff == Decimal("0.00"), (
            f"Period {seq} Balance Sheet out of balance! Assets={assets_val}, Liab={liab_val}, Diff={diff}"
        )

    # 8. Verify Loan Amortization Schedule
    assert len(run_dto.loan_schedule) == 84  # 7 years * 12 months
    assert run_dto.loan_schedule[0].opening_balance_rupees == Decimal("5000000.00")
    assert run_dto.loan_schedule[-1].closing_balance_rupees == Decimal("0.00")

    # 9. Verify Asset Schedule
    assert len(run_dto.asset_schedule) == 7
    assert run_dto.asset_schedule[0].additions_rupees == Decimal("7500000.00")
    assert run_dto.asset_schedule[0].depreciation_rupees > 0

    # 10. Execute Run 2 and verify run_number increments
    run_dto_2 = fin_engine.execute_projection(
        scenario_id=scenario.id,
        prepared_by_label="Lead Financial Analyst",
    )
    assert run_dto_2.run_number == 2
