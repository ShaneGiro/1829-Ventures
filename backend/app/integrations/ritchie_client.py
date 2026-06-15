"""Outbound event fanout to kernelbot (Ritchie's runtime).

Backend state changes enqueue JSON envelopes here. Delivery is best-effort and
non-blocking: the request path enqueues a background job; the job retries with
backoff and, on exhaustion, marks the event `agent_unavailable`. Ritchie being
down never breaks user-facing functionality.
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from typing import Any

import httpx

from app.core.config import settings


def build_envelope(
    event_type: str,
    payload: dict[str, Any],
    *,
    entity_type: str | None = None,
    entity_id: str | None = None,
) -> dict[str, Any]:
    return {
        "id": str(uuid.uuid4()),
        "event_type": event_type,
        "entity_type": entity_type,
        "entity_id": entity_id,
        "payload": payload,
        "emitted_at": datetime.now(UTC).isoformat(),
    }


class RitchieUnavailableError(RuntimeError):
    """Raised when the kernelbot webhook cannot be reached (triggers retry)."""


def deliver_envelope(envelope: dict[str, Any], *, timeout: float = 5.0) -> None:
    """Synchronous POST to the kernelbot webhook. Raises on failure for retry.

    No-op when no webhook is configured (local dev), so nothing blocks.
    """
    url = settings.ritchie_webhook_url
    if not url:
        return
    headers = {"Content-Type": "application/json"}
    if settings.agent_api_key:
        headers["Authorization"] = f"Bearer {settings.agent_api_key}"
    try:
        response = httpx.post(url, json=envelope, headers=headers, timeout=timeout)
        response.raise_for_status()
    except httpx.HTTPError as exc:
        raise RitchieUnavailableError(str(exc)) from exc
