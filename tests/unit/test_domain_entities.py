"""Unit tests for domain entity validations."""

import pytest
import uuid

from app.common.exceptions import ValidationError
from app.common.types import ConstitutionCode, MemberRoleCode
from app.domain.entities.client import Client
from app.domain.entities.legal_entity import LegalEntity
from app.domain.entities.entity_member import EntityMember
from app.domain.entities.project import Project
from app.domain.entities.attachment import Attachment


def test_client_validation():
    valid = Client(client_code="CLT-1", display_name="Acme Corp")
    valid.validate()  # Passes

    with pytest.raises(ValidationError, match="Client code is required"):
        Client(client_code="", display_name="Acme").validate()

    with pytest.raises(ValidationError, match="Display name is required"):
        Client(client_code="CLT-1", display_name="").validate()


def test_legal_entity_validation():
    valid = LegalEntity(
        client_id=uuid.uuid4(),
        constitution_code=ConstitutionCode.LLP,
        legal_name="Alpha LLP",
    )
    valid.validate()

    with pytest.raises(ValidationError, match="Legal name is required"):
        LegalEntity(client_id=uuid.uuid4(), constitution_code=ConstitutionCode.LLP, legal_name="").validate()


def test_entity_member_validation():
    valid = EntityMember(
        entity_id=uuid.uuid4(),
        full_name="John Doe",
        role_code=MemberRoleCode.PARTNER,
    )
    valid.validate()

    with pytest.raises(ValidationError, match="Member full name is required"):
        EntityMember(entity_id=uuid.uuid4(), full_name="", role_code=MemberRoleCode.PARTNER).validate()


def test_project_validation():
    valid = Project(
        entity_id=uuid.uuid4(),
        project_code="PRJ-1",
        project_name="Solar Power Plant",
        projection_year_count=7,
        financial_year_start_month=4,
    )
    valid.validate()

    with pytest.raises(ValidationError, match="Financial year start month must be between 1 and 12"):
        Project(
            entity_id=uuid.uuid4(),
            project_code="PRJ-1",
            project_name="Solar Plant",
            financial_year_start_month=13,
        ).validate()

    with pytest.raises(ValidationError, match="Projection horizon must be between 1 and 30"):
        Project(
            entity_id=uuid.uuid4(),
            project_code="PRJ-1",
            project_name="Solar Plant",
            projection_year_count=0,
        ).validate()


def test_attachment_validation_gap_b1():
    # Gap B-1 rule: Must belong to either entity or project or both
    with pytest.raises(ValidationError, match="Attachment must belong to either an Entity or a Project"):
        Attachment(
            project_id=None,
            entity_id=None,
            original_filename="doc.pdf",
            stored_relative_path="general/doc.pdf",
            sha256_hash="abc",
        ).validate()

    # Valid with entity_id alone
    valid_entity_doc = Attachment(
        project_id=None,
        entity_id=uuid.uuid4(),
        original_filename="deed.pdf",
        stored_relative_path="entities/deed.pdf",
        sha256_hash="abc123hash",
    )
    valid_entity_doc.validate()
