"""Ritchie agent schemas: authorization policy, audit, and event read models.

Agent 02 ships the policy/audit/event read+update schemas backing the data model.
Agent 10 adds the typed tool-definition and context-request schemas.
"""

from __future__ import annotations

import uuid
from typing import Any

from pydantic import BaseModel, Field

from app.core.constants import AgentEventStatus, AiWriteStatus, PolicyState
from app.schemas.common import TimestampedRead


class ToolDefinition(BaseModel):
    """A typed tool's wire contract: name, kind, effective state, JSON Schema."""

    name: str
    description: str
    kind: str
    state: PolicyState
    entity_type: str | None = None
    input_schema: dict[str, Any]


class ToolExecuteRequest(BaseModel):
    payload: dict[str, Any] = Field(default_factory=dict)
    event_id: str | None = None
    confidence: float | None = None
    source: str | None = None


class ToolExecuteResponse(BaseModel):
    status: str
    tool: str
    data: Any = None
    rationale: str | None = None
    idempotency_key: str | None = None
    ai_audit_id: str | None = None
    event_id: str | None = None


class AgentMessageRequest(BaseModel):
    """Human-authored work item to enqueue for Ritchie."""

    prompt: str = Field(min_length=1, max_length=8000)
    entity_type: str | None = Field(default=None, max_length=64)
    entity_id: str | None = Field(default=None, max_length=128)


class AgentMessageResponse(BaseModel):
    event_id: uuid.UUID
    status: AgentEventStatus


class AgentChatRequest(AgentMessageRequest):
    """Human-authored chat turn that should receive a Ritchie response."""


class AgentChatResponse(BaseModel):
    event_id: uuid.UUID
    status: AgentEventStatus
    message: str
    elapsed_ms: int | None = None


class AgentContextResult(BaseModel):
    entity_type: str
    entity_id: uuid.UUID
    title: str
    snippet: str | None = None
    rank: float


class PolicySetRequest(BaseModel):
    tool: str
    field_name: str | None = None
    state: PolicyState


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
