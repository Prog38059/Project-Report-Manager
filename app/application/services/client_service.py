"""Client application service."""

from typing import List, Optional
import uuid

from app.application.dtos.client_dto import (
    CreateClientDTO,
    UpdateClientDTO,
    ClientResponseDTO,
)
from app.common.exceptions import DuplicateEntityError, EntityNotFoundError
from app.domain.entities.client import Client
from app.infrastructure.database.connection import DatabaseManager
from app.infrastructure.repositories.client_repository import ClientRepository


class ClientService:
    """Orchestrates Client use cases."""

    def __init__(self, db_manager: DatabaseManager) -> None:
        self.db_manager = db_manager

    @staticmethod
    def _to_dto(client: Client) -> ClientResponseDTO:
        return ClientResponseDTO(
            id=client.id,
            client_code=client.client_code,
            display_name=client.display_name,
            client_category=client.client_category,
            phone=client.phone,
            email=client.email,
            address_text=client.address_text,
            notes=client.notes,
            is_active=client.is_active,
            created_at=client.created_at,
            updated_at=client.updated_at,
        )

    def create_client(self, dto: CreateClientDTO) -> ClientResponseDTO:
        with self.db_manager.session_scope() as session:
            repo = ClientRepository(session)
            if repo.get_by_code(dto.client_code):
                raise DuplicateEntityError(f"Client code '{dto.client_code}' already exists.")

            client = Client(
                client_code=dto.client_code.strip(),
                display_name=dto.display_name.strip(),
                client_category=dto.client_category,
                phone=dto.phone.strip() if dto.phone else None,
                email=dto.email.strip() if dto.email else None,
                address_text=dto.address_text,
                notes=dto.notes,
            )
            client.validate()
            saved = repo.save(client)
            return self._to_dto(saved)

    def update_client(self, client_id: uuid.UUID, dto: UpdateClientDTO) -> ClientResponseDTO:
        with self.db_manager.session_scope() as session:
            repo = ClientRepository(session)
            client = repo.get_by_id(client_id)
            if not client:
                raise EntityNotFoundError(f"Client '{client_id}' not found.")

            if dto.display_name is not None:
                client.display_name = dto.display_name.strip()
            if dto.client_category is not None:
                client.client_category = dto.client_category
            if dto.phone is not None:
                client.phone = dto.phone.strip() if dto.phone else None
            if dto.email is not None:
                client.email = dto.email.strip() if dto.email else None
            if dto.address_text is not None:
                client.address_text = dto.address_text
            if dto.notes is not None:
                client.notes = dto.notes

            client.validate()
            saved = repo.save(client)
            return self._to_dto(saved)

    def get_client(self, client_id: uuid.UUID) -> Optional[ClientResponseDTO]:
        with self.db_manager.session_scope() as session:
            repo = ClientRepository(session)
            client = repo.get_by_id(client_id)
            return self._to_dto(client) if client else None

    def list_clients(self, include_archived: bool = False) -> List[ClientResponseDTO]:
        with self.db_manager.session_scope() as session:
            repo = ClientRepository(session)
            clients = repo.list_all(include_archived=include_archived)
            return [self._to_dto(c) for c in clients]

    def archive_client(self, client_id: uuid.UUID) -> None:
        with self.db_manager.session_scope() as session:
            repo = ClientRepository(session)
            client = repo.get_by_id(client_id)
            if not client:
                raise EntityNotFoundError(f"Client '{client_id}' not found.")
            repo.archive(client_id)
