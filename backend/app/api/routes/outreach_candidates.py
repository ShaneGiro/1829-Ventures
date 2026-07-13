"""Derived Outreach Candidates queue."""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Query

from app.core.dependencies import CurrentUser, DbSession
from app.core.permissions import PermissionAction, PermissionResource
from app.schemas.common import PaginatedResponse
from app.schemas.outreach_candidate import (
    OutreachCandidateListCreate,
    OutreachCandidateListDetail,
    OutreachCandidateListItemCreate,
    OutreachCandidateListItemRead,
    OutreachCandidateListItemUpdate,
    OutreachCandidateListRead,
    OutreachCandidateListUpdate,
    OutreachCandidateRead,
)
from app.services import outreach_candidate_list_service, outreach_candidate_service
from app.services.permission_service import require_permission

router = APIRouter()


@router.get("", response_model=PaginatedResponse[OutreachCandidateRead])
async def list_outreach_candidates(
    db: DbSession,
    current_user: CurrentUser,
    limit: int = Query(default=100, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    include_recently_contacted: bool = False,
) -> PaginatedResponse[OutreachCandidateRead]:
    require_permission(current_user, PermissionAction.READ, PermissionResource.CRM)
    items, total = await outreach_candidate_service.list_candidates(
        db,
        limit=limit,
        offset=offset,
        include_recently_contacted=include_recently_contacted,
    )
    return PaginatedResponse(items=items, total=total, limit=limit, offset=offset)


@router.post("/lists", response_model=OutreachCandidateListRead, status_code=201)
async def create_candidate_list(
    payload: OutreachCandidateListCreate,
    db: DbSession,
    current_user: CurrentUser,
) -> OutreachCandidateListRead:
    require_permission(current_user, PermissionAction.CREATE, PermissionResource.CRM)
    candidate_list = await outreach_candidate_list_service.create_candidate_list(
        db, payload, current_user
    )
    return OutreachCandidateListRead.model_validate(candidate_list)


@router.get("/lists", response_model=PaginatedResponse[OutreachCandidateListRead])
async def list_candidate_lists(
    db: DbSession,
    current_user: CurrentUser,
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    include_archived: bool = False,
) -> PaginatedResponse[OutreachCandidateListRead]:
    require_permission(current_user, PermissionAction.READ, PermissionResource.CRM)
    lists, total = await outreach_candidate_list_service.list_candidate_lists(
        db,
        limit=limit,
        offset=offset,
        include_archived=include_archived,
    )
    return PaginatedResponse(
        items=[OutreachCandidateListRead.model_validate(item) for item in lists],
        total=total,
        limit=limit,
        offset=offset,
    )


@router.get("/lists/{list_id}", response_model=OutreachCandidateListDetail)
async def get_candidate_list(
    list_id: uuid.UUID,
    db: DbSession,
    current_user: CurrentUser,
    include_archived: bool = False,
) -> OutreachCandidateListDetail:
    require_permission(current_user, PermissionAction.READ, PermissionResource.CRM)
    candidate_list = await outreach_candidate_list_service.get_candidate_list(
        db, list_id, include_archived=include_archived
    )
    return OutreachCandidateListDetail.model_validate(candidate_list)


@router.patch("/lists/{list_id}", response_model=OutreachCandidateListRead)
async def update_candidate_list(
    list_id: uuid.UUID,
    payload: OutreachCandidateListUpdate,
    db: DbSession,
    current_user: CurrentUser,
) -> OutreachCandidateListRead:
    require_permission(current_user, PermissionAction.UPDATE, PermissionResource.CRM)
    candidate_list = await outreach_candidate_list_service.update_candidate_list(
        db, list_id, payload, current_user
    )
    return OutreachCandidateListRead.model_validate(candidate_list)


@router.post(
    "/lists/{list_id}/items",
    response_model=OutreachCandidateListItemRead,
    status_code=201,
)
async def add_candidate_list_item(
    list_id: uuid.UUID,
    payload: OutreachCandidateListItemCreate,
    db: DbSession,
    current_user: CurrentUser,
) -> OutreachCandidateListItemRead:
    require_permission(current_user, PermissionAction.CREATE, PermissionResource.CRM)
    item = await outreach_candidate_list_service.add_candidate_list_item(
        db, list_id, payload, current_user
    )
    return OutreachCandidateListItemRead.model_validate(item)


@router.patch(
    "/lists/{list_id}/items/{item_id}",
    response_model=OutreachCandidateListItemRead,
)
async def update_candidate_list_item(
    list_id: uuid.UUID,
    item_id: uuid.UUID,
    payload: OutreachCandidateListItemUpdate,
    db: DbSession,
    current_user: CurrentUser,
) -> OutreachCandidateListItemRead:
    require_permission(current_user, PermissionAction.UPDATE, PermissionResource.CRM)
    item = await outreach_candidate_list_service.update_candidate_list_item(
        db, list_id, item_id, payload, current_user
    )
    return OutreachCandidateListItemRead.model_validate(item)
