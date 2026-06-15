"""Binary policy: blocked tools never write; flips resolve immediately + audited."""

from __future__ import annotations

import uuid
from typing import Any

import pytest

from app.core.constants import AgentEventStatus, PolicyState
from app.models.agent_event_log import AgentEventLog
from app.models.agent_policy import AgentPolicy
from app.services import agent_policy_service, agent_service
from tests.unit.agent_helpers import FakeAsyncSession, make_agent_user, make_fake_tool


@pytest.mark.asyncio
async def test_blocked_tool_never_writes(monkeypatch: pytest.MonkeyPatch) -> None:
    calls: list[str] = []
    tool = make_fake_tool(calls=calls, default_state=PolicyState.BLOCKED)
    session = FakeAsyncSession()
    monkeypatch.setattr(agent_service, "get_tool", lambda _name: tool)

    async def blocked(*_a: object, **_k: object) -> PolicyState:
        return PolicyState.BLOCKED

    monkeypatch.setattr(agent_service.agent_policy_service, "get_effective_state", blocked)

    result = await agent_service.execute_tool(
        session,  # type: ignore[arg-type]
        agent_user=make_agent_user(),
        tool_name=tool.name,
        payload={"company_id": str(uuid.uuid4()), "value": "x"},
        event_id="evt-blocked",
        confidence=0.4,
    )

    assert result.status == "blocked"
    assert calls == []  # handler never ran -> no write under any path
    events = [o for o in session.objects.values() if isinstance(o, AgentEventLog)]
    assert len(events) == 1
    assert events[0].status is AgentEventStatus.POLICY_BLOCKED
    assert events[0].blocked_tool == tool.name
    assert events[0].confidence == 0.4


@pytest.mark.asyncio
async def test_effective_state_falls_back_to_registry_default(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    async def no_row(*_a: object, **_k: object) -> None:
        return None

    monkeypatch.setattr(agent_policy_service.agent_repo, "get_policy", no_row)
    session: Any = FakeAsyncSession()

    blocked = await agent_policy_service.get_effective_state(session, "update_investment_amount")
    assert blocked is PolicyState.BLOCKED
    authorized = await agent_policy_service.get_effective_state(session, "search_context")
    assert authorized is PolicyState.AUTHORIZED


@pytest.mark.asyncio
async def test_db_policy_overrides_default(monkeypatch: pytest.MonkeyPatch) -> None:
    async def authorized_row(_session: object, tool: str, field: str | None) -> AgentPolicy:
        return AgentPolicy(tool=tool, field_name=field, state=PolicyState.AUTHORIZED)

    monkeypatch.setattr(agent_policy_service.agent_repo, "get_policy", authorized_row)

    # update_investment_amount defaults BLOCKED, but the DB row authorizes it.
    state = await agent_policy_service.get_effective_state(
        FakeAsyncSession(),  # type: ignore[arg-type]
        "update_investment_amount",
    )
    assert state is PolicyState.AUTHORIZED


@pytest.mark.asyncio
async def test_set_state_is_audited(monkeypatch: pytest.MonkeyPatch) -> None:
    recorded: list[dict[str, object]] = []

    async def get_policy(_session: object, _tool: str, _field: str | None) -> None:
        return None

    async def upsert(_session: object, **kwargs: object) -> AgentPolicy:
        return AgentPolicy(
            tool=str(kwargs["tool"]),
            field_name=kwargs["field_name"],  # type: ignore[arg-type]
            state=kwargs["state"],  # type: ignore[arg-type]
        )

    async def record_update(_session: object, **kwargs: object) -> list[object]:
        recorded.append(kwargs)
        return []

    monkeypatch.setattr(agent_policy_service.agent_repo, "get_policy", get_policy)
    monkeypatch.setattr(agent_policy_service.agent_repo, "upsert_policy", upsert)
    monkeypatch.setattr(agent_policy_service.audit_service, "record_update", record_update)

    from app.core.audit import system_actor

    await agent_policy_service.set_state(
        FakeAsyncSession(),  # type: ignore[arg-type]
        tool="update_investment_amount",
        field_name=None,
        state=PolicyState.AUTHORIZED,
        actor=system_actor("admin"),
        actor_id=uuid.uuid4(),
    )

    assert len(recorded) == 1
    assert "state" in recorded[0]["changes"]  # type: ignore[index]
