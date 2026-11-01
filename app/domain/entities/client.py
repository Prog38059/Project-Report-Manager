"""Client domain model."""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional
import uuid


@dataclass
class Client:
    """CA-firm client / customer record."""
    id: uuid.UUID = field(default_factory=uuid.uuid4)
    client_code: str = ""
    display_name: str = ""
    client_category: str = "PERSON"
    phone: Optional[str] = None
    email: Optional[str] = None
    address_text: Optional[str] = None
    notes: Optional[str] = None
    is_active: bool = True
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    created_by_label: Optional[str] = None
    updated_by_label: Optional[str] = None

    def validate(self) -> None:
        """Domain validations for Client."""
        from app.common.exceptions import ValidationError

        if not self.client_code or not self.client_code.strip():
            raise ValidationError("Client code is required.")
        if not self.display_name or not self.display_name.strip():
            raise ValidationError("Display name is required.")
