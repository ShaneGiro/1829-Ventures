"""Policy flow: blocked call rejected/logged -> authorized -> retry executes.

The retry uses the same idempotency key as the original attempt (event ID + tool
+ entity), per the brief.
"""

from __future__ import annotations

import uuid

import pytest

from app.core.idempotency import build_idempotency_key
from app.services import agent_service
from tests.unit.agent_helpers import FakeAsyncSession, make_agent_user, make_fake_tool


@pytest.mark.asyncio
async def test_blocked_then_authorized_retry_executes_with_same_key(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls: list[str] = []
    tool = make_fake_tool(calls=calls)
    company_id = uuid.uuid4()
    event_id = "evt-flow-1"
    expected_key = build_idempotency_key(event_id, tool.name, str(company_id))

    monkeypatch.setattr(agent_service, "get_tool", lambda _name: tool)

    state_holder = {"state": "blocked"}

    async def effective_state(*_a: object, **_k: object) -> object:
        from app.core.constants import PolicyState

        return PolicyState.BLOCKED if state_holder["state"] == "blocked" else PolicyState.AUTHORIZED

    async def no_existing(*_a: object, **_k: object) -> None:
        return None

    monkeypatch.setattr(agent_service.agent_policy_service, "get_effective_state", effective_state)
    monkeypatch.setattr(agent_service.agent_repo, "get_ai_audit_by_key", no_existing)

    payload = {"company_id": str(company_id), "value": "x"}

    # 1) Blocked: rejected, logged, no write.
    blocked = await agent_service.execute_tool(
        FakeAsyncSession(),  # type: ignore[arg-type]
        agent_user=make_agent_user(),
        tool_name=tool.name,
        payload=payload,
        event_id=event_id,
    )
    assert blocked.status == "blocked"
    assert calls == []

    # 2) Human authorizes the tool at runtime.
    state_holder["state"] = "authorized"

    # 3) Retry with the same event id -> executes with the original idempotency key.
    executed = await agent_service.execute_tool(
        FakeAsyncSession(),  # type: ignore[arg-type]
        agent_user=make_agent_user(),
        tool_name=tool.name,
        payload=payload,
        event_id=event_id,
    )
    assert executed.status == "executed"
    assert executed.idempotency_key == expected_key
    assert calls == [tool.name]
