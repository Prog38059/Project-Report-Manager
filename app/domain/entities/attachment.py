"""Attachment domain model."""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional
import uuid


@dataclass
class Attachment:
    """Document attachment metadata record."""
    id: uuid.UUID = field(default_factory=uuid.uuid4)
    project_id: Optional[uuid.UUID] = None
    entity_id: Optional[uuid.UUID] = None
    source_id: Optional[uuid.UUID] = None
    file_category: str = "GENERAL"
    original_filename: str = ""
    stored_relative_path: str = ""
    mime_type: Optional[str] = None
    file_size_bytes: int = 0
    sha256_hash: str = ""
    uploaded_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    notes: Optional[str] = None

    def validate(self) -> None:
        """Domain validations for Attachment."""
        from app.common.exceptions import ValidationError

        if self.project_id is None and self.entity_id is None:
            raise ValidationError("Attachment must belong to either an Entity or a Project (Gap B-1 resolution).")
        if not self.original_filename:
            raise ValidationError("Original filename is required.")
        if not self.stored_relative_path:
            raise ValidationError("Stored relative path is required.")
        if not self.sha256_hash:
            raise ValidationError("SHA-256 hash is required.")
