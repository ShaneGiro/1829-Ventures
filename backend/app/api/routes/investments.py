"""Fund and investment routes."""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Query
from sqlalchemy import select

from app.core.dependencies import CurrentUser, DbSession
from app.core.permissions import PermissionAction, PermissionResource
from app.models.company import Company
from app.models.fund import Fund
from app.models.investment import Investment
from app.repositories import investments as investment_repo
from app.schemas.common import PaginatedResponse
from app.schemas.fund import FundCreate, FundRead, FundUpdate
from app.schemas.investment import InvestmentCreate, InvestmentRead, InvestmentUpdate
from app.services import investment_service
from app.services.permission_service import require_permission

router = APIRouter()
funds_router = APIRouter()


@funds_router.get("", response_model=PaginatedResponse[FundRead])
async def list_funds(
    db: DbSession,
    current_user: CurrentUser,
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
) -> PaginatedResponse[FundRead]:
    require_permission(current_user, PermissionAction.READ, PermissionResource.CRM)
    funds = await investment_repo.list_funds(db, limit=limit, offset=offset)
    total = await investment_repo.count_funds(db)
    return PaginatedResponse(
        items=[FundRead.model_validate(fund) for fund in funds],
        total=total,
        limit=limit,
        offset=offset,
    )


@funds_router.post("", response_model=FundRead, status_code=201)
async def create_fund(payload: FundCreate, db: DbSession, current_user: CurrentUser) -> FundRead:
    require_permission(current_user, PermissionAction.CREATE, PermissionResource.CRM)
    fund = await investment_service.create_fund(db, payload, current_user)
    return FundRead.model_validate(fund)


@funds_router.get("/{fund_id}", response_model=FundRead)
async def get_fund(fund_id: uuid.UUID, db: DbSession, current_user: CurrentUser) -> FundRead:
    require_permission(current_user, PermissionAction.READ, PermissionResource.CRM)
    fund = await investment_service.get_fund(db, fund_id)
    return FundRead.model_validate(fund)


@funds_router.patch("/{fund_id}", response_model=FundRead)
async def update_fund(
    fund_id: uuid.UUID, payload: FundUpdate, db: DbSession, current_user: CurrentUser
) -> FundRead:
    require_permission(current_user, PermissionAction.UPDATE, PermissionResource.CRM)
    fund = await investment_service.update_fund(db, fund_id, payload, current_user)
    return FundRead.model_validate(fund)


@router.get("", response_model=PaginatedResponse[InvestmentRead])
async def list_investments(
    db: DbSession,
    current_user: CurrentUser,
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    include_archived: bool = False,
) -> PaginatedResponse[InvestmentRead]:
    require_permission(current_user, PermissionAction.READ, PermissionResource.CRM)
    investments = await investment_repo.list_investments(
        db, limit=limit, offset=offset, include_archived=include_archived
    )
    total = await investment_repo.count_investments(db, include_archived=include_archived)
    labels = await _investment_labels(db, investments)
    return PaginatedResponse(
        items=[
            InvestmentRead.model_validate(investment).model_copy(
                update=labels.get(investment.id, {})
            )
            for investment in investments
        ],
        total=total,
        limit=limit,
        offset=offset,
    )


@router.post("", response_model=InvestmentRead, status_code=201)
async def create_investment(
    payload: InvestmentCreate, db: DbSession, current_user: CurrentUser
) -> InvestmentRead:
    require_permission(current_user, PermissionAction.CREATE, PermissionResource.CRM)
    investment = await investment_service.create_investment(db, payload, current_user)
    return InvestmentRead.model_validate(investment)


@router.get("/{investment_id}", response_model=InvestmentRead)
async def get_investment(
    investment_id: uuid.UUID,
    db: DbSession,
    current_user: CurrentUser,
    include_archived: bool = False,
) -> InvestmentRead:
    require_permission(current_user, PermissionAction.READ, PermissionResource.CRM)
    investment = await investment_service.get_investment(
        db, investment_id, include_archived=include_archived
    )
    labels = await _investment_labels(db, [investment])
    return InvestmentRead.model_validate(investment).model_copy(
        update=labels.get(investment.id, {})
    )


@router.patch("/{investment_id}", response_model=InvestmentRead)
async def update_investment(
    investment_id: uuid.UUID,
    payload: InvestmentUpdate,
    db: DbSession,
    current_user: CurrentUser,
) -> InvestmentRead:
    require_permission(current_user, PermissionAction.UPDATE, PermissionResource.CRM)
    investment = await investment_service.update_investment(
        db, investment_id, payload, current_user
    )
    return InvestmentRead.model_validate(investment)


@router.post("/{investment_id}/archive", response_model=InvestmentRead)
async def archive_investment(
    investment_id: uuid.UUID, db: DbSession, current_user: CurrentUser
) -> InvestmentRead:
    require_permission(current_user, PermissionAction.ARCHIVE, PermissionResource.CRM)
    investment = await investment_service.archive_investment(db, investment_id, current_user)
    return InvestmentRead.model_validate(investment)


async def _investment_labels(
    db: DbSession, investments: list[Investment]
) -> dict[uuid.UUID, dict[str, str | None]]:
    if not investments:
        return {}
    ids = [investment.id for investment in investments]
    rows = await db.execute(
        select(
            Investment.id,
            Company.name.label("company_name"),
            Fund.name.label("fund_name"),
        )
        .join(Company, Company.id == Investment.company_id)
        .join(Fund, Fund.id == Investment.fund_id)
        .where(Investment.id.in_(ids))
    )
    return {
        investment_id: {
            "company_name": company_name,
            "fund_name": fund_name,
        }
        for investment_id, company_name, fund_name in rows
    }
