"""Analytics service layer."""

from __future__ import annotations

import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories import analytics as analytics_repo
from app.schemas.analytics import (
    AgentActivitySummary,
    CountByKey,
    InteractionCadence,
    PipelineSummary,
    PortfolioSummary,
    ThesisFitSummary,
)


async def get_pipeline_summary(
    session: AsyncSession, *, include_unreviewed: bool = False
) -> PipelineSummary:
    return PipelineSummary(
        by_relationship_status=await analytics_repo.counts_by_relationship_status(
            session, include_unreviewed=include_unreviewed
        ),
        by_investment_status=await analytics_repo.counts_by_investment_status(session),
        total_companies=await analytics_repo.count_companies(
            session, include_unreviewed=include_unreviewed
        ),
        total_deals=await analytics_repo.count_deals(session),
    )


async def get_portfolio_summary(
    session: AsyncSession, *, fund_id: uuid.UUID | None = None
) -> PortfolioSummary:
    totals = await analytics_repo.portfolio_totals(session, fund_id=fund_id)
    return PortfolioSummary(
        **totals,
        by_fund=await analytics_repo.portfolio_by_fund(session, fund_id=fund_id),
    )


async def get_source_summary(
    session: AsyncSession, *, include_unreviewed: bool = False
) -> list[CountByKey]:
    return await analytics_repo.counts_by_source(session, include_unreviewed=include_unreviewed)


async def get_sector_summary(
    session: AsyncSession, *, include_unreviewed: bool = False
) -> list[CountByKey]:
    return await analytics_repo.counts_by_sector(session, include_unreviewed=include_unreviewed)


async def get_interaction_cadence(
    session: AsyncSession,
    *,
    days: int = 30,
    stale_days: int = 30,
) -> InteractionCadence:
    return InteractionCadence(
        days=days,
        points=await analytics_repo.interaction_cadence(session, days=days),
        stale_company_count=await analytics_repo.stale_company_count(
            session, days_without_touch=stale_days
        ),
    )


async def get_thesis_fit_summary(session: AsyncSession) -> ThesisFitSummary:
    return ThesisFitSummary(
        by_sector=await analytics_repo.counts_by_sector(session, include_unreviewed=False),
        by_rubric_bucket=await analytics_repo.rubric_score_buckets(session),
        rit_nexus=await analytics_repo.rit_nexus_counts(session),
    )


async def get_agent_activity_summary(session: AsyncSession) -> AgentActivitySummary:
    return AgentActivitySummary(
        by_event_status=await analytics_repo.agent_event_counts(session),
        blocked_attempts_by_tool=await analytics_repo.blocked_attempt_counts(session),
        trusted_writes_by_tool=await analytics_repo.trusted_write_counts(session),
    )
