"""Fund, investment, and portfolio metric services."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.audit import actor_from_user
from app.core.exceptions import NotFoundError, ValidationError
from app.models.fund import Fund
from app.models.investment import Investment
from app.models.portfolio_metric import PortfolioMetric
from app.models.user import User
from app.repositories import companies as company_repo
from app.repositories import investments as investment_repo
from app.schemas.fund import FundCreate, FundUpdate
from app.schemas.investment import InvestmentCreate, InvestmentUpdate
from app.schemas.portfolio_metric import PortfolioMetricCreate, PortfolioMetricUpdate
from app.services import audit_service


async def get_fund(session: AsyncSession, fund_id: uuid.UUID) -> Fund:
    fund = await investment_repo.get_fund(session, fund_id)
    if fund is None:
        raise NotFoundError("Fund not found")
    return fund


async def create_fund(session: AsyncSession, payload: FundCreate, actor: User) -> Fund:
    fund = Fund(**payload.model_dump(exclude_none=True))
    await investment_repo.create_fund(session, fund)
    await audit_service.record_create(session, actor=actor_from_user(actor), entity=fund)
    await session.commit()
    await session.refresh(fund)
    return fund


async def update_fund(
    session: AsyncSession, fund_id: uuid.UUID, payload: FundUpdate, actor: User
) -> Fund:
    fund = await get_fund(session, fund_id)
    updates = payload.model_dump(exclude_unset=True)
    required_fields = {"name", "status"}
    null_required = sorted(field for field in required_fields if updates.get(field) is None)
    if null_required:
        raise ValidationError(f"Required fund fields cannot be null: {', '.join(null_required)}")
    changes: dict[str, tuple[Any, Any]] = {}
    for field, value in updates.items():
        old_value = getattr(fund, field)
        if old_value != value:
            changes[field] = (old_value, value)
            setattr(fund, field, value)
    if changes:
        await audit_service.record_update(
            session, actor=actor_from_user(actor), entity=fund, changes=changes
        )
    await session.commit()
    await session.refresh(fund)
    return fund


async def get_investment(
    session: AsyncSession, investment_id: uuid.UUID, *, include_archived: bool = False
) -> Investment:
    investment = await investment_repo.get_investment(
        session, investment_id, include_archived=include_archived
    )
    if investment is None:
        raise NotFoundError("Investment not found")
    return investment


async def create_investment(
    session: AsyncSession, payload: InvestmentCreate, actor: User
) -> Investment:
    await get_fund(session, payload.fund_id)
    if await company_repo.get_company(session, payload.company_id) is None:
        raise NotFoundError("Company not found")
    investment = Investment(**payload.model_dump(exclude_none=True))
    await investment_repo.create_investment(session, investment)
    await audit_service.record_create(session, actor=actor_from_user(actor), entity=investment)
    await session.commit()
    await session.refresh(investment)
    return investment


async def update_investment(
    session: AsyncSession,
    investment_id: uuid.UUID,
    payload: InvestmentUpdate,
    actor: User,
) -> Investment:
    investment = await get_investment(session, investment_id)
    updates = payload.model_dump(exclude_unset=True)
    if "fund_id" in updates and updates["fund_id"] is None:
        raise ValidationError("fund_id cannot be null")
    if "fund_id" in updates:
        await get_fund(session, updates["fund_id"])
    changes: dict[str, tuple[Any, Any]] = {}
    for field, value in updates.items():
        old_value = getattr(investment, field)
        if old_value != value:
            changes[field] = (old_value, value)
            setattr(investment, field, value)
    if changes:
        await audit_service.record_update(
            session, actor=actor_from_user(actor), entity=investment, changes=changes
        )
    await session.commit()
    await session.refresh(investment)
    return investment


async def archive_investment(
    session: AsyncSession, investment_id: uuid.UUID, actor: User
) -> Investment:
    investment = await get_investment(session, investment_id)
    old_snapshot = audit_service.snapshot_model(investment)
    investment.archived_at = datetime.now(UTC)
    await audit_service.record_archive(
        session,
        actor=actor_from_user(actor),
        entity=investment,
        old_snapshot=old_snapshot,
    )
    await session.commit()
    await session.refresh(investment)
    return investment


async def get_portfolio_metric(session: AsyncSession, metric_id: uuid.UUID) -> PortfolioMetric:
    metric = await investment_repo.get_portfolio_metric(session, metric_id)
    if metric is None:
        raise NotFoundError("Portfolio metric not found")
    return metric


async def create_portfolio_metric(
    session: AsyncSession, payload: PortfolioMetricCreate, actor: User
) -> PortfolioMetric:
    if await company_repo.get_company(session, payload.company_id) is None:
        raise NotFoundError("Company not found")
    if payload.investment_id is not None:
        await get_investment(session, payload.investment_id)
    metric = PortfolioMetric(**payload.model_dump(exclude_none=True))
    await investment_repo.create_portfolio_metric(session, metric)
    await audit_service.record_create(session, actor=actor_from_user(actor), entity=metric)
    await session.commit()
    await session.refresh(metric)
    return metric


async def update_portfolio_metric(
    session: AsyncSession,
    metric_id: uuid.UUID,
    payload: PortfolioMetricUpdate,
    actor: User,
) -> PortfolioMetric:
    metric = await get_portfolio_metric(session, metric_id)
    updates = payload.model_dump(exclude_unset=True)
    changes: dict[str, tuple[Any, Any]] = {}
    for field, value in updates.items():
        old_value = getattr(metric, field)
        if old_value != value:
            changes[field] = (old_value, value)
            setattr(metric, field, value)
    if changes:
        await audit_service.record_update(
            session, actor=actor_from_user(actor), entity=metric, changes=changes
        )
    await session.commit()
    await session.refresh(metric)
    return metric
