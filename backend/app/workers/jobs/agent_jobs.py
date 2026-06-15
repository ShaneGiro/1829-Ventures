"""Celery jobs for Ritchie event fanout with graceful degradation.

Delivery retries with exponential backoff. When retries are exhausted, the
originating agent event is marked `agent_unavailable` — the failure is logged and
recoverable, and never blocks user-facing functionality.
"""

from __future__ import annotations

import asyncio
import uuid
from typing import Any

from celery import Task

from app.core.constants import AgentEventStatus
from app.core.database import AsyncSessionLocal
from app.integrations.ritchie_client import RitchieUnavailableError, deliver_envelope
from app.repositories import agent as agent_repo
from app.workers.celery_app import celery_app

MAX_RETRIES = 5


async def _mark_agent_unavailable(event_id: uuid.UUID, detail: str) -> None:
    async with AsyncSessionLocal() as session:
        event = await agent_repo.get_event(session, event_id)
        if event is not None:
            event.status = AgentEventStatus.AGENT_UNAVAILABLE
            event.rationale = detail
            await session.commit()


@celery_app.task(bind=True, name="agent.deliver_event", max_retries=MAX_RETRIES)
def deliver_agent_event(self: Task, envelope: dict[str, Any], event_id: str | None = None) -> str:
    """Deliver one event envelope to kernelbot; retry with backoff on failure."""
    try:
        deliver_envelope(envelope)
    except RitchieUnavailableError as exc:
        if self.request.retries >= MAX_RETRIES:
            if event_id is not None:
                asyncio.run(_mark_agent_unavailable(uuid.UUID(event_id), str(exc)))
            return "agent_unavailable"
        # Exponential backoff: 2s, 4s, 8s, ...
        raise self.retry(exc=exc, countdown=2 ** (self.request.retries + 1)) from exc
    return "delivered"
