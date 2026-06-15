"""Shared fakes for Ritchie agent unit tests (not collected as a test module)."""

from __future__ import annotations

import uuid
from typing import Any

from pydantic import BaseModel

from app.agent.tools import AgentTool, ToolResult
from app.core.constants import PolicyState, Role
from app.models.user import User


class FakeAsyncSession:
    """Minimal async session: add/flush/commit/rollback/get over an in-memory map.

    Agent-service tests monkeypatch the repo functions that issue `scalar`
    queries, so this only needs identity-map semantics for objects it creates.
    """

    def __init__(self) -> None:
        self.objects: dict[tuple[str, Any], Any] = {}
        self.commits = 0
        self.rollbacks = 0

    def add(self, obj: Any) -> None:
        if getattr(obj, "id", None) is None:
            obj.id = uuid.uuid4()
        self.objects[(type(obj).__name__, obj.id)] = obj

    async def flush(self) -> None:
        for obj in list(self.objects.values()):
            if getattr(obj, "id", None) is None:  # pragma: no cover - defensive
                obj.id = uuid.uuid4()

    async def commit(self) -> None:
        self.commits += 1

    async def rollback(self) -> None:
        self.rollbacks += 1

    async def get(self, model: type[Any], entity_id: Any) -> Any:
        return self.objects.get((model.__name__, entity_id))


def make_agent_user() -> User:
    return User(
        id=uuid.uuid4(),
        email="ritchie@1829.ventures",
        role=Role.AGENT,
        is_active=True,
        is_agent=True,
    )


class _DemoInput(BaseModel):
    company_id: uuid.UUID
    value: str


def make_fake_tool(
    *,
    name: str = "demo_write",
    kind: str = "write",
    default_state: PolicyState = PolicyState.AUTHORIZED,
    calls: list[str] | None = None,
) -> AgentTool:
    """A registry-shaped tool whose handler records invocation (no DB writes)."""

    async def handler(_session: Any, payload: BaseModel, _actor: User) -> ToolResult:
        if calls is not None:
            calls.append(name)
        assert isinstance(payload, _DemoInput)
        return ToolResult(
            data={"ok": True},
            entity_type="companies",
            entity_id=payload.company_id,
            old_value={"value": "old"},
            new_value={"value": payload.value},
        )

    return AgentTool(
        name=name,
        description="demo",
        kind=kind,
        input_model=_DemoInput,
        handler=handler,
        default_state=default_state,
        entity_type="companies",
    )
