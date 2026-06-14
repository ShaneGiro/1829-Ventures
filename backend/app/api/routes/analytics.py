"""Analytics routes."""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Query

from app.core.dependencies import CurrentUser, DbSession
from app.core.permissions import PermissionAction, PermissionResource
from app.schemas.analytics import (
    AgentActivitySummary,
    CountByKey,
    InteractionCadence,
    PipelineSummary,
    PortfolioSummary,
    ThesisFitSummary,
)
from app.services import analytics_service
from app.services.permission_service import require_permission

router = APIRouter()


@router.get("/pipeline", response_model=PipelineSummary)
async def pipeline_summary(
    db: DbSession,
    current_user: CurrentUser,
    include_unreviewed: bool = False,
) -> PipelineSummary:
    require_permission(current_user, PermissionAction.READ, PermissionResource.CRM)
    return await analytics_service.get_pipeline_summary(db, include_unreviewed=include_unreviewed)


@router.get("/portfolio", response_model=PortfolioSummary)
async def portfolio_summary(
    db: DbSession,
    current_user: CurrentUser,
    fund_id: uuid.UUID | None = None,
) -> PortfolioSummary:
    require_permission(current_user, PermissionAction.READ, PermissionResource.CRM)
    return await analytics_service.get_portfolio_summary(db, fund_id=fund_id)


@router.get("/sources", response_model=list[CountByKey])
async def source_summary(
    db: DbSession,
    current_user: CurrentUser,
    include_unreviewed: bool = False,
) -> list[CountByKey]:
    require_permission(current_user, PermissionAction.READ, PermissionResource.CRM)
    return await analytics_service.get_source_summary(db, include_unreviewed=include_unreviewed)


@router.get("/sectors", response_model=list[CountByKey])
async def sector_summary(
    db: DbSession,
    current_user: CurrentUser,
    include_unreviewed: bool = False,
) -> list[CountByKey]:
    require_permission(current_user, PermissionAction.READ, PermissionResource.CRM)
    return await analytics_service.get_sector_summary(db, include_unreviewed=include_unreviewed)


@router.get("/interactions/cadence", response_model=InteractionCadence)
async def interaction_cadence(
    db: DbSession,
    current_user: CurrentUser,
    days: int = Query(default=30, ge=1, le=365),
    stale_days: int = Query(default=30, ge=1, le=365),
) -> InteractionCadence:
    require_permission(current_user, PermissionAction.READ, PermissionResource.CRM)
    return await analytics_service.get_interaction_cadence(
        db,
        days=days,
        stale_days=stale_days,
    )


@router.get("/thesis-fit", response_model=ThesisFitSummary)
async def thesis_fit_summary(db: DbSession, current_user: CurrentUser) -> ThesisFitSummary:
    require_permission(current_user, PermissionAction.READ, PermissionResource.CRM)
    return await analytics_service.get_thesis_fit_summary(db)


@router.get("/agent-activity", response_model=AgentActivitySummary)
async def agent_activity_summary(db: DbSession, current_user: CurrentUser) -> AgentActivitySummary:
    require_permission(current_user, PermissionAction.READ, PermissionResource.CRM)
    return await analytics_service.get_agent_activity_summary(db)
