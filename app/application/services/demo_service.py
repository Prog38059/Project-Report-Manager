"""Demonstration project generator for Project Report Manager."""

from dataclasses import dataclass
from datetime import date
from decimal import Decimal
import logging
from typing import Optional
import uuid

from app.application.dtos.client_dto import CreateClientDTO
from app.application.dtos.entity_dto import CreateEntityDTO, EntityMemberDTO
from app.application.dtos.project_dto import CreateProjectDTO
from app.application.services.appraisal_service import AppraisalService
from app.application.services.client_service import ClientService
from app.application.services.entity_service import EntityService
from app.application.services.expense_service import ExpenseService
from app.application.services.financial_engine_service import FinancialEngineService
from app.application.services.funding_service import FundingService
from app.application.services.project_cost_service import ProjectCostService
from app.application.services.project_service import ProjectService
from app.application.services.revenue_service import RevenueService
from app.common.money import format_inr, rupees_to_paise
from app.common.types import ConstitutionCode, MemberRoleCode, ProjectNatureCode
from app.infrastructure.database.connection import DatabaseManager
from app.infrastructure.security.encryption import EncryptionService

logger = logging.getLogger(__name__)


@dataclass
class DemoProjectSummaryDTO:
    client_id: uuid.UUID
    entity_id: uuid.UUID
    project_id: uuid.UUID
    scenario_id: uuid.UUID
    calculation_run_id: uuid.UUID
    client_name: str
    entity_name: str
    project_name: str
    total_cost_rupees: Decimal
    term_debt_rupees: Decimal
    equity_rupees: Decimal
    average_dscr: Optional[Decimal]
    project_irr_pct: Optional[Decimal]
    run_status: str


class DemoProjectService:
    """Creates a comprehensive, fully realistic industrial demo project with full projection and appraisal runs."""

    def __init__(self, db_manager: DatabaseManager, encryption_service: Optional[EncryptionService] = None) -> None:
        self.db_manager = db_manager
        if encryption_service is None:
            encryption_service = EncryptionService()
        self.encryption_service = encryption_service

        self.client_service = ClientService(db_manager)
        self.entity_service = EntityService(db_manager, encryption_service)
        self.project_service = ProjectService(db_manager)
        self.cost_service = ProjectCostService(db_manager)
        self.funding_service = FundingService(db_manager)
        self.revenue_service = RevenueService(db_manager)
        self.expense_service = ExpenseService(db_manager)
        self.fin_engine = FinancialEngineService(db_manager)
        self.appraisal_service = AppraisalService(db_manager)

    def create_or_get_demo_project(self) -> DemoProjectSummaryDTO:
        """Creates the benchmark 'Aerospace Dynamics Technologies' showcase project."""
        logger.info("Initializing institutional demo project...")

        # 1. Create Client
        client_code = f"DEMO-{uuid.uuid4().hex[:6].upper()}"
        client = self.client_service.create_client(
            CreateClientDTO(
                client_code=client_code,
                display_name="Aerospace Dynamics Group",
                client_category="ENTERPRISE",
                email="rajesh.sharma@aerodynamics.in",
                phone="+91 98200 12345",
                notes="Advanced Defense & Aerospace Manufacturing Group",
            )
        )

        # 2. Create Private Limited Entity
        entity = self.entity_service.create_entity(
            CreateEntityDTO(
                client_id=client.id,
                constitution_code=ConstitutionCode.PRIVATE_LIMITED,
                legal_name="Aerospace Dynamics Technologies Private Limited",
                trade_name="Aerospace Dynamics",
                business_description="High-precision aerospace component machining and turbine assembly",
                date_of_formation=date(2026, 1, 15),
            )
        )

        # Add Directors / Shareholders
        self.entity_service.add_member(
            EntityMemberDTO(
                entity_id=entity.id,
                full_name="Rajesh Sharma",
                role_code=MemberRoleCode.DIRECTOR,
                pan_plaintext="ABFPS1234A",
                profit_share_pct="60.00",
                shareholding_pct="60.00",
                capital_commitment_paise=2100000000,  # 2.10 Cr
            )
        )
        self.entity_service.add_member(
            EntityMemberDTO(
                entity_id=entity.id,
                full_name="Vikram Mehta",
                role_code=MemberRoleCode.DIRECTOR,
                pan_plaintext="BKXPM5678K",
                profit_share_pct="40.00",
                shareholding_pct="40.00",
                capital_commitment_paise=1400000000,  # 1.40 Cr
            )
        )

        # 3. Create 7-Year Manufacturing Project
        project_code = f"PRJ-AERO-{uuid.uuid4().hex[:4].upper()}"
        project = self.project_service.create_project(
            CreateProjectDTO(
                entity_id=entity.id,
                project_code=project_code,
                project_name="Aerospace Machining & Turbine Assembly Unit",
                project_nature_code=ProjectNatureCode.NEW,
                project_description="Greenfield manufacturing facility for high-precision gas turbine blades and aero-structural subassemblies.",
                projection_start_financial_year=2026,
                projection_year_count=7,
            )
        )
        scenarios = self.project_service.list_scenarios(project.id)
        scenario = scenarios[0]

        # 4. Populate Itemized Capital Expenditure (Total ₹10.00 Crores)
        cost_heads = self.cost_service.list_cost_heads()
        head_map = {h.head_code: h.id for h in cost_heads}

        # Land & Site Development: ₹1.00 Cr (0% GST, 100% capitalized)
        if "LAND" in head_map:
            self.cost_service.save_item(
                scenario_id=scenario.id,
                cost_head_id=head_map["LAND"],
                description="MIDC Industrial Land (2.5 Acres) & Perimeter Development",
                basic_rupees=Decimal("10000000.00"),
                gst_rate_pct=Decimal("0.0"),
                itc_eligibility_pct=Decimal("0.0"),
            )

        # Factory Building & Civil Works: ₹2.50 Cr (18% GST, non-creditable capitalized into gross block)
        if "BUILDING" in head_map:
            self.cost_service.save_item(
                scenario_id=scenario.id,
                cost_head_id=head_map["BUILDING"],
                description="Pre-Engineered Heavy Industrial Shed & Foundation Plinths",
                basic_rupees=Decimal("25000000.00"),
                gst_rate_pct=Decimal("18.0"),
                itc_eligibility_pct=Decimal("0.0"),
            )

        # Plant & Machinery: ₹5.00 Cr (18% GST, 100% ITC creditable)
        pm_head = next((h.id for h in cost_heads if "PLANT" in h.head_code or "EQUIPMENT" in h.head_code), cost_heads[0].id)
        self.cost_service.save_item(
            scenario_id=scenario.id,
            cost_head_id=pm_head,
            description="5-Axis CNC Milling Centers, Coordinate Measuring Machines & Heat Treatment",
            basic_rupees=Decimal("50000000.00"),
            gst_rate_pct=Decimal("18.0"),
            itc_eligibility_pct=Decimal("100.0"),
        )

        # Electrical Substation & Utilities: ₹0.80 Cr (18% GST, 100% ITC creditable)
        util_head = next((h.id for h in cost_heads if "ELECTRICAL" in h.head_code or "UTILITY" in h.head_code), pm_head)
        self.cost_service.save_item(
            scenario_id=scenario.id,
            cost_head_id=util_head,
            description="11 kV Substation Transformer, DG Backup Sets & Industrial Chilling Plant",
            basic_rupees=Decimal("8000000.00"),
            gst_rate_pct=Decimal("18.0"),
            itc_eligibility_pct=Decimal("100.0"),
        )

        # Preliminary & Pre-operative Expenses: ₹0.40 Cr
        pre_head = next((h.id for h in cost_heads if "PRELIM" in h.head_code or "PREOP" in h.head_code), pm_head)
        self.cost_service.save_item(
            scenario_id=scenario.id,
            cost_head_id=pre_head,
            description="Architectural Design, Environmental Approvals & Trial Run Setup",
            basic_rupees=Decimal("4000000.00"),
            gst_rate_pct=Decimal("18.0"),
            itc_eligibility_pct=Decimal("100.0"),
        )

        # Contingencies: ₹0.30 Cr
        cont_head = next((h.id for h in cost_heads if "CONTINGENCY" in h.head_code or "MISC" in h.head_code), pm_head)
        self.cost_service.save_item(
            scenario_id=scenario.id,
            cost_head_id=cont_head,
            description="Unforeseen Price Escalation & Contingency Reserve (3%)",
            basic_rupees=Decimal("3000000.00"),
            gst_rate_pct=Decimal("0.0"),
            itc_eligibility_pct=Decimal("0.0"),
        )

        # 5. Populate Means of Finance (Total ₹10.00 Crores, Perfectly Balanced)
        funding_heads = self.funding_service.list_funding_heads()
        term_head = next((h for h in funding_heads if "TERM_LOAN" in h.funding_code), funding_heads[0])
        equity_head = next((h for h in funding_heads if "EQUITY" in h.funding_code), funding_heads[1])

        # State Bank of India Term Loan: ₹6.50 Crores
        self.funding_service.save_source(
            scenario_id=scenario.id,
            funding_head_id=term_head.id,
            source_name="State Bank of India Term Debt Facility",
            amount_rupees=Decimal("65000000.00"),
            terms_note="10.75% floating interest, 84 months repayment including 12 months moratorium",
        )

        # Promoters' Equity Capital: ₹3.50 Crores
        self.funding_service.save_source(
            scenario_id=scenario.id,
            funding_head_id=equity_head.id,
            source_name="Promoters Equity Share Capital Contribution",
            amount_rupees=Decimal("35000000.00"),
            terms_note="Fully paid up equity shares of ₹10 face value",
        )

        # 6. Execute 7-Year Financial Projection Pipeline
        logger.info("Executing 7-year financial projection pipeline for demo project...")
        run_dto = self.fin_engine.execute_projection(scenario_id=scenario.id)

        # 7. Evaluate Lender Appraisal & Cross-Statement Audit
        logger.info("Evaluating lender appraisal metrics and validation integrity...")
        appraisal_report = self.appraisal_service.evaluate_appraisal(
            scenario_id=scenario.id,
            calculation_run_id=run_dto.id,
        )

        avg_dscr = appraisal_report.lifetime_returns.average_gross_dscr
        irr_pct = appraisal_report.lifetime_returns.irr_pct

        logger.info(f"Demo project ready: Run status={run_dto.run_status}, Average DSCR={avg_dscr}, IRR={irr_pct}%")

        return DemoProjectSummaryDTO(
            client_id=client.id,
            entity_id=entity.id,
            project_id=project.id,
            scenario_id=scenario.id,
            calculation_run_id=run_dto.id,
            client_name=client.display_name,
            entity_name=entity.legal_name,
            project_name=project.project_name,
            total_cost_rupees=Decimal("100000000.00"),  # ₹10.00 Crores
            term_debt_rupees=Decimal("65000000.00"),   # ₹6.50 Crores
            equity_rupees=Decimal("35000000.00"),      # ₹3.50 Crores
            average_dscr=avg_dscr,
            project_irr_pct=irr_pct,
            run_status=run_dto.run_status,
        )
