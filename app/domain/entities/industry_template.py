"""Industry Template domain entities."""

from dataclasses import dataclass
from typing import Optional
from uuid import UUID

from app.common.exceptions import ValidationError


@dataclass
class IndustryTemplateField:
    """Field specification within an industry template."""
    id: UUID
    industry_template_id: UUID
    module_code: str
    field_code: str
    field_label: str
    input_type: str
    unit_code: Optional[str] = None
    required_flag: bool = False
    default_value_text: Optional[str] = None
    help_text: Optional[str] = None
    sort_order: int = 0

    def __post_init__(self):
        if not self.field_code or not self.field_code.strip():
            raise ValidationError("Field code cannot be empty.")
        if not self.field_label or not self.field_label.strip():
            raise ValidationError("Field label cannot be empty.")


@dataclass
class IndustryTemplate:
    """Starter industry template containing recommended assumptions and drivers."""
    id: UUID
    industry_code: str
    industry_name: str
    description: Optional[str] = None
    template_version: str = "1.0"
    active_flag: bool = True
    fields: list[IndustryTemplateField] = None

    def __post_init__(self):
        if not self.industry_code or not self.industry_code.strip():
            raise ValidationError("Industry code cannot be empty.")
        if not self.industry_name or not self.industry_name.strip():
            raise ValidationError("Industry name cannot be empty.")
        if self.fields is None:
            self.fields = []
