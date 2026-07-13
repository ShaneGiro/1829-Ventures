"""Interaction routes."""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Query

from app.core.dependencies import CurrentUser, DbSession
from app.core.permissions import PermissionAction, PermissionResource
from app.repositories import interactions as interaction_repo
from app.schemas.common import PaginatedResponse
from app.schemas.interaction import InteractionCreate, InteractionRead, InteractionUpdate
from app.services import interaction_service
from app.services.permission_service import require_permission

router = APIRouter()


@router.get("", response_model=PaginatedResponse[InteractionRead])
async def list_interactions(
    db: DbSession,
    current_user: CurrentUser,
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    company_id: uuid.UUID | None = None,
    person_id: uuid.UUID | None = None,
    deal_id: uuid.UUID | None = None,
    interaction_type: str | None = None,
    channel: str | None = None,
    direction: str | None = None,
    follow_up_status: str | None = None,
    created_by_id: uuid.UUID | None = None,
    include_archived: bool = False,
) -> PaginatedResponse[InteractionRead]:
    require_permission(current_user, PermissionAction.READ, PermissionResource.CRM)
    interactions = await interaction_repo.list_interactions(
        db,
        limit=limit,
        offset=offset,
        company_id=company_id,
        person_id=person_id,
        deal_id=deal_id,
        interaction_type=interaction_type,
        channel=channel,
        direction=direction,
        follow_up_status=follow_up_status,
        created_by_id=created_by_id,
        include_archived=include_archived,
    )
    total = await interaction_repo.count_interactions(
        db,
        company_id=company_id,
        person_id=person_id,
        deal_id=deal_id,
        interaction_type=interaction_type,
        channel=channel,
        direction=direction,
        follow_up_status=follow_up_status,
        created_by_id=created_by_id,
        include_archived=include_archived,
    )
    return PaginatedResponse(
        items=[InteractionRead.model_validate(interaction) for interaction in interactions],
        total=total,
        limit=limit,
        offset=offset,
    )


@router.post("", response_model=InteractionRead, status_code=201)
async def create_interaction(
    payload: InteractionCreate, db: DbSession, current_user: CurrentUser
) -> InteractionRead:
    require_permission(current_user, PermissionAction.CREATE, PermissionResource.CRM)
    interaction = await interaction_service.create_interaction(db, payload, current_user)
    return InteractionRead.model_validate(interaction)


@router.get("/{interaction_id}", response_model=InteractionRead)
async def get_interaction(
    interaction_id: uuid.UUID,
    db: DbSession,
    current_user: CurrentUser,
    include_archived: bool = False,
) -> InteractionRead:
    require_permission(current_user, PermissionAction.READ, PermissionResource.CRM)
    interaction = await interaction_service.get_interaction(
        db, interaction_id, include_archived=include_archived
    )
    return InteractionRead.model_validate(interaction)


@router.patch("/{interaction_id}", response_model=InteractionRead)
async def update_interaction(
    interaction_id: uuid.UUID,
    payload: InteractionUpdate,
    db: DbSession,
    current_user: CurrentUser,
) -> InteractionRead:
    require_permission(current_user, PermissionAction.UPDATE, PermissionResource.CRM)
    interaction = await interaction_service.update_interaction(
        db, interaction_id, payload, current_user
    )
    return InteractionRead.model_validate(interaction)


@router.post("/{interaction_id}/archive", response_model=InteractionRead)
async def archive_interaction(
    interaction_id: uuid.UUID, db: DbSession, current_user: CurrentUser
) -> InteractionRead:
    require_permission(current_user, PermissionAction.ARCHIVE, PermissionResource.CRM)
    interaction = await interaction_service.archive_interaction(db, interaction_id, current_user)
    return InteractionRead.model_validate(interaction)
