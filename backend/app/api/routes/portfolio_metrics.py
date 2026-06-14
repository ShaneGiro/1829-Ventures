"""Portfolio metric routes."""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Query

from app.core.dependencies import CurrentUser, DbSession
from app.core.permissions import PermissionAction, PermissionResource
from app.repositories import investments as investment_repo
from app.schemas.common import PaginatedResponse
from app.schemas.portfolio_metric import (
    PortfolioMetricCreate,
    PortfolioMetricRead,
    PortfolioMetricUpdate,
)
from app.services import investment_service
from app.services.permission_service import require_permission

router = APIRouter()


@router.get("", response_model=PaginatedResponse[PortfolioMetricRead])
async def list_portfolio_metrics(
    db: DbSession,
    current_user: CurrentUser,
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
) -> PaginatedResponse[PortfolioMetricRead]:
    require_permission(current_user, PermissionAction.READ, PermissionResource.CRM)
    metrics = await investment_repo.list_portfolio_metrics(db, limit=limit, offset=offset)
    total = await investment_repo.count_portfolio_metrics(db)
    return PaginatedResponse(
        items=[PortfolioMetricRead.model_validate(metric) for metric in metrics],
        total=total,
        limit=limit,
        offset=offset,
    )


@router.post("", response_model=PortfolioMetricRead, status_code=201)
async def create_portfolio_metric(
    payload: PortfolioMetricCreate, db: DbSession, current_user: CurrentUser
) -> PortfolioMetricRead:
    require_permission(current_user, PermissionAction.CREATE, PermissionResource.CRM)
    metric = await investment_service.create_portfolio_metric(db, payload, current_user)
    return PortfolioMetricRead.model_validate(metric)


@router.get("/{metric_id}", response_model=PortfolioMetricRead)
async def get_portfolio_metric(
    metric_id: uuid.UUID, db: DbSession, current_user: CurrentUser
) -> PortfolioMetricRead:
    require_permission(current_user, PermissionAction.READ, PermissionResource.CRM)
    metric = await investment_service.get_portfolio_metric(db, metric_id)
    return PortfolioMetricRead.model_validate(metric)


@router.patch("/{metric_id}", response_model=PortfolioMetricRead)
async def update_portfolio_metric(
    metric_id: uuid.UUID,
    payload: PortfolioMetricUpdate,
    db: DbSession,
    current_user: CurrentUser,
) -> PortfolioMetricRead:
    require_permission(current_user, PermissionAction.UPDATE, PermissionResource.CRM)
    metric = await investment_service.update_portfolio_metric(db, metric_id, payload, current_user)
    return PortfolioMetricRead.model_validate(metric)
