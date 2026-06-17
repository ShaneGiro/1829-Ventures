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
    """Synchronous POST to kernelbot's scheduler. Raises on failure for retry.

    No-op when no webhook is configured (local dev), so nothing blocks.
    """
    url = settings.ritchie_webhook_url
    if not url:
        return
    headers = {"Content-Type": "application/json"}
    body = {
        "tag": settings.ritchie_scheduler_tag,
        "envelope": envelope,
        "model": settings.ritchie_scheduler_model,
        "max_retries": settings.ritchie_scheduler_max_retries,
    }
    try:
        response = httpx.post(url, json=body, headers=headers, timeout=timeout)
        response.raise_for_status()
    except httpx.HTTPError as exc:
        raise RitchieUnavailableError(str(exc)) from exc


def chat_with_ritchie(envelope: dict[str, Any], *, timeout: float | None = None) -> dict[str, Any]:
    """Synchronously invoke kernelbot and return Ritchie's chat summary."""
    url = settings.ritchie_chat_url
    if not url:
        raise RitchieUnavailableError("Ritchie chat URL is not configured")
    turn_timeout = timeout or settings.ritchie_chat_timeout_seconds
    body = {
        "trigger": "crm_chat",
        "envelope": envelope,
        "timeout_ms": int(turn_timeout * 1000),
    }
    try:
        response = httpx.post(
            url,
            json=body,
            headers={"Content-Type": "application/json"},
            timeout=turn_timeout + 10,
        )
        response.raise_for_status()
        data = response.json()
    except httpx.HTTPError as exc:
        raise RitchieUnavailableError(str(exc)) from exc

    if not isinstance(data, dict):
        raise RitchieUnavailableError("Ritchie chat returned an invalid response")
    return data
