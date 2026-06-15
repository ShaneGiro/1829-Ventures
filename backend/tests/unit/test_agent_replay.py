"""Replay recorded tool payloads deterministically, with no live LLM calls.

Ritchie tools are typed handlers — no model/network call is made — so replaying a
recorded payload is safe and, with the same event id, idempotent.
"""

from __future__ import annotations

import uuid
from typing import Any

import pytest

from app.core.constants import AiWriteStatus, PolicyState
from app.models.ai_audit_log import AiAuditLog
from app.services import agent_service
from tests.unit.agent_helpers import FakeAsyncSession, make_agent_user, make_fake_tool

# A small recording of tool calls captured from a prior run.
RECORDED_PAYLOADS = [
    {"company_id": str(uuid.uuid4()), "value": "first"},
    {"company_id": str(uuid.uuid4()), "value": "second"},
]


@pytest.mark.asyncio
async def test_replay_recorded_payloads_executes_without_network(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls: list[str] = []
    tool = make_fake_tool(calls=calls)
    monkeypatch.setattr(agent_service, "get_tool", lambda _name: tool)

    async def authorized(*_a: object, **_k: object) -> PolicyState:
        return PolicyState.AUTHORIZED

    async def no_existing(*_a: object, **_k: object) -> None:
        return None

    monkeypatch.setattr(agent_service.agent_policy_service, "get_effective_state", authorized)
    monkeypatch.setattr(agent_service.agent_repo, "get_ai_audit_by_key", no_existing)

    for index, payload in enumerate(RECORDED_PAYLOADS):
        result = await agent_service.execute_tool(
            FakeAsyncSession(),  # type: ignore[arg-type]
            agent_user=make_agent_user(),
            tool_name=tool.name,
            payload=payload,
            event_id=f"replay-{index}",
        )
        assert result.status == "executed"
    assert calls == [tool.name, tool.name]


@pytest.mark.asyncio
async def test_replaying_same_event_is_idempotent(monkeypatch: pytest.MonkeyPatch) -> None:
    calls: list[str] = []
    tool = make_fake_tool(calls=calls)
    store: dict[str, AiAuditLog] = {}
    monkeypatch.setattr(agent_service, "get_tool", lambda _name: tool)

    async def authorized(*_a: object, **_k: object) -> PolicyState:
        return PolicyState.AUTHORIZED

    async def get_by_key(_session: object, key: str) -> AiAuditLog | None:
        return store.get(key)

    async def create_pending(session: Any, **kwargs: Any) -> AiAuditLog:
        audit = AiAuditLog(
            tool=kwargs["tool"],
            entity_type=kwargs["entity_type"],
            entity_id=kwargs["entity_id"],
            status=AiWriteStatus.PENDING,
            field_name=kwargs["field_name"],
            old_value=kwargs["old_value"],
            new_value=kwargs["new_value"],
            source=kwargs["source"],
            confidence=kwargs["confidence"],
            idempotency_key=kwargs["idempotency_key"],
        )
        session.add(audit)
        store[kwargs["idempotency_key"]] = audit
        return audit

    monkeypatch.setattr(agent_service.agent_policy_service, "get_effective_state", authorized)
    monkeypatch.setattr(agent_service.agent_repo, "get_ai_audit_by_key", get_by_key)
    monkeypatch.setattr(agent_service.agent_repo, "create_ai_audit_pending", create_pending)

    payload = {"company_id": str(uuid.uuid4()), "value": "x"}
    session = FakeAsyncSession()

    first = await agent_service.execute_tool(
        session,  # type: ignore[arg-type]
        agent_user=make_agent_user(),
        tool_name=tool.name,
        payload=payload,
        event_id="evt-replay",
    )
    assert first.status == "executed"

    # Replaying the identical event is a no-op (the recorded write already committed).
    second = await agent_service.execute_tool(
        session,  # type: ignore[arg-type]
        agent_user=make_agent_user(),
        tool_name=tool.name,
        payload=payload,
        event_id="evt-replay",
    )
    assert second.status == "duplicate"
    assert calls == [tool.name]  # handler ran exactly once
