"""Data transfer objects for Industry Templates."""

from dataclasses import dataclass
from typing import List, Optional
from uuid import UUID


@dataclass
class TemplateFieldDTO:
    id: UUID
    module_code: str
    field_code: str
    field_label: str
    input_type: str
    unit_code: Optional[str]
    required_flag: bool
    default_value_text: Optional[str]
    help_text: Optional[str]


@dataclass
class IndustryTemplateDTO:
    id: UUID
    industry_code: str
    industry_name: str
    description: Optional[str]
    fields: List[TemplateFieldDTO]
