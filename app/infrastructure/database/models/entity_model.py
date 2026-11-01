"""Legal Entity and constitution extension SQLAlchemy ORM models."""

import uuid
from datetime import date
from typing import Optional, List
from sqlalchemy import (
    String,
    Text,
    Date,
    Boolean,
    BigInteger,
    ForeignKey,
    Index,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.infrastructure.database.models.base import Base, GUID, TimestampMixin


class EntityModel(Base, TimestampMixin):
    """Legal business/applicant entity."""
    __tablename__ = "entities"

    id: Mapped[uuid.UUID] = mapped_column(GUID, primary_key=True, default=uuid.uuid4)
    client_id: Mapped[uuid.UUID] = mapped_column(
        GUID,
        ForeignKey("clients.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    constitution_code: Mapped[str] = mapped_column(String(30), nullable=False, index=True)
    legal_name: Mapped[str] = mapped_column(String(250), nullable=False)
    trade_name: Mapped[Optional[str]] = mapped_column(String(250), nullable=True)
    business_description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    accounting_framework_code: Mapped[Optional[str]] = mapped_column(String(40), nullable=True)
    tax_profile_code: Mapped[Optional[str]] = mapped_column(String(40), nullable=True)
    date_of_formation: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    active_flag: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    # Relationships
    client: Mapped["ClientModel"] = relationship("ClientModel", back_populates="entities")
    members: Mapped[List["EntityMemberModel"]] = relationship(
        "EntityMemberModel",
        back_populates="entity",
        cascade="all, delete-orphan",
    )
    identifiers: Mapped[List["EntityIdentifierModel"]] = relationship(
        "EntityIdentifierModel",
        back_populates="entity",
        cascade="all, delete-orphan",
    )
    projects: Mapped[List["ProjectModel"]] = relationship(
        "ProjectModel",
        back_populates="entity",
        cascade="all, delete-orphan",
    )

    # 1:1 Constitution extensions
    huf_details: Mapped[Optional["HUFDetailsModel"]] = relationship(
        "HUFDetailsModel",
        uselist=False,
        cascade="all, delete-orphan",
    )
    proprietorship_details: Mapped[Optional["ProprietorshipDetailsModel"]] = relationship(
        "ProprietorshipDetailsModel",
        uselist=False,
        cascade="all, delete-orphan",
    )
    partnership_details: Mapped[Optional["PartnershipDetailsModel"]] = relationship(
        "PartnershipDetailsModel",
        uselist=False,
        cascade="all, delete-orphan",
    )
    llp_details: Mapped[Optional["LLPDetailsModel"]] = relationship(
        "LLPDetailsModel",
        uselist=False,
        cascade="all, delete-orphan",
    )
    company_details: Mapped[Optional["CompanyDetailsModel"]] = relationship(
        "CompanyDetailsModel",
        uselist=False,
        cascade="all, delete-orphan",
    )

    __table_args__ = (
        Index("idx_entities_client_legal_name", "client_id", "legal_name"),
    )


class EntityMemberModel(Base, TimestampMixin):
    """Person associated with an entity."""
    __tablename__ = "entity_members"

    id: Mapped[uuid.UUID] = mapped_column(GUID, primary_key=True, default=uuid.uuid4)
    entity_id: Mapped[uuid.UUID] = mapped_column(
        GUID,
        ForeignKey("entities.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    full_name: Mapped[str] = mapped_column(String(200), nullable=False)
    role_code: Mapped[str] = mapped_column(String(35), nullable=False)
    pan_encrypted: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    address_text: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    contact_phone: Mapped[Optional[str]] = mapped_column(String(30), nullable=True)
    contact_email: Mapped[Optional[str]] = mapped_column(String(254), nullable=True)
    profit_share_pct: Mapped[Optional[str]] = mapped_column(String(40), nullable=True)
    shareholding_pct: Mapped[Optional[str]] = mapped_column(String(40), nullable=True)
    capital_commitment_paise: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    date_from: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    date_to: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    entity: Mapped["EntityModel"] = relationship("EntityModel", back_populates="members")


class EntityIdentifierModel(Base, TimestampMixin):
    """Statutory identifier for an entity."""
    __tablename__ = "entity_identifiers"

    id: Mapped[uuid.UUID] = mapped_column(GUID, primary_key=True, default=uuid.uuid4)
    entity_id: Mapped[uuid.UUID] = mapped_column(
        GUID,
        ForeignKey("entities.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    identifier_type: Mapped[str] = mapped_column(String(30), nullable=False)
    identifier_value_encrypted: Mapped[str] = mapped_column(Text, nullable=False)
    identifier_value_hash: Mapped[Optional[str]] = mapped_column(String(128), nullable=True, index=True)
    valid_from: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    valid_to: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    verification_status: Mapped[str] = mapped_column(String(25), nullable=False, default="UNVERIFIED")
    source_attachment_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        GUID,
        ForeignKey("attachments.id", ondelete="SET NULL"),
        nullable=True,
    )
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    entity: Mapped["EntityModel"] = relationship("EntityModel", back_populates="identifiers")

    __table_args__ = (
        Index("idx_entity_identifiers_lookup", "entity_id", "identifier_type"),
    )


class HUFDetailsModel(Base):
    """HUF specific details."""
    __tablename__ = "huf_details"

    entity_id: Mapped[uuid.UUID] = mapped_column(
        GUID,
        ForeignKey("entities.id", ondelete="CASCADE"),
        primary_key=True,
    )
    karta_member_id: Mapped[uuid.UUID] = mapped_column(
        GUID,
        ForeignKey("entity_members.id", ondelete="RESTRICT"),
        nullable=False,
    )
    formation_note: Mapped[Optional[str]] = mapped_column(Text, nullable=True)


class ProprietorshipDetailsModel(Base):
    """Proprietorship specific details."""
    __tablename__ = "proprietorship_details"

    entity_id: Mapped[uuid.UUID] = mapped_column(
        GUID,
        ForeignKey("entities.id", ondelete="CASCADE"),
        primary_key=True,
    )
    proprietor_member_id: Mapped[uuid.UUID] = mapped_column(
        GUID,
        ForeignKey("entity_members.id", ondelete="RESTRICT"),
        nullable=False,
    )
    business_start_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)


class PartnershipDetailsModel(Base):
    """Partnership specific details."""
    __tablename__ = "partnership_details"

    entity_id: Mapped[uuid.UUID] = mapped_column(
        GUID,
        ForeignKey("entities.id", ondelete="CASCADE"),
        primary_key=True,
    )
    deed_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    registration_status: Mapped[Optional[str]] = mapped_column(String(25), nullable=True)
    deed_attachment_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        GUID,
        ForeignKey("attachments.id", ondelete="SET NULL"),
        nullable=True,
    )


class LLPDetailsModel(Base):
    """LLP specific details."""
    __tablename__ = "llp_details"

    entity_id: Mapped[uuid.UUID] = mapped_column(
        GUID,
        ForeignKey("entities.id", ondelete="CASCADE"),
        primary_key=True,
    )
    incorporation_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    llp_agreement_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    agreement_attachment_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        GUID,
        ForeignKey("attachments.id", ondelete="SET NULL"),
        nullable=True,
    )


class CompanyDetailsModel(Base):
    """Company specific details."""
    __tablename__ = "company_details"

    entity_id: Mapped[uuid.UUID] = mapped_column(
        GUID,
        ForeignKey("entities.id", ondelete="CASCADE"),
        primary_key=True,
    )
    incorporation_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    company_class: Mapped[Optional[str]] = mapped_column(String(30), nullable=True)
    authorised_capital_paise: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    paid_up_capital_paise: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    registered_office_address: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
