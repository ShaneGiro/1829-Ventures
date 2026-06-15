"""Runtime binary authorization policy for Ritchie.

Every tool (optionally narrowed to a field) is either AUTHORIZED or BLOCKED. The
effective state is the DB row if present, else the tool's registry default
(sensitive tools default BLOCKED). Flips are audited and take effect immediately
— there is no restart and no proposal/approval workflow.
"""

from __future__ import annotations

import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.agent.tools import get_tool
from app.core.audit import AuditActor
from app.core.constants import PolicyState
from app.repositories import agent as agent_repo
from app.services import audit_service


async def get_effective_state(
    session: AsyncSession, tool: str, field_name: str | None = None
) -> PolicyState:
    """Resolve the binary state: field-level row > tool-level row > registry default."""
    if field_name is not None:
        field_policy = await agent_repo.get_policy(session, tool, field_name)
        if field_policy is not None:
            return field_policy.state

    tool_policy = await agent_repo.get_policy(session, tool, None)
    if tool_policy is not None:
        return tool_policy.state

    registered = get_tool(tool)
    if registered is not None:
        return registered.default_state
    # Unknown tools are blocked by default — fail closed.
    return PolicyState.BLOCKED


async def set_state(
    session: AsyncSession,
    *,
    tool: str,
    field_name: str | None,
    state: PolicyState,
    actor: AuditActor,
    actor_id: uuid.UUID | None,
) -> None:
    """Flip a tool/field state. Audited; effective immediately on the next gate check."""
    previous = await agent_repo.get_policy(session, tool, field_name)
    old_state = previous.state if previous is not None else None
    policy = await agent_repo.upsert_policy(
        session, tool=tool, field_name=field_name, state=state, updated_by=actor_id
    )
    await audit_service.record_update(
        session,
        actor=actor,
        entity=policy,
        changes={"state": (old_state, state)},
        reason=f"Agent policy set for {tool}.{field_name or '*'}",
    )
    await session.commit()


async def seed_default_policies(session: AsyncSession, *, actor_id: uuid.UUID | None = None) -> int:
    """Persist explicit policy rows for every registered tool (idempotent).

    Effective-state resolution already falls back to registry defaults, so this is
    optional, but materializing rows makes the policy table self-documenting.
    """
    from app.agent.tools import all_tools

    created = 0
    for tool in all_tools():
        if await agent_repo.get_policy(session, tool.name, None) is None:
            await agent_repo.upsert_policy(
                session,
                tool=tool.name,
                field_name=None,
                state=tool.default_state,
                updated_by=actor_id,
            )
            created += 1
    await session.commit()
    return created
