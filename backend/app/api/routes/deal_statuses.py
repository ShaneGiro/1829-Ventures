"""Configurable pipeline stage routes."""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Query

from app.core.dependencies import CurrentUser, DbSession
from app.core.exceptions import ConflictError, NotFoundError, ValidationError
from app.core.permissions import PermissionAction, PermissionResource
from app.repositories import deal_statuses as status_repo
from app.schemas.common import PaginatedResponse
from app.schemas.deal_status import DealStatusCreate, DealStatusRead, DealStatusUpdate
from app.services.permission_service import require_permission

router = APIRouter()


@router.post("/seed", response_model=list[DealStatusRead])
async def seed_deal_statuses(db: DbSession, current_user: CurrentUser) -> list[DealStatusRead]:
    require_permission(current_user, PermissionAction.MANAGE, PermissionResource.CRM)
    statuses = await status_repo.seed_default_deal_statuses(db)
    await db.commit()
    return [DealStatusRead.model_validate(status) for status in statuses]


@router.get("", response_model=PaginatedResponse[DealStatusRead])
async def list_deal_statuses(
    db: DbSession,
    current_user: CurrentUser,
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
) -> PaginatedResponse[DealStatusRead]:
    require_permission(current_user, PermissionAction.READ, PermissionResource.CRM)
    statuses = await status_repo.list_deal_statuses(db, limit=limit, offset=offset)
    total = await status_repo.count_deal_statuses(db)
    return PaginatedResponse(
        items=[DealStatusRead.model_validate(status) for status in statuses],
        total=total,
        limit=limit,
        offset=offset,
    )


@router.post("", response_model=DealStatusRead)
async def create_deal_status(
    payload: DealStatusCreate,
    db: DbSession,
    current_user: CurrentUser,
) -> DealStatusRead:
    require_permission(current_user, PermissionAction.CREATE, PermissionResource.CRM)
    existing = await status_repo.get_deal_status_by_name(db, payload.name)
    if existing is not None:
        raise ConflictError("Deal status name already exists")
    status = await status_repo.create_deal_status(
        db,
        **payload.model_dump(),
        is_system=False,
    )
    await db.commit()
    await db.refresh(status)
    return DealStatusRead.model_validate(status)


@router.patch("/{status_id}", response_model=DealStatusRead)
async def update_deal_status(
    status_id: uuid.UUID,
    payload: DealStatusUpdate,
    db: DbSession,
    current_user: CurrentUser,
) -> DealStatusRead:
    require_permission(current_user, PermissionAction.UPDATE, PermissionResource.CRM)
    status = await status_repo.get_deal_status(db, status_id)
    if status is None:
        raise NotFoundError("Deal status not found")
    values = payload.model_dump(exclude_unset=True)
    if "name" in values:
        existing = await status_repo.get_deal_status_by_name(db, values["name"])
        if existing is not None and existing.id != status.id:
            raise ConflictError("Deal status name already exists")
    for field, value in values.items():
        setattr(status, field, value)
    await db.commit()
    await db.refresh(status)
    return DealStatusRead.model_validate(status)


@router.delete("/{status_id}", response_model=dict[str, str])
async def delete_deal_status(
    status_id: uuid.UUID,
    db: DbSession,
    current_user: CurrentUser,
) -> dict[str, str]:
    require_permission(current_user, PermissionAction.ARCHIVE, PermissionResource.CRM)
    status = await status_repo.get_deal_status(db, status_id)
    if status is None:
        raise NotFoundError("Deal status not found")
    if status.is_system:
        raise ValidationError("System deal statuses cannot be deleted")
    await db.delete(status)
    await db.commit()
    return {"status": "deleted"}
