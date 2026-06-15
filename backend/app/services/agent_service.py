"""Ritchie tool execution: policy gate, AI audit, idempotency, event logging.

Flow for every tool call:
  1. Validate payload against the tool's typed model (no free-form text writes).
  2. Record an agent event (processing).
  3. Policy gate: if BLOCKED, log `policy_blocked` and return WITHOUT writing.
  4. Reads: run the handler, return.
  5. Writes: build the idempotency key; if a committed audit row exists, no-op;
     otherwise record AI-audit intent (pending) BEFORE the canonical write, run
     the handler, then mark committed (or failed on exception).

The gate runs before any handler/service logic, so a blocked tool cannot write
under any code path.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from typing import Any

from pydantic import ValidationError as PydanticValidationError
from sqlalchemy.ext.asyncio import AsyncSession

from app.agent.tools import AgentTool, get_tool
from app.core.constants import AgentEventStatus, AiWriteStatus, PolicyState
from app.core.exceptions import PolicyBlockedError, ValidationError
from app.core.idempotency import build_idempotency_key
from app.models.user import User
from app.repositories import agent as agent_repo
from app.services import agent_policy_service


@dataclass(frozen=True)
class ToolExecution:
    status: str  # "executed" | "blocked" | "duplicate" | "failed"
    tool: str
    data: Any = None
    rationale: str | None = None
    idempotency_key: str | None = None
    ai_audit_id: str | None = None
    event_id: str | None = None


def _payload_hash(payload: dict[str, Any]) -> str:
    return hashlib.sha256(json.dumps(payload, sort_keys=True, default=str).encode()).hexdigest()


async def execute_tool(
    session: AsyncSession,
    *,
    agent_user: User,
    tool_name: str,
    payload: dict[str, Any],
    event_id: str,
    confidence: float | None = None,
    source: str | None = None,
) -> ToolExecution:
    tool = get_tool(tool_name)
    if tool is None:
        raise ValidationError(f"Unknown tool: {tool_name}")

    try:
        parsed = tool.input_model.model_validate(payload)
    except PydanticValidationError as exc:
        raise ValidationError(f"Invalid payload for {tool_name}: {exc.errors()}") from exc

    payload_dict = parsed.model_dump(mode="json")
    phash = _payload_hash(payload_dict)
    entity_id_str = _extract_entity_id(payload_dict)
    field_name = payload_dict.get("field_name") if isinstance(payload_dict, dict) else None

    event = await agent_repo.create_event(
        session,
        event_type=f"tool:{tool_name}",
        entity_type=tool.entity_type,
        entity_id=entity_id_str,
        payload=payload_dict,
        payload_hash=phash,
        status=AgentEventStatus.PROCESSING,
    )

    # ── Policy gate (before any handler/service logic) ──
    state = await agent_policy_service.get_effective_state(session, tool_name, field_name)
    if state is PolicyState.BLOCKED:
        rationale = f"Tool '{tool_name}' is blocked by policy"
        event.status = AgentEventStatus.POLICY_BLOCKED
        event.blocked_tool = tool_name
        event.rationale = rationale
        event.confidence = confidence
        await session.commit()
        return ToolExecution(
            status="blocked", tool=tool_name, rationale=rationale, event_id=str(event.id)
        )

    # ── Reads: no audit/idempotency needed ──
    if tool.kind == "read":
        result = await tool.handler(session, parsed, agent_user)
        event.status = AgentEventStatus.PROCESSED
        await session.commit()
        return ToolExecution(
            status="executed", tool=tool_name, data=result.data, event_id=str(event.id)
        )

    # ── Writes: idempotency + AI audit intent → canonical write → committed ──
    idempotency_key = build_idempotency_key(event_id, tool_name, entity_id_str)
    existing = await agent_repo.get_ai_audit_by_key(session, idempotency_key)
    if existing is not None and existing.status == AiWriteStatus.COMMITTED:
        event.status = AgentEventStatus.PROCESSED
        event.response_summary = "duplicate (idempotent no-op)"
        await session.commit()
        return ToolExecution(
            status="duplicate",
            tool=tool_name,
            idempotency_key=idempotency_key,
            ai_audit_id=str(existing.id),
            event_id=str(event.id),
        )

    audit = await agent_repo.create_ai_audit_pending(
        session,
        tool=tool_name,
        entity_type=tool.entity_type,
        entity_id=None,
        field_name=field_name,
        old_value=None,
        new_value=payload_dict,
        source=source,
        confidence=confidence,
        idempotency_key=idempotency_key,
    )

    return await _run_write(
        session,
        tool,
        parsed,
        agent_user,
        audit_id=audit.id,
        event_id=event.id,
        tool_name=tool_name,
        idempotency_key=idempotency_key,
    )


async def _run_write(
    session: AsyncSession,
    tool: AgentTool,
    parsed: Any,
    agent_user: User,
    *,
    audit_id: Any,
    event_id: Any,
    tool_name: str,
    idempotency_key: str,
) -> ToolExecution:
    from app.models.agent_event_log import AgentEventLog
    from app.models.ai_audit_log import AiAuditLog

    try:
        result = await tool.handler(session, parsed, agent_user)
    except Exception as exc:  # noqa: BLE001 - record failure, never leak a partial write
        await session.rollback()
        audit = await session.get(AiAuditLog, audit_id)
        if audit is not None:
            audit.status = AiWriteStatus.FAILED
            audit.error = f"{type(exc).__name__}: {exc}"
        event = await session.get(AgentEventLog, event_id)
        if event is not None:
            event.status = AgentEventStatus.FAILED
            event.rationale = f"{type(exc).__name__}: {exc}"
        await session.commit()
        return ToolExecution(
            status="failed", tool=tool_name, rationale=str(exc), idempotency_key=idempotency_key
        )

    audit = await session.get(AiAuditLog, audit_id)
    if audit is not None:
        audit.status = AiWriteStatus.COMMITTED
        audit.entity_id = result.entity_id
        if result.old_value is not None:
            audit.old_value = result.old_value
        if result.new_value is not None:
            audit.new_value = result.new_value
    event = await session.get(AgentEventLog, event_id)
    if event is not None:
        event.status = AgentEventStatus.PROCESSED
        event.response_summary = f"committed {tool_name}"
    await session.commit()
    return ToolExecution(
        status="executed",
        tool=tool_name,
        data=result.data,
        idempotency_key=idempotency_key,
        ai_audit_id=str(audit_id),
        event_id=str(event_id),
    )


def _extract_entity_id(payload: dict[str, Any]) -> str | None:
    for key in ("company_id", "investment_id", "rubric_id", "deal_id", "person_id", "task_id"):
        value = payload.get(key)
        if value:
            return str(value)
    return None


async def assert_tool_authorized(session: AsyncSession, tool_name: str) -> None:
    """Helper for callers that want to fail fast outside execute_tool."""
    state = await agent_policy_service.get_effective_state(session, tool_name)
    if state is PolicyState.BLOCKED:
        raise PolicyBlockedError(f"Tool '{tool_name}' is blocked by policy")
