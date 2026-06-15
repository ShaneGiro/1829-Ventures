"""Company CRM routes."""

from __future__ import annotations

import uuid
from datetime import datetime

from fastapi import APIRouter, HTTPException, Query

from app.core.dependencies import CurrentUser, DbSession
from app.core.permissions import PermissionAction, PermissionResource
from app.integrations.dealroom_columns import TEMPLATE_COLUMNS
from app.repositories.companies import CompanyFilters, DealroomColumnFilter
from app.schemas.common import PaginatedResponse
from app.schemas.company import CompanyCompleteness, CompanyCreate, CompanyRead, CompanyUpdate
from app.services import company_service
from app.services.permission_service import require_permission

router = APIRouter()


@router.get("", response_model=PaginatedResponse[CompanyRead])
async def list_companies(  # noqa: PLR0913 - filter surface intentionally wide
    db: DbSession,
    current_user: CurrentUser,
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    q: str | None = Query(default=None, description="Search by name, domain, website, description"),
    sector: list[str] | None = Query(default=None),
    relationship_status: list[str] | None = Query(default=None),
    stage: list[str] | None = Query(default=None),
    country: list[str] | None = Query(default=None),
    state: list[str] | None = Query(default=None),
    city: list[str] | None = Query(default=None),
    source_system: list[str] | None = Query(default=None),
    has_rit_nexus: bool | None = Query(default=None),
    imported_unreviewed: bool | None = Query(default=None),
    has_website: bool | None = Query(default=None),
    min_completeness: float | None = Query(default=None, ge=0, le=100),
    max_completeness: float | None = Query(default=None, ge=0, le=100),
    created_after: datetime | None = Query(default=None),
    created_before: datetime | None = Query(default=None),
    updated_after: datetime | None = Query(default=None),
    updated_before: datetime | None = Query(default=None),
    dealroom_column: str | None = Query(
        default=None, description="Canonical Dealroom CSV column to filter."
    ),
    dealroom_contains: str | None = Query(
        default=None, description="Case-insensitive substring in the selected Dealroom column."
    ),
    include_archived: bool = False,
) -> PaginatedResponse[CompanyRead]:
    require_permission(current_user, PermissionAction.READ, PermissionResource.CRM)
    dealroom_column_filters: tuple[DealroomColumnFilter, ...] = ()
    if dealroom_column or dealroom_contains:
        if not dealroom_column or not dealroom_contains:
            raise HTTPException(
                status_code=422,
                detail="dealroom_column and dealroom_contains must be provided together.",
            )
        if dealroom_column not in TEMPLATE_COLUMNS:
            raise HTTPException(status_code=422, detail="Unknown Dealroom column.")
        dealroom_column_filters = (
            DealroomColumnFilter(column=dealroom_column, contains=dealroom_contains),
        )
    filters = CompanyFilters(
        include_archived=include_archived,
        sectors=tuple(sector or ()),
        relationship_statuses=tuple(relationship_status or ()),
        stages=tuple(stage or ()),
        countries=tuple(country or ()),
        states=tuple(state or ()),
        cities=tuple(city or ()),
        source_systems=tuple(source_system or ()),
        has_rit_nexus=has_rit_nexus,
        imported_unreviewed=imported_unreviewed,
        has_website=has_website,
        min_completeness=min_completeness,
        max_completeness=max_completeness,
        created_after=created_after,
        created_before=created_before,
        updated_after=updated_after,
        updated_before=updated_before,
        dealroom_column_filters=dealroom_column_filters,
    )
    companies, total = await company_service.list_companies(
        db, query=q, filters=filters, limit=limit, offset=offset
    )
    return PaginatedResponse(
        items=[CompanyRead.model_validate(company) for company in companies],
        total=total,
        limit=limit,
        offset=offset,
    )


@router.get("/dealroom-columns", response_model=list[str])
async def list_dealroom_columns(current_user: CurrentUser) -> list[str]:
    require_permission(current_user, PermissionAction.READ, PermissionResource.CRM)
    return list(TEMPLATE_COLUMNS)


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
