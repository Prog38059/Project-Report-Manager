"""Entity member and entity identifier domain models."""

from dataclasses import dataclass, field
from datetime import date, datetime, timezone
from typing import Optional
import uuid

from app.common.types import MemberRoleCode, IdentifierTypeCode


@dataclass
class EntityMember:
    """Individual person associated with an entity (Karta, Partner, Director, Proprietor, etc.)."""
    id: uuid.UUID = field(default_factory=uuid.uuid4)
    entity_id: uuid.UUID = field(default_factory=uuid.uuid4)
    full_name: str = ""
    role_code: MemberRoleCode = MemberRoleCode.OTHER
    pan_encrypted: Optional[str] = None
    address_text: Optional[str] = None
    contact_phone: Optional[str] = None
    contact_email: Optional[str] = None
    profit_share_pct: Optional[str] = None
    shareholding_pct: Optional[str] = None
    capital_commitment_paise: Optional[int] = None
    date_from: Optional[date] = None
    date_to: Optional[date] = None
    notes: Optional[str] = None
    is_active: bool = True
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    created_by_label: Optional[str] = None
    updated_by_label: Optional[str] = None

    def validate(self) -> None:
        """Domain validations for EntityMember."""
        from app.common.exceptions import ValidationError

        if not self.full_name or not self.full_name.strip():
            raise ValidationError("Member full name is required.")
        if not self.role_code:
            raise ValidationError("Member role code is required.")


@dataclass
class EntityIdentifier:
    """Statutory or registration identifier for an entity (PAN, GSTIN, CIN, etc.)."""
    id: uuid.UUID = field(default_factory=uuid.uuid4)
    entity_id: uuid.UUID = field(default_factory=uuid.uuid4)
    identifier_type: IdentifierTypeCode = IdentifierTypeCode.OTHER
    identifier_value_encrypted: str = ""
    identifier_value_hash: Optional[str] = None
    valid_from: Optional[date] = None
    valid_to: Optional[date] = None
    verification_status: str = "UNVERIFIED"
    source_attachment_id: Optional[uuid.UUID] = None
    notes: Optional[str] = None
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
