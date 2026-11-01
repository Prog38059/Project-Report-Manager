"""Legal Entity persistence repository."""

from datetime import datetime, timezone
from typing import List, Optional
import uuid
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.common.types import ConstitutionCode, MemberRoleCode, IdentifierTypeCode
from app.domain.entities.legal_entity import (
    LegalEntity,
    HUFDetails,
    ProprietorshipDetails,
    PartnershipDetails,
    LLPDetails,
    CompanyDetails,
)
from app.domain.entities.entity_member import EntityMember, EntityIdentifier
from app.infrastructure.database.models.entity_model import (
    EntityModel,
    EntityMemberModel,
    EntityIdentifierModel,
    HUFDetailsModel,
    ProprietorshipDetailsModel,
    PartnershipDetailsModel,
    LLPDetailsModel,
    CompanyDetailsModel,
)


class EntityRepository:
    """Repository handling LegalEntity, Members, Identifiers, and Constitution Details."""

    def __init__(self, session: Session) -> None:
        self.session = session

    @staticmethod
    def _to_entity(model: EntityModel) -> LegalEntity:
        return LegalEntity(
            id=model.id,
            client_id=model.client_id,
            constitution_code=ConstitutionCode(model.constitution_code),
            legal_name=model.legal_name,
            trade_name=model.trade_name,
            business_description=model.business_description,
            accounting_framework_code=model.accounting_framework_code,
            tax_profile_code=model.tax_profile_code,
            date_of_formation=model.date_of_formation,
            active_flag=model.active_flag,
            created_at=model.created_at,
            updated_at=model.updated_at,
            created_by_label=model.created_by_label,
            updated_by_label=model.updated_by_label,
        )

    def get_by_id(self, entity_id: uuid.UUID) -> Optional[LegalEntity]:
        model = self.session.get(EntityModel, entity_id)
        return self._to_entity(model) if model else None

    def list_by_client_id(self, client_id: uuid.UUID, include_archived: bool = False) -> List[LegalEntity]:
        stmt = select(EntityModel).where(EntityModel.client_id == client_id)
        if not include_archived:
            stmt = stmt.where(EntityModel.active_flag.is_(True))
        stmt = stmt.order_by(EntityModel.legal_name)
        models = self.session.execute(stmt).scalars().all()
        return [self._to_entity(m) for m in models]

    def save(self, entity: LegalEntity) -> LegalEntity:
        model = self.session.get(EntityModel, entity.id)
        now = datetime.now(timezone.utc)
        if model is None:
            model = EntityModel(
                id=entity.id,
                client_id=entity.client_id,
                constitution_code=entity.constitution_code.value if hasattr(entity.constitution_code, "value") else str(entity.constitution_code),
                legal_name=entity.legal_name,
                trade_name=entity.trade_name,
                business_description=entity.business_description,
                accounting_framework_code=entity.accounting_framework_code,
                tax_profile_code=entity.tax_profile_code,
                date_of_formation=entity.date_of_formation,
                active_flag=entity.active_flag,
                created_at=entity.created_at or now,
                updated_at=now,
                created_by_label=entity.created_by_label,
                updated_by_label=entity.updated_by_label,
            )
            self.session.add(model)
        else:
            model.constitution_code = entity.constitution_code.value if hasattr(entity.constitution_code, "value") else str(entity.constitution_code)
            model.legal_name = entity.legal_name
            model.trade_name = entity.trade_name
            model.business_description = entity.business_description
            model.accounting_framework_code = entity.accounting_framework_code
            model.tax_profile_code = entity.tax_profile_code
            model.date_of_formation = entity.date_of_formation
            model.active_flag = entity.active_flag
            model.updated_at = now
            model.updated_by_label = entity.updated_by_label

        self.session.flush()
        return self._to_entity(model)

    def archive(self, entity_id: uuid.UUID) -> None:
        model = self.session.get(EntityModel, entity_id)
        if model:
            model.active_flag = False
            model.is_active = False
            model.updated_at = datetime.now(timezone.utc)
            self.session.flush()

    # Constitution Extensions
    def get_huf_details(self, entity_id: uuid.UUID) -> Optional[HUFDetails]:
        m = self.session.get(HUFDetailsModel, entity_id)
        return HUFDetails(m.entity_id, m.karta_member_id, m.formation_note) if m else None

    def save_huf_details(self, details: HUFDetails) -> None:
        m = self.session.get(HUFDetailsModel, details.entity_id)
        if m is None:
            m = HUFDetailsModel(
                entity_id=details.entity_id,
                karta_member_id=details.karta_member_id,
                formation_note=details.formation_note,
            )
            self.session.add(m)
        else:
            m.karta_member_id = details.karta_member_id
            m.formation_note = details.formation_note
        self.session.flush()

    def get_proprietorship_details(self, entity_id: uuid.UUID) -> Optional[ProprietorshipDetails]:
        m = self.session.get(ProprietorshipDetailsModel, entity_id)
        return ProprietorshipDetails(m.entity_id, m.proprietor_member_id, m.business_start_date) if m else None

    def save_proprietorship_details(self, details: ProprietorshipDetails) -> None:
        m = self.session.get(ProprietorshipDetailsModel, details.entity_id)
        if m is None:
            m = ProprietorshipDetailsModel(
                entity_id=details.entity_id,
                proprietor_member_id=details.proprietor_member_id,
                business_start_date=details.business_start_date,
            )
            self.session.add(m)
        else:
            m.proprietor_member_id = details.proprietor_member_id
            m.business_start_date = details.business_start_date
        self.session.flush()

    def get_partnership_details(self, entity_id: uuid.UUID) -> Optional[PartnershipDetails]:
        m = self.session.get(PartnershipDetailsModel, entity_id)
        return PartnershipDetails(m.entity_id, m.deed_date, m.registration_status, m.deed_attachment_id) if m else None

    def save_partnership_details(self, details: PartnershipDetails) -> None:
        m = self.session.get(PartnershipDetailsModel, details.entity_id)
        if m is None:
            m = PartnershipDetailsModel(
                entity_id=details.entity_id,
                deed_date=details.deed_date,
                registration_status=details.registration_status,
                deed_attachment_id=details.deed_attachment_id,
            )
            self.session.add(m)
        else:
            m.deed_date = details.deed_date
            m.registration_status = details.registration_status
            m.deed_attachment_id = details.deed_attachment_id
        self.session.flush()

    def get_llp_details(self, entity_id: uuid.UUID) -> Optional[LLPDetails]:
        m = self.session.get(LLPDetailsModel, entity_id)
        return LLPDetails(m.entity_id, m.incorporation_date, m.llp_agreement_date, m.agreement_attachment_id) if m else None

    def save_llp_details(self, details: LLPDetails) -> None:
        m = self.session.get(LLPDetailsModel, details.entity_id)
        if m is None:
            m = LLPDetailsModel(
                entity_id=details.entity_id,
                incorporation_date=details.incorporation_date,
                llp_agreement_date=details.llp_agreement_date,
                agreement_attachment_id=details.agreement_attachment_id,
            )
            self.session.add(m)
        else:
            m.incorporation_date = details.incorporation_date
            m.llp_agreement_date = details.llp_agreement_date
            m.agreement_attachment_id = details.agreement_attachment_id
        self.session.flush()

    def get_company_details(self, entity_id: uuid.UUID) -> Optional[CompanyDetails]:
        m = self.session.get(CompanyDetailsModel, entity_id)
        return CompanyDetails(
            m.entity_id,
            m.incorporation_date,
            m.company_class,
            m.authorised_capital_paise,
            m.paid_up_capital_paise,
            m.registered_office_address,
        ) if m else None

    def save_company_details(self, details: CompanyDetails) -> None:
        m = self.session.get(CompanyDetailsModel, details.entity_id)
        if m is None:
            m = CompanyDetailsModel(
                entity_id=details.entity_id,
                incorporation_date=details.incorporation_date,
                company_class=details.company_class,
                authorised_capital_paise=details.authorised_capital_paise,
                paid_up_capital_paise=details.paid_up_capital_paise,
                registered_office_address=details.registered_office_address,
            )
            self.session.add(m)
        else:
            m.incorporation_date = details.incorporation_date
            m.company_class = details.company_class
            m.authorised_capital_paise = details.authorised_capital_paise
            m.paid_up_capital_paise = details.paid_up_capital_paise
            m.registered_office_address = details.registered_office_address
        self.session.flush()

    # Member operations
    @staticmethod
    def _member_to_entity(m: EntityMemberModel) -> EntityMember:
        return EntityMember(
            id=m.id,
            entity_id=m.entity_id,
            full_name=m.full_name,
            role_code=MemberRoleCode(m.role_code),
            pan_encrypted=m.pan_encrypted,
            address_text=m.address_text,
            contact_phone=m.contact_phone,
            contact_email=m.contact_email,
            profit_share_pct=m.profit_share_pct,
            shareholding_pct=m.shareholding_pct,
            capital_commitment_paise=m.capital_commitment_paise,
            date_from=m.date_from,
            date_to=m.date_to,
            notes=m.notes,
            is_active=m.is_active,
            created_at=m.created_at,
            updated_at=m.updated_at,
            created_by_label=m.created_by_label,
            updated_by_label=m.updated_by_label,
        )

    def list_members(self, entity_id: uuid.UUID, include_archived: bool = False) -> List[EntityMember]:
        stmt = select(EntityMemberModel).where(EntityMemberModel.entity_id == entity_id)
        if not include_archived:
            stmt = stmt.where(EntityMemberModel.is_active.is_(True))
        models = self.session.execute(stmt).scalars().all()
        return [self._member_to_entity(m) for m in models]

    def get_member(self, member_id: uuid.UUID) -> Optional[EntityMember]:
        m = self.session.get(EntityMemberModel, member_id)
        return self._member_to_entity(m) if m else None

    def save_member(self, member: EntityMember) -> EntityMember:
        m = self.session.get(EntityMemberModel, member.id)
        now = datetime.now(timezone.utc)
        role_str = member.role_code.value if hasattr(member.role_code, "value") else str(member.role_code)
        if m is None:
            m = EntityMemberModel(
                id=member.id,
                entity_id=member.entity_id,
                full_name=member.full_name,
                role_code=role_str,
                pan_encrypted=member.pan_encrypted,
                address_text=member.address_text,
                contact_phone=member.contact_phone,
                contact_email=member.contact_email,
                profit_share_pct=member.profit_share_pct,
                shareholding_pct=member.shareholding_pct,
                capital_commitment_paise=member.capital_commitment_paise,
                date_from=member.date_from,
                date_to=member.date_to,
                notes=member.notes,
                is_active=member.is_active,
                created_at=member.created_at or now,
                updated_at=now,
                created_by_label=member.created_by_label,
                updated_by_label=member.updated_by_label,
            )
            self.session.add(m)
        else:
            m.full_name = member.full_name
            m.role_code = role_str
            m.pan_encrypted = member.pan_encrypted
            m.address_text = member.address_text
            m.contact_phone = member.contact_phone
            m.contact_email = member.contact_email
            m.profit_share_pct = member.profit_share_pct
            m.shareholding_pct = member.shareholding_pct
            m.capital_commitment_paise = member.capital_commitment_paise
            m.date_from = member.date_from
            m.date_to = member.date_to
            m.notes = member.notes
            m.is_active = member.is_active
            m.updated_at = now
            m.updated_by_label = member.updated_by_label

        self.session.flush()
        return self._member_to_entity(m)

    def archive_member(self, member_id: uuid.UUID) -> None:
        m = self.session.get(EntityMemberModel, member_id)
        if m:
            m.is_active = False
            m.updated_at = datetime.now(timezone.utc)
            self.session.flush()

    # Identifier operations
    @staticmethod
    def _identifier_to_entity(m: EntityIdentifierModel) -> EntityIdentifier:
        return EntityIdentifier(
            id=m.id,
            entity_id=m.entity_id,
            identifier_type=IdentifierTypeCode(m.identifier_type),
            identifier_value_encrypted=m.identifier_value_encrypted,
            identifier_value_hash=m.identifier_value_hash,
            valid_from=m.valid_from,
            valid_to=m.valid_to,
            verification_status=m.verification_status,
            source_attachment_id=m.source_attachment_id,
            notes=m.notes,
            created_at=m.created_at,
            updated_at=m.updated_at,
        )

    def list_identifiers(self, entity_id: uuid.UUID) -> List[EntityIdentifier]:
        stmt = select(EntityIdentifierModel).where(
            EntityIdentifierModel.entity_id == entity_id,
            EntityIdentifierModel.is_active.is_(True),
        )
        models = self.session.execute(stmt).scalars().all()
        return [self._identifier_to_entity(m) for m in models]

    def save_identifier(self, identifier: EntityIdentifier) -> EntityIdentifier:
        m = self.session.get(EntityIdentifierModel, identifier.id)
        now = datetime.now(timezone.utc)
        id_type_str = identifier.identifier_type.value if hasattr(identifier.identifier_type, "value") else str(identifier.identifier_type)
        if m is None:
            m = EntityIdentifierModel(
                id=identifier.id,
                entity_id=identifier.entity_id,
                identifier_type=id_type_str,
                identifier_value_encrypted=identifier.identifier_value_encrypted,
                identifier_value_hash=identifier.identifier_value_hash,
                valid_from=identifier.valid_from,
                valid_to=identifier.valid_to,
                verification_status=identifier.verification_status,
                source_attachment_id=identifier.source_attachment_id,
                notes=identifier.notes,
                created_at=identifier.created_at or now,
                updated_at=now,
            )
            self.session.add(m)
        else:
            m.identifier_type = id_type_str
            m.identifier_value_encrypted = identifier.identifier_value_encrypted
            m.identifier_value_hash = identifier.identifier_value_hash
            m.valid_from = identifier.valid_from
            m.valid_to = identifier.valid_to
            m.verification_status = identifier.verification_status
            m.source_attachment_id = identifier.source_attachment_id
            m.notes = identifier.notes
            m.updated_at = now

        self.session.flush()
        return self._identifier_to_entity(m)
