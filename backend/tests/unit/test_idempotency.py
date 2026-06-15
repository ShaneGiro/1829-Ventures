"""Idempotency keys: stability and duplicate-write prevention."""

from __future__ import annotations

import uuid

import pytest

from app.core.constants import AiWriteStatus, PolicyState
from app.core.idempotency import build_idempotency_key
from app.models.ai_audit_log import AiAuditLog
from app.services import agent_service
from tests.unit.agent_helpers import FakeAsyncSession, make_agent_user, make_fake_tool


def test_key_is_stable_for_same_inputs() -> None:
    a = build_idempotency_key("evt-1", "update_company_description", "c1")
    b = build_idempotency_key("evt-1", "update_company_description", "c1")
    assert a == b


def test_key_varies_by_event_tool_and_entity() -> None:
    base = build_idempotency_key("evt-1", "tool", "c1")
    assert base != build_idempotency_key("evt-2", "tool", "c1")
    assert base != build_idempotency_key("evt-1", "other", "c1")
    assert base != build_idempotency_key("evt-1", "tool", "c2")


@pytest.mark.asyncio
async def test_duplicate_committed_write_is_a_noop(monkeypatch: pytest.MonkeyPatch) -> None:
    calls: list[str] = []
    tool = make_fake_tool(calls=calls)
    company_id = uuid.uuid4()
    event_id = "evt-dup"
    key = build_idempotency_key(event_id, tool.name, str(company_id))

    monkeypatch.setattr(agent_service, "get_tool", lambda _name: tool)

    async def authorized(*_a: object, **_k: object) -> PolicyState:
        return PolicyState.AUTHORIZED

    async def existing_committed(_session: object, _key: str) -> AiAuditLog:
        return AiAuditLog(
            id=uuid.uuid4(),
            tool=tool.name,
            status=AiWriteStatus.COMMITTED,
            idempotency_key=key,
        )

    monkeypatch.setattr(agent_service.agent_policy_service, "get_effective_state", authorized)
    monkeypatch.setattr(agent_service.agent_repo, "get_ai_audit_by_key", existing_committed)

    result = await agent_service.execute_tool(
        FakeAsyncSession(),  # type: ignore[arg-type]
        agent_user=make_agent_user(),
        tool_name=tool.name,
        payload={"company_id": str(company_id), "value": "x"},
        event_id=event_id,
    )

    assert result.status == "duplicate"
    assert result.idempotency_key == key
    assert calls == []  # handler never ran
