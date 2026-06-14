"""Fund, investment, and portfolio metric repository helpers."""

from __future__ import annotations

import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.fund import Fund
from app.models.investment import Investment
from app.models.portfolio_metric import PortfolioMetric
from app.repositories import base


async def get_fund(session: AsyncSession, fund_id: uuid.UUID) -> Fund | None:
    return await base.get_by_id(session, Fund, fund_id)


async def list_funds(session: AsyncSession, *, limit: int, offset: int) -> list[Fund]:
    return await base.list_rows(session, Fund, limit=limit, offset=offset, order_by=Fund.name)


async def count_funds(session: AsyncSession) -> int:
    return await base.count_rows(session, Fund)


async def create_fund(session: AsyncSession, fund: Fund) -> Fund:
    session.add(fund)
    await session.flush()
    return fund


async def get_investment(
    session: AsyncSession, investment_id: uuid.UUID, *, include_archived: bool = False
) -> Investment | None:
    return await base.get_by_id(
        session, Investment, investment_id, include_archived=include_archived
    )


async def list_investments(
    session: AsyncSession, *, limit: int, offset: int, include_archived: bool = False
) -> list[Investment]:
    return await base.list_rows(
        session,
        Investment,
        limit=limit,
        offset=offset,
        include_archived=include_archived,
    )


async def count_investments(session: AsyncSession, *, include_archived: bool = False) -> int:
    return await base.count_rows(session, Investment, include_archived=include_archived)


async def create_investment(session: AsyncSession, investment: Investment) -> Investment:
    session.add(investment)
    await session.flush()
    return investment


async def get_portfolio_metric(
    session: AsyncSession, metric_id: uuid.UUID
) -> PortfolioMetric | None:
    return await base.get_by_id(session, PortfolioMetric, metric_id)


async def list_portfolio_metrics(
    session: AsyncSession, *, limit: int, offset: int
) -> list[PortfolioMetric]:
    return await base.list_rows(session, PortfolioMetric, limit=limit, offset=offset)


async def count_portfolio_metrics(session: AsyncSession) -> int:
    return await base.count_rows(session, PortfolioMetric)


async def create_portfolio_metric(
    session: AsyncSession, metric: PortfolioMetric
) -> PortfolioMetric:
    session.add(metric)
    await session.flush()
    return metric
