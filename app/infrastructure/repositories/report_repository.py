"""Repository for Report Templates, Template Sections, and Generated Reports."""

from datetime import datetime, timezone
from typing import List, Optional
import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.infrastructure.database.models.report_model import (
    GeneratedReportModel,
    ReportTemplateModel,
    ReportTemplateSectionModel,
)


class ReportRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def list_templates(self, active_only: bool = True) -> List[ReportTemplateModel]:
        stmt = select(ReportTemplateModel)
        if active_only:
            stmt = stmt.where(ReportTemplateModel.active_flag.is_(True))
        stmt = stmt.order_by(ReportTemplateModel.template_name)
        return list(self.session.execute(stmt).scalars().all())

    def get_template_by_id(self, template_id: uuid.UUID) -> Optional[ReportTemplateModel]:
        return self.session.get(ReportTemplateModel, template_id)

    def get_template_by_code(self, template_code: str) -> Optional[ReportTemplateModel]:
        stmt = select(ReportTemplateModel).where(ReportTemplateModel.template_code == template_code)
        return self.session.execute(stmt).scalars().first()

    def get_sections_for_template(self, template_id: uuid.UUID) -> List[ReportTemplateSectionModel]:
        stmt = (
            select(ReportTemplateSectionModel)
            .where(ReportTemplateSectionModel.report_template_id == template_id)
            .order_by(ReportTemplateSectionModel.sort_order)
        )
        return list(self.session.execute(stmt).scalars().all())

    def create_generated_report(
        self,
        project_id: uuid.UUID,
        scenario_id: uuid.UUID,
        calculation_run_id: uuid.UUID,
        report_template_id: uuid.UUID,
        output_type: str,
        stored_relative_path: str,
        file_hash: str,
        report_version: str = "1.0",
        notes: Optional[str] = None,
        generation_status: str = "SUCCESS",
    ) -> GeneratedReportModel:
        record = GeneratedReportModel(
            id=uuid.uuid4(),
            project_id=project_id,
            scenario_id=scenario_id,
            calculation_run_id=calculation_run_id,
            report_template_id=report_template_id,
            report_version=report_version,
            output_type=output_type,
            stored_relative_path=stored_relative_path,
            file_hash=file_hash,
            generated_at=datetime.now(timezone.utc),
            generation_status=generation_status,
            notes=notes,
        )
        self.session.add(record)
        self.session.flush()
        return record

    def list_generated_reports(
        self,
        project_id: Optional[uuid.UUID] = None,
        calculation_run_id: Optional[uuid.UUID] = None,
    ) -> List[GeneratedReportModel]:
        stmt = select(GeneratedReportModel).order_by(GeneratedReportModel.generated_at.desc())
        if project_id:
            stmt = stmt.where(GeneratedReportModel.project_id == project_id)
        if calculation_run_id:
            stmt = stmt.where(GeneratedReportModel.calculation_run_id == calculation_run_id)
        return list(self.session.execute(stmt).scalars().all())

    def get_generated_report_by_id(self, report_id: uuid.UUID) -> Optional[GeneratedReportModel]:
        return self.session.get(GeneratedReportModel, report_id)
