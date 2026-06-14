"""Celery jobs for analytics refresh hooks.

Current v1 analytics are computed live from indexed aggregates. These tasks give
the scheduler/Ritchie a non-request path to warm or validate those queries, and
leave room for materialized snapshots later without changing callers.
"""

from __future__ import annotations

import asyncio

from app.core.database import AsyncSessionLocal
from app.services import analytics_service
from app.workers.celery_app import celery_app


@celery_app.task(name="analytics.refresh")
def refresh_analytics() -> dict[str, int]:
    async def _run() -> dict[str, int]:
        async with AsyncSessionLocal() as session:
            pipeline = await analytics_service.get_pipeline_summary(session)
            agent = await analytics_service.get_agent_activity_summary(session)
            return {
                "total_companies": pipeline.total_companies,
                "total_deals": pipeline.total_deals,
                "agent_status_buckets": len(agent.by_event_status),
            }

    return asyncio.run(_run())
