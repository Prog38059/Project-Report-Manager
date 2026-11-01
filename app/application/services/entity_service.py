"""Legal Entity application service."""

from typing import List, Optional
import uuid

from app.application.dtos.entity_dto import (
    CreateEntityDTO,
    UpdateEntityDTO,
    EntityResponseDTO,
    EntityMemberDTO,
)
from app.common.exceptions import EntityNotFoundError
from app.common.types import MemberRoleCode, IdentifierTypeCode
from app.domain.entities.legal_entity import (
    LegalEntity,
    HUFDetails,
    ProprietorshipDetails,
    PartnershipDetails,
    LLPDetails,
    CompanyDetails,
)
from app.domain.entities.entity_member import EntityMember, EntityIdentifier
from app.infrastructure.database.connection import DatabaseManager
from app.infrastructure.repositories.client_repository import ClientRepository
from app.infrastructure.repositories.entity_repository import EntityRepository
from app.infrastructure.security.encryption import EncryptionService


class EntityService:
    """Orchestrates Legal Entity, Constitution Extensions, and Member use cases."""

    def __init__(self, db_manager: DatabaseManager, encryption_service: EncryptionService) -> None:
        self.db_manager = db_manager
        self.encryption_service = encryption_service

    @staticmethod
    def _to_dto(entity: LegalEntity) -> EntityResponseDTO:
        return EntityResponseDTO(
            id=entity.id,
            client_id=entity.client_id,
            constitution_code=entity.constitution_code,
            legal_name=entity.legal_name,
            trade_name=entity.trade_name,
            business_description=entity.business_description,
            accounting_framework_code=entity.accounting_framework_code,
            tax_profile_code=entity.tax_profile_code,
            date_of_formation=entity.date_of_formation,
            active_flag=entity.active_flag,
            created_at=entity.created_at,
            updated_at=entity.updated_at,
        )

    def create_entity(self, dto: CreateEntityDTO) -> EntityResponseDTO:
        with self.db_manager.session_scope() as session:
            client_repo = ClientRepository(session)
            if not client_repo.get_by_id(dto.client_id):
                raise EntityNotFoundError(f"Parent client '{dto.client_id}' does not exist.")

            repo = EntityRepository(session)
            entity = LegalEntity(
                client_id=dto.client_id,
                constitution_code=dto.constitution_code,
                legal_name=dto.legal_name.strip(),
                trade_name=dto.trade_name.strip() if dto.trade_name else None,
                business_description=dto.business_description,
                accounting_framework_code=dto.accounting_framework_code,
                tax_profile_code=dto.tax_profile_code,
                date_of_formation=dto.date_of_formation,
            )
            entity.validate()
            saved = repo.save(entity)
            return self._to_dto(saved)

    def update_entity(self, entity_id: uuid.UUID, dto: UpdateEntityDTO) -> EntityResponseDTO:
        with self.db_manager.session_scope() as session:
            repo = EntityRepository(session)
            entity = repo.get_by_id(entity_id)
            if not entity:
                raise EntityNotFoundError(f"Legal entity '{entity_id}' not found.")

            if dto.legal_name is not None:
                entity.legal_name = dto.legal_name.strip()
            if dto.trade_name is not None:
                entity.trade_name = dto.trade_name.strip() if dto.trade_name else None
            if dto.business_description is not None:
                entity.business_description = dto.business_description
            if dto.accounting_framework_code is not None:
                entity.accounting_framework_code = dto.accounting_framework_code
            if dto.tax_profile_code is not None:
                entity.tax_profile_code = dto.tax_profile_code
            if dto.date_of_formation is not None:
                entity.date_of_formation = dto.date_of_formation

            entity.validate()
            saved = repo.save(entity)
            return self._to_dto(saved)

    def get_entity(self, entity_id: uuid.UUID) -> Optional[EntityResponseDTO]:
        with self.db_manager.session_scope() as session:
            repo = EntityRepository(session)
            entity = repo.get_by_id(entity_id)
            return self._to_dto(entity) if entity else None

    def list_entities_for_client(self, client_id: uuid.UUID) -> List[EntityResponseDTO]:
        with self.db_manager.session_scope() as session:
            repo = EntityRepository(session)
            entities = repo.list_by_client_id(client_id)
            return [self._to_dto(e) for e in entities]

    def archive_entity(self, entity_id: uuid.UUID) -> None:
        with self.db_manager.session_scope() as session:
            repo = EntityRepository(session)
            entity = repo.get_by_id(entity_id)
            if not entity:
                raise EntityNotFoundError(f"Legal entity '{entity_id}' not found.")
            repo.archive(entity_id)

    # Constitution Extensions
    def save_huf_details(self, details: HUFDetails) -> None:
        with self.db_manager.session_scope() as session:
            repo = EntityRepository(session)
            repo.save_huf_details(details)

    def get_huf_details(self, entity_id: uuid.UUID) -> Optional[HUFDetails]:
        with self.db_manager.session_scope() as session:
            repo = EntityRepository(session)
            return repo.get_huf_details(entity_id)

    def save_proprietorship_details(self, details: ProprietorshipDetails) -> None:
        with self.db_manager.session_scope() as session:
            repo = EntityRepository(session)
            repo.save_proprietorship_details(details)

    def get_proprietorship_details(self, entity_id: uuid.UUID) -> Optional[ProprietorshipDetails]:
        with self.db_manager.session_scope() as session:
            repo = EntityRepository(session)
            return repo.get_proprietorship_details(entity_id)

    def save_partnership_details(self, details: PartnershipDetails) -> None:
        with self.db_manager.session_scope() as session:
            repo = EntityRepository(session)
            repo.save_partnership_details(details)

    def get_partnership_details(self, entity_id: uuid.UUID) -> Optional[PartnershipDetails]:
        with self.db_manager.session_scope() as session:
            repo = EntityRepository(session)
            return repo.get_partnership_details(entity_id)

    def save_llp_details(self, details: LLPDetails) -> None:
        with self.db_manager.session_scope() as session:
            repo = EntityRepository(session)
            repo.save_llp_details(details)

    def get_llp_details(self, entity_id: uuid.UUID) -> Optional[LLPDetails]:
        with self.db_manager.session_scope() as session:
            repo = EntityRepository(session)
            return repo.get_llp_details(entity_id)

    def save_company_details(self, details: CompanyDetails) -> None:
        with self.db_manager.session_scope() as session:
            repo = EntityRepository(session)
            repo.save_company_details(details)

    def get_company_details(self, entity_id: uuid.UUID) -> Optional[CompanyDetails]:
        with self.db_manager.session_scope() as session:
            repo = EntityRepository(session)
            return repo.get_company_details(entity_id)

    # Member Management with Encryption
    def add_member(self, dto: EntityMemberDTO) -> EntityMember:
        with self.db_manager.session_scope() as session:
            repo = EntityRepository(session)
            if not repo.get_by_id(dto.entity_id):
                raise EntityNotFoundError(f"Entity '{dto.entity_id}' not found.")

            pan_enc = None
            if dto.pan_plaintext:
                pan_enc = self.encryption_service.encrypt(dto.pan_plaintext.strip().upper())

            member = EntityMember(
                entity_id=dto.entity_id,
                full_name=dto.full_name.strip(),
                role_code=dto.role_code,
                pan_encrypted=pan_enc,
                address_text=dto.address_text,
                contact_phone=dto.contact_phone,
                contact_email=dto.contact_email,
                profit_share_pct=dto.profit_share_pct,
                shareholding_pct=dto.shareholding_pct,
                capital_commitment_paise=dto.capital_commitment_paise,
                date_from=dto.date_from,
                date_to=dto.date_to,
                notes=dto.notes,
            )
            member.validate()
            return repo.save_member(member)

    def list_members(self, entity_id: uuid.UUID, decrypt_pan: bool = False) -> List[EntityMember]:
        with self.db_manager.session_scope() as session:
            repo = EntityRepository(session)
            members = repo.list_members(entity_id)
            if decrypt_pan:
                for m in members:
                    if m.pan_encrypted:
                        m.pan_encrypted = self.encryption_service.decrypt(m.pan_encrypted)
            return members

    # Identifier Management
    def add_identifier(
        self,
        entity_id: uuid.UUID,
        id_type: IdentifierTypeCode,
        id_value_plaintext: str,
        source_attachment_id: Optional[uuid.UUID] = None,
        notes: Optional[str] = None,
    ) -> EntityIdentifier:
        with self.db_manager.session_scope() as session:
            repo = EntityRepository(session)
            if not repo.get_by_id(entity_id):
                raise EntityNotFoundError(f"Entity '{entity_id}' not found.")

            val_enc = self.encryption_service.encrypt(id_value_plaintext.strip())
            val_hash = self.encryption_service.compute_search_hash(id_value_plaintext.strip())

            ident = EntityIdentifier(
                entity_id=entity_id,
                identifier_type=id_type,
                identifier_value_encrypted=val_enc,
                identifier_value_hash=val_hash,
                source_attachment_id=source_attachment_id,
                notes=notes,
            )
            return repo.save_identifier(ident)
