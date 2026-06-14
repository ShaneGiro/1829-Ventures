"""People, company contact, and RIT affiliation routes."""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Query

from app.core.dependencies import CurrentUser, DbSession
from app.core.permissions import PermissionAction, PermissionResource
from app.repositories import people as people_repo
from app.schemas.common import PaginatedResponse
from app.schemas.company_contact import (
    CompanyContactCreate,
    CompanyContactRead,
    CompanyContactUpdate,
)
from app.schemas.person import (
    AffiliationCreate,
    AffiliationRead,
    AffiliationUpdate,
    PersonCreate,
    PersonRead,
    PersonUpdate,
)
from app.services import people_service
from app.services.permission_service import require_permission

router = APIRouter()
contacts_router = APIRouter()
affiliations_router = APIRouter()


@router.get("", response_model=PaginatedResponse[PersonRead])
async def list_people(
    db: DbSession,
    current_user: CurrentUser,
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    include_archived: bool = False,
) -> PaginatedResponse[PersonRead]:
    require_permission(current_user, PermissionAction.READ, PermissionResource.CRM)
    people = await people_repo.list_people(
        db, limit=limit, offset=offset, include_archived=include_archived
    )
    total = await people_repo.count_people(db, include_archived=include_archived)
    return PaginatedResponse(
        items=[PersonRead.model_validate(person) for person in people],
        total=total,
        limit=limit,
        offset=offset,
    )


@router.post("", response_model=PersonRead, status_code=201)
async def create_person(
    payload: PersonCreate, db: DbSession, current_user: CurrentUser
) -> PersonRead:
    require_permission(current_user, PermissionAction.CREATE, PermissionResource.CRM)
    person = await people_service.create_person(db, payload, current_user)
    return PersonRead.model_validate(person)


@router.get("/{person_id}", response_model=PersonRead)
async def get_person(
    person_id: uuid.UUID,
    db: DbSession,
    current_user: CurrentUser,
    include_archived: bool = False,
) -> PersonRead:
    require_permission(current_user, PermissionAction.READ, PermissionResource.CRM)
    person = await people_service.get_person(db, person_id, include_archived=include_archived)
    return PersonRead.model_validate(person)


@router.patch("/{person_id}", response_model=PersonRead)
async def update_person(
    person_id: uuid.UUID,
    payload: PersonUpdate,
    db: DbSession,
    current_user: CurrentUser,
) -> PersonRead:
    require_permission(current_user, PermissionAction.UPDATE, PermissionResource.CRM)
    person = await people_service.update_person(db, person_id, payload, current_user)
    return PersonRead.model_validate(person)


@router.post("/{person_id}/archive", response_model=PersonRead)
async def archive_person(
    person_id: uuid.UUID, db: DbSession, current_user: CurrentUser
) -> PersonRead:
    require_permission(current_user, PermissionAction.ARCHIVE, PermissionResource.CRM)
    person = await people_service.archive_person(db, person_id, current_user)
    return PersonRead.model_validate(person)


@router.get("/{person_id}/affiliations", response_model=list[AffiliationRead])
async def list_person_affiliations(
    person_id: uuid.UUID, db: DbSession, current_user: CurrentUser
) -> list[AffiliationRead]:
    require_permission(current_user, PermissionAction.READ, PermissionResource.CRM)
    await people_service.get_person(db, person_id)
    affiliations = await people_repo.list_person_affiliations(db, person_id)
    return [AffiliationRead.model_validate(affiliation) for affiliation in affiliations]


@contacts_router.post("", response_model=CompanyContactRead, status_code=201)
async def create_company_contact(
    payload: CompanyContactCreate, db: DbSession, current_user: CurrentUser
) -> CompanyContactRead:
    require_permission(current_user, PermissionAction.CREATE, PermissionResource.CRM)
    contact = await people_service.create_company_contact(db, payload, current_user)
    return CompanyContactRead.model_validate(contact)


@contacts_router.get("/company/{company_id}", response_model=list[CompanyContactRead])
async def list_company_contacts(
    company_id: uuid.UUID, db: DbSession, current_user: CurrentUser
) -> list[CompanyContactRead]:
    require_permission(current_user, PermissionAction.READ, PermissionResource.CRM)
    contacts = await people_repo.list_company_contacts(db, company_id)
    return [CompanyContactRead.model_validate(contact) for contact in contacts]


@contacts_router.patch("/{contact_id}", response_model=CompanyContactRead)
async def update_company_contact(
    contact_id: uuid.UUID,
    payload: CompanyContactUpdate,
    db: DbSession,
    current_user: CurrentUser,
) -> CompanyContactRead:
    require_permission(current_user, PermissionAction.UPDATE, PermissionResource.CRM)
    contact = await people_service.update_company_contact(db, contact_id, payload, current_user)
    return CompanyContactRead.model_validate(contact)


@affiliations_router.post("", response_model=AffiliationRead, status_code=201)
async def create_affiliation(
    payload: AffiliationCreate, db: DbSession, current_user: CurrentUser
) -> AffiliationRead:
    require_permission(current_user, PermissionAction.CREATE, PermissionResource.CRM)
    affiliation = await people_service.create_affiliation(db, payload, current_user)
    return AffiliationRead.model_validate(affiliation)


@affiliations_router.patch("/{affiliation_id}", response_model=AffiliationRead)
async def update_affiliation(
    affiliation_id: uuid.UUID,
    payload: AffiliationUpdate,
    db: DbSession,
    current_user: CurrentUser,
) -> AffiliationRead:
    require_permission(current_user, PermissionAction.UPDATE, PermissionResource.CRM)
    affiliation = await people_service.update_affiliation(db, affiliation_id, payload, current_user)
    return AffiliationRead.model_validate(affiliation)
