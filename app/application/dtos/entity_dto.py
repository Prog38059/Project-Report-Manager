"""Legal Entity and Member DTOs."""

from dataclasses import dataclass
from datetime import date, datetime
from typing import Optional
import uuid

from app.common.types import ConstitutionCode, MemberRoleCode, IdentifierTypeCode


@dataclass
class CreateEntityDTO:
    client_id: uuid.UUID
    constitution_code: ConstitutionCode
    legal_name: str
    trade_name: Optional[str] = None
    business_description: Optional[str] = None
    accounting_framework_code: Optional[str] = None
    tax_profile_code: Optional[str] = None
    date_of_formation: Optional[date] = None


@dataclass
class UpdateEntityDTO:
    legal_name: Optional[str] = None
    trade_name: Optional[str] = None
    business_description: Optional[str] = None
    accounting_framework_code: Optional[str] = None
    tax_profile_code: Optional[str] = None
    date_of_formation: Optional[date] = None


@dataclass
class EntityResponseDTO:
    id: uuid.UUID
    client_id: uuid.UUID
    constitution_code: ConstitutionCode
    legal_name: str
    trade_name: Optional[str]
    business_description: Optional[str]
    accounting_framework_code: Optional[str]
    tax_profile_code: Optional[str]
    date_of_formation: Optional[date]
    active_flag: bool
    created_at: datetime
    updated_at: datetime


@dataclass
class EntityMemberDTO:
    entity_id: uuid.UUID
    full_name: str
    role_code: MemberRoleCode
    pan_plaintext: Optional[str] = None
    address_text: Optional[str] = None
    contact_phone: Optional[str] = None
    contact_email: Optional[str] = None
    profit_share_pct: Optional[str] = None
    shareholding_pct: Optional[str] = None
    capital_commitment_paise: Optional[int] = None
    date_from: Optional[date] = None
    date_to: Optional[date] = None
    notes: Optional[str] = None
