"""Task routes."""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Query

from app.core.constants import TaskStatus
from app.core.dependencies import CurrentUser, DbSession
from app.core.permissions import PermissionAction, PermissionResource
from app.repositories import tasks as task_repo
from app.schemas.common import PaginatedResponse
from app.schemas.task import TaskComplete, TaskCreate, TaskRead, TaskReassign, TaskUpdate
from app.services import task_service
from app.services.permission_service import require_permission

router = APIRouter()


@router.get("", response_model=PaginatedResponse[TaskRead])
async def list_tasks(
    db: DbSession,
    current_user: CurrentUser,
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    owner_id: uuid.UUID | None = None,
    status: TaskStatus | None = None,
    company_id: uuid.UUID | None = None,
    deal_id: uuid.UUID | None = None,
    include_unassigned: bool = False,
    include_archived: bool = False,
) -> PaginatedResponse[TaskRead]:
    require_permission(current_user, PermissionAction.READ, PermissionResource.CRM)
    tasks = await task_repo.list_tasks(
        db,
        limit=limit,
        offset=offset,
        owner_id=owner_id,
        status=status,
        company_id=company_id,
        deal_id=deal_id,
        include_unassigned=include_unassigned,
        include_archived=include_archived,
    )
    total = await task_repo.count_tasks(
        db,
        owner_id=owner_id,
        status=status,
        company_id=company_id,
        deal_id=deal_id,
        include_unassigned=include_unassigned,
        include_archived=include_archived,
    )
    return PaginatedResponse(
        items=[TaskRead.model_validate(task) for task in tasks],
        total=total,
        limit=limit,
        offset=offset,
    )


@router.get("/shared-queue", response_model=PaginatedResponse[TaskRead])
async def list_shared_queue(
    db: DbSession,
    current_user: CurrentUser,
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
) -> PaginatedResponse[TaskRead]:
    require_permission(current_user, PermissionAction.READ, PermissionResource.CRM)
    tasks = await task_repo.list_tasks(
        db,
        limit=limit,
        offset=offset,
        include_unassigned=True,
        status=TaskStatus.OPEN,
    )
    total = await task_repo.count_tasks(
        db,
        include_unassigned=True,
        status=TaskStatus.OPEN,
    )
    return PaginatedResponse(
        items=[TaskRead.model_validate(task) for task in tasks],
        total=total,
        limit=limit,
        offset=offset,
    )


@router.post("", response_model=TaskRead, status_code=201)
async def create_task(payload: TaskCreate, db: DbSession, current_user: CurrentUser) -> TaskRead:
    require_permission(current_user, PermissionAction.CREATE, PermissionResource.CRM)
    task = await task_service.create_task(db, payload, current_user)
    return TaskRead.model_validate(task)


@router.get("/{task_id}", response_model=TaskRead)
async def get_task(
    task_id: uuid.UUID,
    db: DbSession,
    current_user: CurrentUser,
    include_archived: bool = False,
) -> TaskRead:
    require_permission(current_user, PermissionAction.READ, PermissionResource.CRM)
    task = await task_service.get_task(db, task_id, include_archived=include_archived)
    return TaskRead.model_validate(task)


@router.patch("/{task_id}", response_model=TaskRead)
async def update_task(
    task_id: uuid.UUID,
    payload: TaskUpdate,
    db: DbSession,
    current_user: CurrentUser,
) -> TaskRead:
    require_permission(current_user, PermissionAction.UPDATE, PermissionResource.CRM)
    task = await task_service.update_task(db, task_id, payload, current_user)
    return TaskRead.model_validate(task)


@router.post("/{task_id}/reassign", response_model=TaskRead)
async def reassign_task(
    task_id: uuid.UUID,
    payload: TaskReassign,
    db: DbSession,
    current_user: CurrentUser,
) -> TaskRead:
    require_permission(current_user, PermissionAction.UPDATE, PermissionResource.CRM)
    task = await task_service.reassign_task(db, task_id, payload.owner_id, current_user)
    return TaskRead.model_validate(task)


@router.post("/{task_id}/complete", response_model=TaskRead)
async def complete_task(
    task_id: uuid.UUID,
    payload: TaskComplete,
    db: DbSession,
    current_user: CurrentUser,
) -> TaskRead:
    require_permission(current_user, PermissionAction.UPDATE, PermissionResource.CRM)
    task = await task_service.complete_task(db, task_id, payload, current_user)
    return TaskRead.model_validate(task)


@router.post("/{task_id}/archive", response_model=TaskRead)
async def archive_task(task_id: uuid.UUID, db: DbSession, current_user: CurrentUser) -> TaskRead:
    require_permission(current_user, PermissionAction.ARCHIVE, PermissionResource.CRM)
    task = await task_service.archive_task(db, task_id, current_user)
    return TaskRead.model_validate(task)

