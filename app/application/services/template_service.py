"""Application service for Industry Templates."""

from typing import List, Optional
import uuid

from app.application.dtos.template_dto import IndustryTemplateDTO, TemplateFieldDTO
from app.common.types import GstTreatmentCode, RevenueMethodCode
from app.domain.entities.revenue import RevenueStream
from app.infrastructure.database.connection import DatabaseManager
from app.infrastructure.repositories.revenue_repository import RevenueRepository
from app.infrastructure.repositories.template_repository import TemplateRepository


class TemplateService:
    def __init__(self, db_manager: DatabaseManager) -> None:
        self.db_manager = db_manager

    def list_templates(self) -> List[IndustryTemplateDTO]:
        with self.db_manager.session_scope() as session:
            repo = TemplateRepository(session)
            templates = repo.list_templates(active_only=True)
            return [
                IndustryTemplateDTO(
                    id=t.id,
                    industry_code=t.industry_code,
                    industry_name=t.industry_name,
                    description=t.description,
                    fields=[
                        TemplateFieldDTO(
                            id=f.id,
                            module_code=f.module_code,
                            field_code=f.field_code,
                            field_label=f.field_label,
                            input_type=f.input_type,
                            unit_code=f.unit_code,
                            required_flag=f.required_flag,
                            default_value_text=f.default_value_text,
                            help_text=f.help_text,
                        )
                        for f in t.fields
                    ],
                )
                for t in templates
            ]

    def get_template(self, industry_code: str) -> Optional[IndustryTemplateDTO]:
        with self.db_manager.session_scope() as session:
            repo = TemplateRepository(session)
            t = repo.get_by_code(industry_code)
            if not t:
                return None
            return IndustryTemplateDTO(
                id=t.id,
                industry_code=t.industry_code,
                industry_name=t.industry_name,
                description=t.description,
                fields=[
                    TemplateFieldDTO(
                        id=f.id,
                        module_code=f.module_code,
                        field_code=f.field_code,
                        field_label=f.field_label,
                        input_type=f.input_type,
                        unit_code=f.unit_code,
                        required_flag=f.required_flag,
                        default_value_text=f.default_value_text,
                        help_text=f.help_text,
                    )
                    for f in t.fields
                ],
            )

    def apply_starter_template(self, scenario_id: uuid.UUID, industry_code: str) -> None:
        """Applies sensible starter revenue streams for the selected industry."""
        with self.db_manager.session_scope() as session:
            rev_repo = RevenueRepository(session)

            # Map starter stream by industry
            starter_configs = {
                "IND_MANUFACTURING": ("REV_MAIN_PROD", "Primary Manufactured Product", RevenueMethodCode.CAPACITY_UTILISATION_PRICE, "MT"),
                "IND_TRADING": ("REV_TRADING_GOODS", "Traded Goods Sales", RevenueMethodCode.TURNOVER_GROWTH, "INR"),
                "IND_HOSPITAL": ("REV_IPD_BEDS", "In-Patient Bed Charges & Procedures", RevenueMethodCode.OCCUPANCY_RATE, "BEDS"),
                "IND_HOTEL": ("REV_ROOM_STAY", "Room Stay & Lodging", RevenueMethodCode.OCCUPANCY_RATE, "ROOMS"),
                "IND_RESTAURANT": ("REV_DINE_IN", "Dine-In Restaurant Food & Beverages", RevenueMethodCode.CUSTOMERS_AVERAGE_BILL, "COVERS"),
                "IND_EV_CHARGING": ("REV_EV_CHARGING", "EV Charging Station Energy Sales", RevenueMethodCode.CAPACITY_UTILISATION_PRICE, "KWH"),
                "IND_TRANSPORT": ("REV_FREIGHT", "Logistics & Freight Services", RevenueMethodCode.UNITS_PRICE, "TRIPS"),
                "IND_EDUCATION": ("REV_TUITION_FEES", "Annual Tuition Fees", RevenueMethodCode.UNITS_PRICE, "STUDENTS"),
                "IND_RENTAL": ("REV_LEASE_RENT", "Commercial Space Lease Rental", RevenueMethodCode.RENTAL_UNITS_RATE, "SQFT"),
                "IND_SERVICES": ("REV_CONSULTING", "Professional Consulting Services", RevenueMethodCode.HEADCOUNT_BILLING, "HOURS"),
            }

            cfg = starter_configs.get(industry_code)
            if cfg:
                code, name, method, unit = cfg
                stream = RevenueStream(
                    id=uuid.uuid4(),
                    scenario_id=scenario_id,
                    stream_code=code,
                    stream_name=name,
                    method_code=method,
                    gst_treatment_code=GstTreatmentCode.TAXABLE_EXCLUSIVE,
                    gst_rate_pct_text="18.0",
                    unit_code=unit,
                )
                rev_repo.save_stream(stream)
