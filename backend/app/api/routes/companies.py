"""Company CRM routes."""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Query

from app.core.dependencies import CurrentUser, DbSession
from app.core.permissions import PermissionAction, PermissionResource
from app.repositories import companies as company_repo
from app.schemas.common import PaginatedResponse
from app.schemas.company import CompanyCompleteness, CompanyCreate, CompanyRead, CompanyUpdate
from app.services import company_service
from app.services.permission_service import require_permission

router = APIRouter()


@router.get("", response_model=PaginatedResponse[CompanyRead])
async def list_companies(
    db: DbSession,
    current_user: CurrentUser,
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    include_archived: bool = False,
) -> PaginatedResponse[CompanyRead]:
    require_permission(current_user, PermissionAction.READ, PermissionResource.CRM)
    companies = await company_repo.list_companies(
        db, limit=limit, offset=offset, include_archived=include_archived
    )
    total = await company_repo.count_companies(db, include_archived=include_archived)
    return PaginatedResponse(
        items=[CompanyRead.model_validate(company) for company in companies],
        total=total,
        limit=limit,
        offset=offset,
    )


@router.post("", response_model=CompanyRead, status_code=201)
async def create_company(
    payload: CompanyCreate, db: DbSession, current_user: CurrentUser
) -> CompanyRead:
    require_permission(current_user, PermissionAction.CREATE, PermissionResource.CRM)
    company = await company_service.create_company(db, payload, current_user)
    return CompanyRead.model_validate(company)


@router.get("/{company_id}", response_model=CompanyRead)
async def get_company(
    company_id: uuid.UUID,
    db: DbSession,
    current_user: CurrentUser,
    include_archived: bool = False,
) -> CompanyRead:
    require_permission(current_user, PermissionAction.READ, PermissionResource.CRM)
    company = await company_service.get_company(db, company_id, include_archived=include_archived)
    return CompanyRead.model_validate(company)


@router.patch("/{company_id}", response_model=CompanyRead)
async def update_company(
    company_id: uuid.UUID,
    payload: CompanyUpdate,
    db: DbSession,
    current_user: CurrentUser,
) -> CompanyRead:
    require_permission(current_user, PermissionAction.UPDATE, PermissionResource.CRM)
    company = await company_service.update_company(db, company_id, payload, current_user)
    return CompanyRead.model_validate(company)


@router.post("/{company_id}/archive", response_model=CompanyRead)
async def archive_company(
    company_id: uuid.UUID, db: DbSession, current_user: CurrentUser
) -> CompanyRead:
    require_permission(current_user, PermissionAction.ARCHIVE, PermissionResource.CRM)
    company = await company_service.archive_company(db, company_id, current_user)
    return CompanyRead.model_validate(company)


@router.get("/{company_id}/completeness", response_model=CompanyCompleteness)
async def get_company_completeness(
    company_id: uuid.UUID, db: DbSession, current_user: CurrentUser
) -> CompanyCompleteness:
    require_permission(current_user, PermissionAction.READ, PermissionResource.CRM)
    return await company_service.get_company_completeness(db, company_id)
