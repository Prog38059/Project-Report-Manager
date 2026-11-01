"""Integration tests for Client, Entity (6 constitutions), Member, and Project CRUD."""

from datetime import date
import pytest
import uuid

from app.application.dtos.client_dto import CreateClientDTO, UpdateClientDTO
from app.application.dtos.entity_dto import CreateEntityDTO, UpdateEntityDTO, EntityMemberDTO
from app.application.dtos.project_dto import CreateProjectDTO
from app.application.services.client_service import ClientService
from app.application.services.entity_service import EntityService
from app.application.services.project_service import ProjectService
from app.common.exceptions import DuplicateEntityError, EntityNotFoundError
from app.common.types import ConstitutionCode, MemberRoleCode, PeriodRole, PeriodType
from app.domain.entities.legal_entity import (
    HUFDetails,
    ProprietorshipDetails,
    PartnershipDetails,
    LLPDetails,
    CompanyDetails,
)


def test_client_crud_lifecycle(client_service: ClientService):
    # 1. Create
    dto = CreateClientDTO(
        client_code="CLT-TEST-001",
        display_name="Ramesh Sharma",
        client_category="PERSON",
        phone="+91 9876543210",
        email="ramesh@example.com",
    )
    client = client_service.create_client(dto)
    assert client.id is not None
    assert client.client_code == "CLT-TEST-001"
    assert client.display_name == "Ramesh Sharma"

    # 2. Duplicate code rejected
    with pytest.raises(DuplicateEntityError):
        client_service.create_client(dto)

    # 3. Read
    fetched = client_service.get_client(client.id)
    assert fetched is not None
    assert fetched.client_code == "CLT-TEST-001"

    # 4. Update
    updated = client_service.update_client(client.id, UpdateClientDTO(display_name="Ramesh K. Sharma"))
    assert updated.display_name == "Ramesh K. Sharma"

    # 5. List
    all_clients = client_service.list_clients()
    assert any(c.client_code == "CLT-TEST-001" for c in all_clients)

    # 6. Archive
    client_service.archive_client(client.id)
    active_clients = client_service.list_clients(include_archived=False)
    assert not any(c.client_code == "CLT-TEST-001" for c in active_clients)


def test_all_six_constitutions_and_members(client_service: ClientService, entity_service: EntityService):
    # Create master client
    client = client_service.create_client(
        CreateClientDTO(client_code="CLT-MULTI-001", display_name="National Enterprises Group")
    )

    # 1. INDIVIDUAL
    ent_ind = entity_service.create_entity(
        CreateEntityDTO(
            client_id=client.id,
            constitution_code=ConstitutionCode.INDIVIDUAL,
            legal_name="Suresh Kumar",
        )
    )
    assert ent_ind.constitution_code == ConstitutionCode.INDIVIDUAL

    # 2. PROPRIETORSHIP
    ent_prop = entity_service.create_entity(
        CreateEntityDTO(
            client_id=client.id,
            constitution_code=ConstitutionCode.PROPRIETORSHIP,
            legal_name="Suresh Trading Co",
            trade_name="Suresh Enterprises",
        )
    )
    # Add proprietor member
    proprietor = entity_service.add_member(
        EntityMemberDTO(
            entity_id=ent_prop.id,
            full_name="Suresh Kumar",
            role_code=MemberRoleCode.PROPRIETOR,
            pan_plaintext="ABCDE1111A",
        )
    )
    entity_service.save_proprietorship_details(
        ProprietorshipDetails(
            entity_id=ent_prop.id,
            proprietor_member_id=proprietor.id,
            business_start_date=date(2020, 1, 15),
        )
    )
    prop_details = entity_service.get_proprietorship_details(ent_prop.id)
    assert prop_details is not None
    assert prop_details.proprietor_member_id == proprietor.id

    # 3. HUF
    ent_huf = entity_service.create_entity(
        CreateEntityDTO(
            client_id=client.id,
            constitution_code=ConstitutionCode.HUF,
            legal_name="Suresh Kumar HUF",
        )
    )
    karta = entity_service.add_member(
        EntityMemberDTO(
            entity_id=ent_huf.id,
            full_name="Suresh Kumar",
            role_code=MemberRoleCode.KARTA,
            pan_plaintext="ABCDE2222B",
        )
    )
    entity_service.save_huf_details(
        HUFDetails(entity_id=ent_huf.id, karta_member_id=karta.id, formation_note="Ancestral HUF")
    )
    huf_details = entity_service.get_huf_details(ent_huf.id)
    assert huf_details is not None
    assert huf_details.karta_member_id == karta.id

    # 4. PARTNERSHIP
    ent_part = entity_service.create_entity(
        CreateEntityDTO(
            client_id=client.id,
            constitution_code=ConstitutionCode.PARTNERSHIP,
            legal_name="Sharma & Brothers",
        )
    )
    p1 = entity_service.add_member(
        EntityMemberDTO(
            entity_id=ent_part.id,
            full_name="Partner One",
            role_code=MemberRoleCode.PARTNER,
            profit_share_pct="60.0",
        )
    )
    p2 = entity_service.add_member(
        EntityMemberDTO(
            entity_id=ent_part.id,
            full_name="Partner Two",
            role_code=MemberRoleCode.PARTNER,
            profit_share_pct="40.0",
        )
    )
    entity_service.save_partnership_details(
        PartnershipDetails(
            entity_id=ent_part.id,
            deed_date=date(2021, 4, 1),
            registration_status="REGISTERED",
        )
    )
    part_details = entity_service.get_partnership_details(ent_part.id)
    assert part_details is not None
    assert part_details.registration_status == "REGISTERED"

    # 5. LLP
    ent_llp = entity_service.create_entity(
        CreateEntityDTO(
            client_id=client.id,
            constitution_code=ConstitutionCode.LLP,
            legal_name="Green Tech Logistics LLP",
        )
    )
    dp = entity_service.add_member(
        EntityMemberDTO(
            entity_id=ent_llp.id,
            full_name="Designated Partner A",
            role_code=MemberRoleCode.DESIGNATED_PARTNER,
            pan_plaintext="ABCDE3333C",
        )
    )
    entity_service.save_llp_details(
        LLPDetails(
            entity_id=ent_llp.id,
            incorporation_date=date(2022, 6, 1),
            llp_agreement_date=date(2022, 6, 10),
        )
    )
    llp_details = entity_service.get_llp_details(ent_llp.id)
    assert llp_details is not None
    assert llp_details.incorporation_date == date(2022, 6, 1)

    # 6. PRIVATE_LIMITED
    ent_co = entity_service.create_entity(
        CreateEntityDTO(
            client_id=client.id,
            constitution_code=ConstitutionCode.PRIVATE_LIMITED,
            legal_name="Nexus Infotech Private Limited",
        )
    )
    director = entity_service.add_member(
        EntityMemberDTO(
            entity_id=ent_co.id,
            full_name="Managing Director X",
            role_code=MemberRoleCode.DIRECTOR,
            pan_plaintext="ABCDE4444D",
            shareholding_pct="75.0",
        )
    )
    entity_service.save_company_details(
        CompanyDetails(
            entity_id=ent_co.id,
            incorporation_date=date(2023, 3, 1),
            company_class="PRIVATE",
            authorised_capital_paise=1000000000,  # ₹1 crore
            paid_up_capital_paise=500000000,     # ₹50 lakhs
        )
    )
    co_details = entity_service.get_company_details(ent_co.id)
    assert co_details is not None
    assert co_details.authorised_capital_paise == 1000000000

    # Test member listing with PAN decryption
    co_members = entity_service.list_members(ent_co.id, decrypt_pan=True)
    assert len(co_members) == 1
    assert co_members[0].pan_encrypted == "ABCDE4444D"  # Decrypted matches original!


def test_project_creation_and_period_generation(
    client_service: ClientService,
    entity_service: EntityService,
    project_service: ProjectService,
):
    client = client_service.create_client(
        CreateClientDTO(client_code="CLT-PRJ-01", display_name="Energy Corp")
    )
    entity = entity_service.create_entity(
        CreateEntityDTO(
            client_id=client.id,
            constitution_code=ConstitutionCode.LLP,
            legal_name="Green Energy Projects LLP",
        )
    )

    # Create project with standard 7-year default and historical off
    dto = CreateProjectDTO(
        entity_id=entity.id,
        project_code="PRJ-EV-2026",
        project_name="EV Fast Charging Hub",
        projection_year_count=7,
        projection_start_financial_year=2026,
        financial_year_start_month=4,
        historical_data_enabled=False,
    )
    project = project_service.create_project(dto)
    assert project.id is not None
    assert project.project_code == "PRJ-EV-2026"
    assert project.projection_year_count == 7
    assert project.historical_data_enabled is False

    # Verify default Base scenario automatically generated
    scenarios = project_service.list_scenarios(project.id)
    assert len(scenarios) == 1
    assert scenarios[0].scenario_code == "BASE"
    assert scenarios[0].is_default is True

    # Verify 7 annual projection periods automatically generated
    periods = project_service.list_periods(project.id)
    assert len(periods) == 7
    for idx, p in enumerate(periods, start=1):
        assert p.period_sequence == idx
        assert p.period_role == PeriodRole.PROJECTION
        assert p.period_label == f"Project Year {idx}"
        assert p.is_report_column is True
        # Check financial year label format: e.g. FY 2026-27 for Y1, FY 2032-33 for Y7
        expected_start = 2026 + idx - 1
        expected_end = expected_start + 1
        expected_fy = f"FY {expected_start}-{str(expected_end)[-2:]}"
        assert p.financial_year_label == expected_fy
        assert p.start_date == date(expected_start, 4, 1)
        assert p.end_date == date(expected_end, 3, 31)

    # Test global uniqueness of project code
    with pytest.raises(DuplicateEntityError):
        project_service.create_project(dto)
