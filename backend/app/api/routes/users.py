"""User routes."""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Query

from app.core.dependencies import CurrentUser, DbSession
from app.core.exceptions import NotFoundError
from app.core.permissions import PermissionAction, PermissionResource
from app.repositories import users as user_repo
from app.schemas.common import PaginatedResponse
from app.schemas.user import UserRead
from app.services.permission_service import require_permission

router = APIRouter()


@router.get("", response_model=PaginatedResponse[UserRead])
async def list_users(
    db: DbSession,
    current_user: CurrentUser,
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
) -> PaginatedResponse[UserRead]:
    require_permission(current_user, PermissionAction.READ, PermissionResource.USER)
    users = await user_repo.list_users(db, limit=limit, offset=offset)
    total = await user_repo.count_human_users(db)
    return PaginatedResponse(
        items=[UserRead.model_validate(user) for user in users],
        total=total,
        limit=limit,
        offset=offset,
    )


@router.get("/me", response_model=UserRead)
async def current_user(current_user: CurrentUser) -> UserRead:
    return UserRead.model_validate(current_user)


@router.get("/{user_id}", response_model=UserRead)
async def get_user(user_id: uuid.UUID, db: DbSession, current_user: CurrentUser) -> UserRead:
    require_permission(current_user, PermissionAction.READ, PermissionResource.USER)
    user = await user_repo.get_user_by_id(db, user_id)
    if user is None or user.is_agent:
        raise NotFoundError("User not found")
    return UserRead.model_validate(user)
