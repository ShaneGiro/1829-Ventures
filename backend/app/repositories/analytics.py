"""Aggregation queries for analytics dashboards."""

from __future__ import annotations

import uuid
from datetime import date, timedelta
from decimal import Decimal
from typing import Any

from sqlalchemy import case, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.constants import AgentEventStatus, AiWriteStatus
from app.models.agent_event_log import AgentEventLog
from app.models.ai_audit_log import AiAuditLog
from app.models.company import Company
from app.models.deal import Deal
from app.models.interaction import Interaction
from app.models.investment import Investment
from app.models.portfolio_metric import PortfolioMetric
from app.models.rubric import Rubric
from app.schemas.analytics import CountByKey, InteractionCadencePoint, NumericByKey


async def count_companies(session: AsyncSession, *, include_unreviewed: bool) -> int:
    stmt = select(func.count()).select_from(Company).where(Company.archived_at.is_(None))
    if not include_unreviewed:
        stmt = stmt.where(Company.imported_unreviewed.is_(False))
    return int(await session.scalar(stmt) or 0)


async def count_deals(session: AsyncSession) -> int:
    stmt = select(func.count()).select_from(Deal).where(Deal.archived_at.is_(None))
    return int(await session.scalar(stmt) or 0)


async def counts_by_relationship_status(
    session: AsyncSession, *, include_unreviewed: bool
) -> list[CountByKey]:
    stmt = (
        select(Company.relationship_status, func.count())
        .where(Company.archived_at.is_(None))
        .group_by(Company.relationship_status)
        .order_by(Company.relationship_status)
    )
    if not include_unreviewed:
        stmt = stmt.where(Company.imported_unreviewed.is_(False))
    return _count_rows(await session.execute(stmt))


async def counts_by_investment_status(session: AsyncSession) -> list[CountByKey]:
    stmt = (
        select(Deal.investment_status, func.count())
        .where(Deal.archived_at.is_(None))
        .group_by(Deal.investment_status)
        .order_by(Deal.investment_status)
    )
    return _count_rows(await session.execute(stmt))


async def counts_by_source(session: AsyncSession, *, include_unreviewed: bool) -> list[CountByKey]:
    stmt = (
        select(func.coalesce(Company.source_system, "manual"), func.count())
        .where(Company.archived_at.is_(None))
        .group_by(func.coalesce(Company.source_system, "manual"))
        .order_by(func.count().desc())
    )
    if not include_unreviewed:
        stmt = stmt.where(Company.imported_unreviewed.is_(False))
    return _count_rows(await session.execute(stmt))


async def counts_by_sector(session: AsyncSession, *, include_unreviewed: bool) -> list[CountByKey]:
    stmt = (
        select(Company.sector, func.count())
        .where(Company.archived_at.is_(None))
        .group_by(Company.sector)
        .order_by(func.count().desc(), Company.sector)
    )
    if not include_unreviewed:
        stmt = stmt.where(Company.imported_unreviewed.is_(False))
    return _count_rows(await session.execute(stmt))


async def portfolio_by_fund(
    session: AsyncSession, fund_id: uuid.UUID | None = None
) -> list[NumericByKey]:
    from app.models.fund import Fund

    stmt = (
        select(Fund.name, func.sum(Investment.amount))
        .join(Investment, Investment.fund_id == Fund.id)
        .where(Investment.archived_at.is_(None))
        .group_by(Fund.name)
        .order_by(Fund.name)
    )
    if fund_id is not None:
        stmt = stmt.where(Fund.id == fund_id)
    rows = await session.execute(stmt)
    return [NumericByKey(key=str(key), value=_decimal(value)) for key, value in rows]


async def portfolio_totals(
    session: AsyncSession, fund_id: uuid.UUID | None = None
) -> dict[str, Any]:
    stmt = select(
        func.count(Investment.id),
        func.sum(Investment.amount),
        func.sum(PortfolioMetric.valuation_mark),
        func.avg(PortfolioMetric.tvpi),
        func.avg(PortfolioMetric.dpi),
        func.avg(PortfolioMetric.irr),
    ).select_from(Investment)
    stmt = stmt.outerjoin(PortfolioMetric, PortfolioMetric.investment_id == Investment.id)
    stmt = stmt.where(Investment.archived_at.is_(None))
    if fund_id is not None:
        stmt = stmt.where(Investment.fund_id == fund_id)
    row = (await session.execute(stmt)).one()
    return {
        "total_investments": int(row[0] or 0),
        "total_invested_amount": _decimal(row[1]),
        "total_valuation_mark": _decimal(row[2]),
        "average_tvpi": _decimal(row[3]),
        "average_dpi": _decimal(row[4]),
        "average_irr": _decimal(row[5]),
    }


async def interaction_cadence(session: AsyncSession, *, days: int) -> list[InteractionCadencePoint]:
    start_date = date.today() - timedelta(days=days - 1)
    period = func.date(func.coalesce(Interaction.occurred_at, Interaction.created_at))
    stmt = (
        select(period.label("period"), func.count())
        .where(
            Interaction.archived_at.is_(None),
            period >= start_date,
        )
        .group_by(period)
        .order_by(period)
    )
    rows = await session.execute(stmt)
    return [InteractionCadencePoint(period=key, count=int(count)) for key, count in rows]


async def stale_company_count(session: AsyncSession, *, days_without_touch: int) -> int:
    cutoff = date.today() - timedelta(days=days_without_touch)
    latest_touch = (
        select(
            Interaction.company_id.label("company_id"),
            func.max(
                func.date(func.coalesce(Interaction.occurred_at, Interaction.created_at))
            ).label("last_touch"),
        )
        .where(Interaction.archived_at.is_(None), Interaction.company_id.is_not(None))
        .group_by(Interaction.company_id)
        .subquery()
    )
    stmt = (
        select(func.count())
        .select_from(Company)
        .outerjoin(latest_touch, latest_touch.c.company_id == Company.id)
        .where(
            Company.archived_at.is_(None),
            Company.imported_unreviewed.is_(False),
            (latest_touch.c.last_touch.is_(None)) | (latest_touch.c.last_touch < cutoff),
        )
    )
    return int(await session.scalar(stmt) or 0)


async def rubric_score_buckets(session: AsyncSession) -> list[CountByKey]:
    bucket = case(
        (Rubric.composite_score >= 80, "80-100"),
        (Rubric.composite_score >= 70, "70-79"),
        (Rubric.composite_score.is_not(None), "<70"),
        else_="unscored",
    )
    stmt = (
        select(bucket, func.count())
        .select_from(Rubric)
        .join(Deal, Deal.id == Rubric.deal_id)
        .where(Deal.archived_at.is_(None))
        .group_by(bucket)
        .order_by(bucket)
    )
    return _count_rows(await session.execute(stmt))


async def rit_nexus_counts(session: AsyncSession) -> list[CountByKey]:
    label = case((Company.has_rit_nexus.is_(True), "has_rit_nexus"), else_="missing_rit_nexus")
    stmt = (
        select(label, func.count())
        .select_from(Company)
        .where(Company.archived_at.is_(None), Company.imported_unreviewed.is_(False))
        .group_by(label)
        .order_by(label)
    )
    return _count_rows(await session.execute(stmt))


async def agent_event_counts(session: AsyncSession) -> list[CountByKey]:
    stmt = (
        select(AgentEventLog.status, func.count())
        .group_by(AgentEventLog.status)
        .order_by(AgentEventLog.status)
    )
    return _count_rows(await session.execute(stmt))


async def blocked_attempt_counts(session: AsyncSession) -> list[CountByKey]:
    stmt = (
        select(func.coalesce(AgentEventLog.blocked_tool, AgentEventLog.event_type), func.count())
        .where(AgentEventLog.status == AgentEventStatus.POLICY_BLOCKED)
        .group_by(func.coalesce(AgentEventLog.blocked_tool, AgentEventLog.event_type))
        .order_by(func.count().desc())
    )
    return _count_rows(await session.execute(stmt))


async def trusted_write_counts(session: AsyncSession) -> list[CountByKey]:
    stmt = (
        select(AiAuditLog.tool, func.count())
        .where(AiAuditLog.status == AiWriteStatus.COMMITTED)
        .group_by(AiAuditLog.tool)
        .order_by(func.count().desc())
    )
    return _count_rows(await session.execute(stmt))


def _count_rows(rows: Any) -> list[CountByKey]:
    return [CountByKey(key=str(key), count=int(count)) for key, count in rows]


def _decimal(value: object) -> Decimal | None:
    if value is None:
        return None
    if isinstance(value, Decimal):
        return value
    return Decimal(str(value))
