"""Derived Outreach Candidates queue."""

from __future__ import annotations

from fastapi import APIRouter, Query

from app.core.dependencies import CurrentUser, DbSession
from app.core.permissions import PermissionAction, PermissionResource
from app.schemas.common import PaginatedResponse
from app.schemas.outreach_candidate import OutreachCandidateRead
from app.services import outreach_candidate_service
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
