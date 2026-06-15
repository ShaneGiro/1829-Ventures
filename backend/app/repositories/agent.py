"""Repository for Ritchie governance tables: policy, events, AI audit."""

from __future__ import annotations

import uuid
from typing import Any, cast

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.constants import AgentEventStatus, AiWriteStatus, PolicyState
from app.models.agent_event_log import AgentEventLog
from app.models.agent_policy import AgentPolicy
from app.models.ai_audit_log import AiAuditLog


# ─── Policy ───────────────────────────────────────────────────────────────────
async def get_policy(
    session: AsyncSession, tool: str, field_name: str | None
) -> AgentPolicy | None:
    stmt = select(AgentPolicy).where(AgentPolicy.tool == tool)
    stmt = stmt.where(
        AgentPolicy.field_name == field_name
        if field_name is not None
        else AgentPolicy.field_name.is_(None)
    )
    return cast("AgentPolicy | None", await session.scalar(stmt))


async def list_policies(session: AsyncSession) -> list[AgentPolicy]:
    stmt = select(AgentPolicy).order_by(AgentPolicy.tool, AgentPolicy.field_name)
    return list(await session.scalars(stmt))


async def upsert_policy(
    session: AsyncSession,
    *,
    tool: str,
    field_name: str | None,
    state: PolicyState,
    updated_by: uuid.UUID | None,
) -> AgentPolicy:
    policy = await get_policy(session, tool, field_name)
    if policy is None:
        policy = AgentPolicy(tool=tool, field_name=field_name, state=state, updated_by=updated_by)
        session.add(policy)
    else:
        policy.state = state
        policy.updated_by = updated_by
    await session.flush()
    return policy


# ─── Events ───────────────────────────────────────────────────────────────────
async def create_event(
    session: AsyncSession,
    *,
    event_type: str,
    entity_type: str | None,
    entity_id: str | None,
    payload: dict[str, Any],
    payload_hash: str | None,
    status: AgentEventStatus = AgentEventStatus.PENDING,
) -> AgentEventLog:
    event = AgentEventLog(
        event_type=event_type,
        entity_type=entity_type,
        entity_id=entity_id,
        payload=payload,
        payload_hash=payload_hash,
        status=status,
    )
    session.add(event)
    await session.flush()
    return event


async def get_event(session: AsyncSession, event_id: uuid.UUID) -> AgentEventLog | None:
    return cast(
        "AgentEventLog | None",
        await session.scalar(select(AgentEventLog).where(AgentEventLog.id == event_id)),
    )


async def list_events(session: AsyncSession, *, limit: int, offset: int) -> list[AgentEventLog]:
    stmt = (
        select(AgentEventLog).order_by(AgentEventLog.created_at.desc()).limit(limit).offset(offset)
    )
    return list(await session.scalars(stmt))


async def count_events(session: AsyncSession) -> int:
    return int(await session.scalar(select(func.count()).select_from(AgentEventLog)) or 0)


# ─── AI audit ─────────────────────────────────────────────────────────────────
async def get_ai_audit_by_key(session: AsyncSession, idempotency_key: str) -> AiAuditLog | None:
    return cast(
        "AiAuditLog | None",
        await session.scalar(
            select(AiAuditLog).where(AiAuditLog.idempotency_key == idempotency_key)
        ),
    )


async def create_ai_audit_pending(
    session: AsyncSession,
    *,
    tool: str,
    entity_type: str | None,
    entity_id: uuid.UUID | None,
    field_name: str | None,
    old_value: dict[str, Any] | None,
    new_value: dict[str, Any] | None,
    source: str | None,
    confidence: float | None,
    idempotency_key: str,
) -> AiAuditLog:
    audit = AiAuditLog(
        tool=tool,
        entity_type=entity_type,
        entity_id=entity_id,
        status=AiWriteStatus.PENDING,
        field_name=field_name,
        old_value=old_value,
        new_value=new_value,
        source=source,
        confidence=confidence,
        idempotency_key=idempotency_key,
    )
    session.add(audit)
    await session.flush()
    return audit
