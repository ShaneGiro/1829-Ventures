"""Company CRM routes."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Literal

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from app.core.dependencies import CurrentUser, DbSession
from app.core.permissions import PermissionAction, PermissionResource
from app.integrations.dealroom_columns import TEMPLATE_COLUMNS
from app.repositories import companies as company_repo
from app.repositories.companies import CompanyFilters, DealroomColumnFilter
from app.schemas.common import PaginatedResponse
from app.schemas.company import (
    CompanyCompleteness,
    CompanyCreate,
    CompanyDealroomData,
    CompanyRead,
    CompanyUpdate,
)
from app.schemas.rubric import RubricRead, RubricUpdate
from app.services import company_service, diligence_service
from app.services.permission_service import require_permission

router = APIRouter()

DealroomColumnKind = Literal["text", "number", "date", "boolean"]


class DealroomColumnOption(BaseModel):
    name: str
    kind: DealroomColumnKind


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
    dealroom_filter: list[str] | None = Query(
        default=None,
        description=(
            "Repeated typed Dealroom filters encoded as "
            "column<TAB>operator<TAB>value<TAB>value_to."
        ),
    ),
    dealroom_column: str | None = Query(
        default=None, description="Legacy single Dealroom CSV column filter."
    ),
    dealroom_contains: str | None = Query(
        default=None, description="Legacy case-insensitive substring Dealroom filter."
    ),
    include_archived: bool = False,
) -> PaginatedResponse[CompanyRead]:
    require_permission(current_user, PermissionAction.READ, PermissionResource.CRM)
    dealroom_column_filters = _parse_dealroom_filters(dealroom_filter or [])
    if dealroom_column or dealroom_contains:
        if not dealroom_column or not dealroom_contains:
            raise HTTPException(
                status_code=422,
                detail="dealroom_column and dealroom_contains must be provided together.",
            )
        if dealroom_column not in TEMPLATE_COLUMNS:
            raise HTTPException(status_code=422, detail="Unknown Dealroom column.")
        dealroom_column_filters = (
            *dealroom_column_filters,
            DealroomColumnFilter(
                column=dealroom_column,
                operator="contains",
                value=dealroom_contains,
            ),
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


@router.get("/dealroom-columns", response_model=list[DealroomColumnOption])
async def list_dealroom_columns(current_user: CurrentUser) -> list[DealroomColumnOption]:
    require_permission(current_user, PermissionAction.READ, PermissionResource.CRM)
    return [
        DealroomColumnOption(name=column, kind=_dealroom_column_kind(column))
        for column in TEMPLATE_COLUMNS
    ]


def _parse_dealroom_filters(encoded_filters: list[str]) -> tuple[DealroomColumnFilter, ...]:
    filters: list[DealroomColumnFilter] = []
    for encoded in encoded_filters:
        parts = [*encoded.split("\t"), "", "", ""]
        column, operator, value, value_to = parts[:4]
        if column not in TEMPLATE_COLUMNS:
            raise HTTPException(status_code=422, detail=f"Unknown Dealroom column: {column}")
        _validate_dealroom_operator(column, operator, value, value_to)
        filters.append(
            DealroomColumnFilter(
                column=column,
                operator=operator,
                value=value or None,
                value_to=value_to or None,
            )
        )
    return tuple(filters)


def _validate_dealroom_operator(column: str, operator: str, value: str, value_to: str) -> None:
    kind = _dealroom_column_kind(column)
    allowed = {
        "text": {"contains", "equals", "present", "blank"},
        "number": {"number_gte", "number_lte", "number_between", "present", "blank"},
        "date": {"date_gte", "date_lte", "date_between", "present", "blank"},
        "boolean": {"yes_no", "present", "blank"},
    }[kind]
    if operator not in allowed:
        raise HTTPException(status_code=422, detail=f"Unsupported operator for {column}.")
    if operator.startswith("number"):
        _validate_float(value, column)
        if operator == "number_between":
            _validate_float(value_to, column)
    if operator.startswith("date"):
        _validate_date(value, column)
        if operator == "date_between":
            _validate_date(value_to, column)
    if operator == "yes_no" and value not in {"yes", "no"}:
        raise HTTPException(status_code=422, detail=f"{column} must be yes or no.")


def _validate_float(value: str, column: str) -> None:
    try:
        float(value)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=f"{column} requires a numeric value.") from exc


def _validate_date(value: str, column: str) -> None:
    try:
        datetime.strptime(value, "%Y-%m-%d")
    except ValueError as exc:
        raise HTTPException(
            status_code=422,
            detail=f"{column} requires a YYYY-MM-DD date.",
        ) from exc


def _dealroom_column_kind(column: str) -> DealroomColumnKind:
    lowered = column.lower()
    if "(yes/no)" in lowered or lowered.startswith("is ") or " is " in lowered:
        return "boolean"
    if "date" in lowered or "dates" in lowered:
        return "date"
    number_markers = (
        "amount",
        "funding",
        "valuation",
        "traffic",
        "employees",
        "growth",
        "profit",
        "margin",
        "ebitda",
        "revenue",
        "rank",
        "number",
        "year",
        "month",
        "downloads",
        "strength",
        "rating",
        "completeness",
        "timing",
        "latitude",
        "longitude",
        "ev/",
    )
    if any(marker in lowered for marker in number_markers):
        return "number"
    return "text"


@router.post("", response_model=CompanyRead, status_code=201)
async def create_company(
    payload: CompanyCreate, db: DbSession, current_user: CurrentUser
) -> CompanyRead:
    require_permission(current_user, PermissionAction.CREATE, PermissionResource.CRM)
    company = await company_service.create_company(db, payload, current_user)
    return CompanyRead.model_validate(company)


@router.get("/{company_id}/dealroom-data", response_model=CompanyDealroomData)
async def get_company_dealroom_data(
    company_id: uuid.UUID,
    db: DbSession,
    current_user: CurrentUser,
) -> CompanyDealroomData:
    require_permission(current_user, PermissionAction.READ, PermissionResource.CRM)
    company = await company_service.get_company(db, company_id)
    row = await company_repo.get_latest_dealroom_import_row(db, company_id)
    if row is None:
        return CompanyDealroomData(company_id=str(company.id))
    return CompanyDealroomData(
        company_id=str(company.id),
        import_row_id=str(row.id),
        batch_id=str(row.batch_id),
        row_number=row.row_number,
        status=row.status.value if hasattr(row.status, "value") else str(row.status),
        raw=dict(row.raw_data.get("dealroom") or {}),
        normalized=dict(row.raw_data.get("normalized") or {}),
    )


@router.get("/{company_id}/rubric", response_model=RubricRead)
async def get_company_rubric(
    company_id: uuid.UUID,
    db: DbSession,
    current_user: CurrentUser,
) -> RubricRead:
    require_permission(current_user, PermissionAction.READ, PermissionResource.CRM)
    return RubricRead.model_validate(await diligence_service.get_company_rubric(db, company_id))


@router.patch("/{company_id}/rubric", response_model=RubricRead)
async def update_company_rubric(
    company_id: uuid.UUID,
    payload: RubricUpdate,
    db: DbSession,
    current_user: CurrentUser,
) -> RubricRead:
    require_permission(current_user, PermissionAction.UPDATE, PermissionResource.CRM)
    rubric = await diligence_service.update_company_rubric(
        db,
        company_id=company_id,
        values=payload.model_dump(exclude_unset=True),
    )
    return RubricRead.model_validate(rubric)


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
