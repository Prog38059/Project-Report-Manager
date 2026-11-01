"""Legal entity domain models and constitution-specific extension models."""

from dataclasses import dataclass, field
from datetime import date, datetime, timezone
from typing import Optional
import uuid

from app.common.types import ConstitutionCode


@dataclass
class LegalEntity:
    """The legal applicant / business entity used by projects."""
    id: uuid.UUID = field(default_factory=uuid.uuid4)
    client_id: uuid.UUID = field(default_factory=uuid.uuid4)
    constitution_code: ConstitutionCode = ConstitutionCode.INDIVIDUAL
    legal_name: str = ""
    trade_name: Optional[str] = None
    business_description: Optional[str] = None
    accounting_framework_code: Optional[str] = None
    tax_profile_code: Optional[str] = None
    date_of_formation: Optional[date] = None
    active_flag: bool = True
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    created_by_label: Optional[str] = None
    updated_by_label: Optional[str] = None

    def validate(self) -> None:
        """Domain validations for LegalEntity."""
        from app.common.exceptions import ValidationError

        if not self.legal_name or not self.legal_name.strip():
            raise ValidationError("Legal name is required.")
        if not self.constitution_code:
            raise ValidationError("Constitution code is required.")


@dataclass
class HUFDetails:
    """HUF-specific extension details."""
    entity_id: uuid.UUID
    karta_member_id: uuid.UUID
    formation_note: Optional[str] = None


@dataclass
class ProprietorshipDetails:
    """Proprietorship-specific extension details."""
    entity_id: uuid.UUID
    proprietor_member_id: uuid.UUID
    business_start_date: Optional[date] = None


@dataclass
class PartnershipDetails:
    """Partnership-specific extension details."""
    entity_id: uuid.UUID
    deed_date: Optional[date] = None
    registration_status: Optional[str] = None
    deed_attachment_id: Optional[uuid.UUID] = None


@dataclass
class LLPDetails:
    """LLP-specific extension details."""
    entity_id: uuid.UUID
    incorporation_date: Optional[date] = None
    llp_agreement_date: Optional[date] = None
    agreement_attachment_id: Optional[uuid.UUID] = None


@dataclass
class CompanyDetails:
    """Company-specific extension details."""
    entity_id: uuid.UUID
    incorporation_date: Optional[date] = None
    company_class: Optional[str] = None
    authorised_capital_paise: Optional[int] = None
    paid_up_capital_paise: Optional[int] = None
    registered_office_address: Optional[str] = None
