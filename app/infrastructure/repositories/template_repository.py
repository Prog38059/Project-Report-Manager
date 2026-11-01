"""Repository for Industry Templates and Template Fields."""

from typing import List, Optional
import uuid
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.domain.entities.industry_template import IndustryTemplate, IndustryTemplateField
from app.infrastructure.database.models.template_model import (
    IndustryTemplateFieldModel,
    IndustryTemplateModel,
)


class TemplateRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    @staticmethod
    def _field_to_entity(model: IndustryTemplateFieldModel) -> IndustryTemplateField:
        return IndustryTemplateField(
            id=model.id,
            industry_template_id=model.industry_template_id,
            module_code=model.module_code,
            field_code=model.field_code,
            field_label=model.field_label,
            input_type=model.input_type,
            unit_code=model.unit_code,
            required_flag=model.required_flag,
            default_value_text=model.default_value_text,
            help_text=model.help_text,
            sort_order=model.sort_order,
        )

    def _to_entity(self, model: IndustryTemplateModel) -> IndustryTemplate:
        fields = [self._field_to_entity(f) for f in model.fields]
        return IndustryTemplate(
            id=model.id,
            industry_code=model.industry_code,
            industry_name=model.industry_name,
            description=model.description,
            template_version=model.template_version,
            active_flag=model.active_flag,
            fields=fields,
        )

    def list_templates(self, active_only: bool = True) -> List[IndustryTemplate]:
        stmt = select(IndustryTemplateModel)
        if active_only:
            stmt = stmt.where(IndustryTemplateModel.active_flag.is_(True))
        stmt = stmt.order_by(IndustryTemplateModel.industry_name)
        models = self.session.execute(stmt).scalars().all()
        return [self._to_entity(m) for m in models]

    def get_by_code(self, industry_code: str) -> Optional[IndustryTemplate]:
        stmt = select(IndustryTemplateModel).where(IndustryTemplateModel.industry_code == industry_code)
        model = self.session.execute(stmt).scalar_one_or_none()
        return self._to_entity(model) if model else None
