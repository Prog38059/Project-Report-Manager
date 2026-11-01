"""Integration test for AppraisalService, Ratios, Break-Even, Sensitivity, and Validation persistence."""

from decimal import Decimal
from pathlib import Path
import uuid
import pytest

from alembic.config import Config
from alembic import command

from app.application.dtos.client_dto import CreateClientDTO
from app.application.dtos.entity_dto import CreateEntityDTO
from app.application.dtos.project_dto import CreateProjectDTO
from app.application.services.appraisal_service import AppraisalService
from app.application.services.client_service import ClientService
from app.application.services.entity_service import EntityService
from app.application.services.financial_engine_service import FinancialEngineService
from app.application.services.funding_service import FundingService
from app.application.services.project_cost_service import ProjectCostService
from app.application.services.project_service import ProjectService
from app.common.types import ConstitutionCode, ProjectNatureCode
from app.config import AppConfig
from app.infrastructure.database.connection import DatabaseManager
from app.infrastructure.repositories.calculation_repository import CalculationRepository
from app.infrastructure.security.encryption import EncryptionService


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


def test_full_appraisal_and_validation_service_lifecycle(service_env):
    db_manager, encryption_service = service_env
    client_service = ClientService(db_manager)
    entity_service = EntityService(db_manager, encryption_service)
    project_service = ProjectService(db_manager)
    cost_service = ProjectCostService(db_manager)
    funding_service = FundingService(db_manager)
    fin_engine = FinancialEngineService(db_manager)
    appraisal_service = AppraisalService(db_manager)

    # 1. Create Client, Entity, Project, and Scenario
    client = client_service.create_client(
        CreateClientDTO(client_code="CLI-APP-01", display_name="Precision Aero Systems")
    )
    entity = entity_service.create_entity(
        CreateEntityDTO(
            client_id=client.id,
            constitution_code=ConstitutionCode.PRIVATE_LIMITED,
            legal_name="Precision Aero Systems Private Limited",
        )
    )
    project = project_service.create_project(
        CreateProjectDTO(
            entity_id=entity.id,
            project_code="PRJ-APP-01",
            project_name="Aerospace Component Fabrication Facility",
            project_nature_code=ProjectNatureCode.NEW,
            projection_start_financial_year=2026,
            projection_year_count=7,
        )
    )
    scenarios = project_service.list_scenarios(project.id)
    scenario = scenarios[0]

    # 2. Add Project Costs (Capex = 80 Lakhs)
    cost_heads = cost_service.list_cost_heads()
    pm_head = next(h for h in cost_heads if "PLANT" in h.head_code or "EQUIPMENT" in h.head_code)
    cost_service.save_item(
        scenario_id=scenario.id,
        cost_head_id=pm_head.id,
        description="High-Precision Multi-Axis CNC Machine",
        basic_rupees=Decimal("8000000.00"),  # 80 Lakhs
        gst_rate_pct=Decimal("18.0"),
        itc_eligibility_pct=Decimal("100.0"),
    )

    # 3. Add Funding (Term Loan 50L + Equity 30L = 80 Lakhs, Zero Gap)
    funding_heads = funding_service.list_funding_heads()
    term_debt_head = next(h for h in funding_heads if "TERM_LOAN" in h.funding_code)
    equity_head = next(h for h in funding_heads if "EQUITY" in h.funding_code)

    funding_service.save_source(
        scenario_id=scenario.id,
        funding_head_id=term_debt_head.id,
        source_name="Bank of Baroda Term Loan",
        amount_rupees=Decimal("5000000.00"),  # 50 Lakhs
        terms_note="11.5% interest, 84 months tenure",
    )
    funding_service.save_source(
        scenario_id=scenario.id,
        funding_head_id=equity_head.id,
        source_name="Promoter Equity Contribution",
        amount_rupees=Decimal("3000000.00"),  # 30 Lakhs
    )

    # 4. Run Financial Projections first
    run_dto = fin_engine.execute_projection(
        scenario_id=scenario.id,
        prepared_by_label="Appraisal Analyst",
    )
    assert run_dto.run_status == "SUCCESS"

    # 5. Evaluate Appraisal and Validation Engine
    report = appraisal_service.evaluate_appraisal(
        scenario_id=scenario.id,
        discount_rate_pct=Decimal("10.0"),
    )

    # 6. Verify AppraisalReportDTO Structure
    assert report.calculation_run_id == run_dto.id
    assert report.run_number == 1
    assert len(report.period_headers) == 7

    # 7. Verify Lifetime Returns
    returns = report.lifetime_returns
    assert returns.initial_investment_rupees == Decimal("8000000.00")
    assert returns.discount_rate_pct == Decimal("10.0")
    assert returns.npv_rupees > 0
    assert returns.irr_pct is not None
    assert returns.irr_pct > Decimal("10.0")  # Return exceeds 10% discount rate
    assert returns.payback_years > 0
    assert returns.profitability_index is not None
    assert returns.profitability_index > Decimal("1.00")
    assert returns.average_gross_dscr is not None
    assert returns.average_gross_dscr > Decimal("1.00")

    # 8. Verify Ratio Rows (Coverage, Liquidity, Solvency, Margins, BEP)
    ratio_by_code = {r.metric_code: r for r in report.ratio_rows}
    assert "CURRENT_RATIO" in ratio_by_code
    assert "DEBT_EQUITY" in ratio_by_code
    assert "GROSS_DSCR" in ratio_by_code
    assert "NET_CFADS_DSCR" in ratio_by_code
    assert "INTEREST_COVERAGE" in ratio_by_code
    assert "EBITDA_MARGIN" in ratio_by_code
    assert "PAT_MARGIN" in ratio_by_code
    assert "BEP_CAPACITY" in ratio_by_code
    assert "MARGIN_OF_SAFETY" in ratio_by_code

    # Check 7 periods are populated for Current Ratio
    cr_row = ratio_by_code["CURRENT_RATIO"]
    assert len(cr_row.period_values) == 7
    for seq in range(1, 8):
        assert seq in cr_row.period_values

    # 9. Verify Sensitivity Scenarios (+/- 5%, 10%)
    assert len(report.sensitivity_rows) >= 9  # Base Case + 4 price variations + 4 cost variations
    base_case = report.sensitivity_rows[0]
    assert base_case.parameter_name == "Base Case (Current Projection)"
    assert base_case.variation_pct == Decimal("0.0")
    assert base_case.average_dscr != "N/A"
    assert base_case.irr_pct != "N/A"

    # Price increase (+10%) should yield higher PAT than price decrease (-10%)
    price_plus_10 = next(s for s in report.sensitivity_rows if s.parameter_name == "Selling Price / Billing" and s.variation_pct == Decimal("10.0"))
    price_minus_10 = next(s for s in report.sensitivity_rows if s.parameter_name == "Selling Price / Billing" and s.variation_pct == Decimal("-10.0"))
    assert price_plus_10.avg_pat_rupees > price_minus_10.avg_pat_rupees

    # 10. Verify Persistence in Database
    with db_manager.session_scope() as session:
        calc_repo = CalculationRepository(session)

        # Ratio results persisted
        persisted_ratios = calc_repo.get_ratio_results_for_run(run_dto.id)
        assert len(persisted_ratios) > 0
        ratio_codes = {r.ratio_code for r in persisted_ratios}
        assert "CURRENT_RATIO" in ratio_codes
        assert "GROSS_DSCR" in ratio_codes
        assert "NPV" in ratio_codes
        assert "PROJECT_IRR" in ratio_codes

        # Validation results persisted
        persisted_val = calc_repo.get_validation_results_for_run(run_dto.id)
        # In a balanced projection with 0 funding gap, no fatal errors
        error_issues = [v for v in persisted_val if v.severity == "ERROR"]
        assert len(error_issues) == 0

        # Run record validation counts updated
        run_record = calc_repo.get_run_by_id(run_dto.id)
        assert run_record.validation_error_count == 0
