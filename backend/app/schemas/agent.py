"""Ritchie agent schemas: authorization policy, audit, and event read models.

Agent 02 ships the policy/audit/event read+update schemas backing the data model.
Agent 10 adds the typed tool-definition and context-request schemas.
"""

from __future__ import annotations

import uuid
from typing import Any

from pydantic import BaseModel

from app.core.constants import AgentEventStatus, AiWriteStatus, PolicyState
from app.schemas.common import TimestampedRead


class AgentPolicyRead(TimestampedRead):
    tool: str
    field_name: str | None = None
    state: PolicyState
    updated_by: uuid.UUID | None = None


class AgentPolicyUpdate(BaseModel):
    """Flip a tool/field between authorized and blocked at runtime."""

    state: PolicyState


class AiAuditLogRead(TimestampedRead):
    tool: str
    entity_type: str | None = None
    entity_id: uuid.UUID | None = None
    status: AiWriteStatus
    field_name: str | None = None
    old_value: dict[str, Any] | None = None
    new_value: dict[str, Any] | None = None
    source: str | None = None
    confidence: float | None = None
    idempotency_key: str
    error: str | None = None


class AgentEventLogRead(TimestampedRead):
    event_type: str
    entity_type: str | None = None
    entity_id: str | None = None
    status: AgentEventStatus
    payload_hash: str | None = None
    blocked_tool: str | None = None
    rationale: str | None = None
    confidence: float | None = None
    response_summary: str | None = None
