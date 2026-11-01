"""Client persistence repository."""

from datetime import datetime, timezone
from typing import List, Optional
import uuid
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.domain.entities.client import Client
from app.infrastructure.database.models.client_model import ClientModel


class ClientRepository:
    """Repository handling Client entity persistence."""

    def __init__(self, session: Session) -> None:
        self.session = session

    @staticmethod
    def _to_entity(model: ClientModel) -> Client:
        return Client(
            id=model.id,
            client_code=model.client_code,
            display_name=model.display_name,
            client_category=model.client_category,
            phone=model.phone,
            email=model.email,
            address_text=model.address_text,
            notes=model.notes,
            is_active=model.is_active,
            created_at=model.created_at,
            updated_at=model.updated_at,
            created_by_label=model.created_by_label,
            updated_by_label=model.updated_by_label,
        )

    def get_by_id(self, client_id: uuid.UUID) -> Optional[Client]:
        model = self.session.get(ClientModel, client_id)
        return self._to_entity(model) if model else None

    def get_by_code(self, client_code: str) -> Optional[Client]:
        stmt = select(ClientModel).where(ClientModel.client_code == client_code.strip())
        model = self.session.execute(stmt).scalar_one_or_none()
        return self._to_entity(model) if model else None

    def list_all(self, include_archived: bool = False) -> List[Client]:
        stmt = select(ClientModel)
        if not include_archived:
            stmt = stmt.where(ClientModel.is_active.is_(True))
        stmt = stmt.order_by(ClientModel.display_name)
        models = self.session.execute(stmt).scalars().all()
        return [self._to_entity(m) for m in models]

    def save(self, client: Client) -> Client:
        model = self.session.get(ClientModel, client.id)
        now = datetime.now(timezone.utc)
        if model is None:
            model = ClientModel(
                id=client.id,
                client_code=client.client_code,
                display_name=client.display_name,
                client_category=client.client_category,
                phone=client.phone,
                email=client.email,
                address_text=client.address_text,
                notes=client.notes,
                is_active=client.is_active,
                created_at=client.created_at or now,
                updated_at=now,
                created_by_label=client.created_by_label,
                updated_by_label=client.updated_by_label,
            )
            self.session.add(model)
        else:
            model.client_code = client.client_code
            model.display_name = client.display_name
            model.client_category = client.client_category
            model.phone = client.phone
            model.email = client.email
            model.address_text = client.address_text
            model.notes = client.notes
            model.is_active = client.is_active
            model.updated_at = now
            model.updated_by_label = client.updated_by_label

        self.session.flush()
        return self._to_entity(model)

    def archive(self, client_id: uuid.UUID) -> None:
        model = self.session.get(ClientModel, client_id)
        if model:
            model.is_active = False
            model.updated_at = datetime.now(timezone.utc)
            self.session.flush()
