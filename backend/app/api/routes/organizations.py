"""RIT organization and legal-entity routes."""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Query

from app.core.dependencies import CurrentUser, DbSession
from app.core.permissions import PermissionAction, PermissionResource
from app.repositories import organizations as organization_repo
from app.schemas.common import PaginatedResponse
from app.schemas.legal_entity import (
    LegalEntityCreate,
    LegalEntityRead,
    LegalEntityRelationshipCreate,
    LegalEntityRelationshipRead,
    LegalEntityUpdate,
)
from app.schemas.organization import OrganizationCreate, OrganizationRead, OrganizationUpdate
from app.services import organization_service
from app.services.permission_service import require_permission

router = APIRouter()
legal_entities_router = APIRouter()


@router.get("", response_model=PaginatedResponse[OrganizationRead])
async def list_organizations(
    db: DbSession,
    current_user: CurrentUser,
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
) -> PaginatedResponse[OrganizationRead]:
    require_permission(current_user, PermissionAction.READ, PermissionResource.ORGANIZATION)
    organizations = await organization_repo.list_organizations_for_user(
        db, current_user.id, limit=limit, offset=offset
    )
    total = await organization_repo.count_organizations_for_user(db, current_user.id)
    return PaginatedResponse(
        items=[OrganizationRead.model_validate(item) for item in organizations],
        total=total,
        limit=limit,
        offset=offset,
    )


@router.post("", response_model=OrganizationRead, status_code=201)
async def create_organization(
    payload: OrganizationCreate, db: DbSession, current_user: CurrentUser
) -> OrganizationRead:
    require_permission(current_user, PermissionAction.CREATE, PermissionResource.ORGANIZATION)
    organization = await organization_service.create_organization(db, payload, current_user)
    return OrganizationRead.model_validate(organization)


@router.get("/{organization_id}", response_model=OrganizationRead)
async def get_organization(
    organization_id: uuid.UUID, db: DbSession, current_user: CurrentUser
) -> OrganizationRead:
    require_permission(current_user, PermissionAction.READ, PermissionResource.ORGANIZATION)
    organization = await organization_service.get_organization(
        db, organization_id, current_user
    )
    return OrganizationRead.model_validate(organization)


@router.patch("/{organization_id}", response_model=OrganizationRead)
async def update_organization(
    organization_id: uuid.UUID,
    payload: OrganizationUpdate,
    db: DbSession,
    current_user: CurrentUser,
) -> OrganizationRead:
    require_permission(current_user, PermissionAction.UPDATE, PermissionResource.ORGANIZATION)
    organization = await organization_service.update_organization(
        db, organization_id, payload, current_user
    )
    return OrganizationRead.model_validate(organization)


@legal_entities_router.get("", response_model=PaginatedResponse[LegalEntityRead])
async def list_legal_entities(
    organization_id: uuid.UUID,
    db: DbSession,
    current_user: CurrentUser,
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
) -> PaginatedResponse[LegalEntityRead]:
    require_permission(current_user, PermissionAction.READ, PermissionResource.LEGAL_ENTITY)
    await organization_service.get_organization(db, organization_id, current_user)
    entities = await organization_repo.list_legal_entities(
        db, organization_id, limit=limit, offset=offset
    )
    total = await organization_repo.count_legal_entities(db, organization_id)
    return PaginatedResponse(
        items=[LegalEntityRead.model_validate(item) for item in entities],
        total=total,
        limit=limit,
        offset=offset,
    )


@legal_entities_router.post("", response_model=LegalEntityRead, status_code=201)
async def create_legal_entity(
    payload: LegalEntityCreate, db: DbSession, current_user: CurrentUser
) -> LegalEntityRead:
    require_permission(current_user, PermissionAction.CREATE, PermissionResource.LEGAL_ENTITY)
    entity = await organization_service.create_legal_entity(db, payload, current_user)
    return LegalEntityRead.model_validate(entity)


@legal_entities_router.get(
    "/relationships/by-organization/{organization_id}",
    response_model=list[LegalEntityRelationshipRead],
)
async def list_legal_entity_relationships(
    organization_id: uuid.UUID, db: DbSession, current_user: CurrentUser
) -> list[LegalEntityRelationshipRead]:
    require_permission(current_user, PermissionAction.READ, PermissionResource.LEGAL_ENTITY)
    await organization_service.get_organization(db, organization_id, current_user)
    relationships = await organization_repo.list_relationships(db, organization_id)
    return [LegalEntityRelationshipRead.model_validate(item) for item in relationships]


@legal_entities_router.post(
    "/relationships", response_model=LegalEntityRelationshipRead, status_code=201
)
async def create_legal_entity_relationship(
    payload: LegalEntityRelationshipCreate,
    db: DbSession,
    current_user: CurrentUser,
) -> LegalEntityRelationshipRead:
    require_permission(current_user, PermissionAction.CREATE, PermissionResource.LEGAL_ENTITY)
    relationship = await organization_service.create_relationship(db, payload, current_user)
    return LegalEntityRelationshipRead.model_validate(relationship)


@legal_entities_router.get("/{entity_id}", response_model=LegalEntityRead)
async def get_legal_entity(
    entity_id: uuid.UUID, db: DbSession, current_user: CurrentUser
) -> LegalEntityRead:
    require_permission(current_user, PermissionAction.READ, PermissionResource.LEGAL_ENTITY)
    entity = await organization_service.get_legal_entity(db, entity_id, current_user)
    return LegalEntityRead.model_validate(entity)


@legal_entities_router.patch("/{entity_id}", response_model=LegalEntityRead)
async def update_legal_entity(
    entity_id: uuid.UUID,
    payload: LegalEntityUpdate,
    db: DbSession,
    current_user: CurrentUser,
) -> LegalEntityRead:
    require_permission(current_user, PermissionAction.UPDATE, PermissionResource.LEGAL_ENTITY)
    entity = await organization_service.update_legal_entity(
        db, entity_id, payload, current_user
    )
    return LegalEntityRead.model_validate(entity)
