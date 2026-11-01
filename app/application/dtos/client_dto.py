"""Client DTOs."""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional
import uuid


@dataclass
class CreateClientDTO:
    client_code: str
    display_name: str
    client_category: str = "PERSON"
    phone: Optional[str] = None
    email: Optional[str] = None
    address_text: Optional[str] = None
    notes: Optional[str] = None


@dataclass
class UpdateClientDTO:
    display_name: Optional[str] = None
    client_category: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    address_text: Optional[str] = None
    notes: Optional[str] = None


@dataclass
class ClientResponseDTO:
    id: uuid.UUID
    client_code: str
    display_name: str
    client_category: str
    phone: Optional[str]
    email: Optional[str]
    address_text: Optional[str]
    notes: Optional[str]
    is_active: bool
    created_at: datetime
    updated_at: datetime
