"""Auth dependency behavior tests."""

from __future__ import annotations

import uuid

import pytest

from app.core.constants import Role
from app.core.exceptions import PermissionDeniedError
from app.models.user import User
from app.services import auth_service


def human_user() -> User:
    return User(
        id=uuid.uuid4(),
        email="human@g.rit.edu",
        role=Role.MEMBER,
        is_active=True,
        is_agent=False,
    )


@pytest.mark.asyncio
async def test_human_dependency_rejects_valid_agent_key(monkeypatch: pytest.MonkeyPatch) -> None:
    from app.core.dependencies import get_current_human_user

    async def agent_auth(_db: object, _token: str) -> User:
        return User(
            id=uuid.uuid4(),
            email=auth_service.AGENT_EMAIL,
            role=Role.AGENT,
            is_active=True,
            is_agent=True,
        )

    monkeypatch.setattr(auth_service, "authenticate_agent_api_key", agent_auth)

    with pytest.raises(PermissionDeniedError):
        await get_current_human_user(
            None,  # type: ignore[arg-type]
            authorization="Bearer valid-agent-key",
            access_token=None,
        )


@pytest.mark.asyncio
async def test_human_dependency_accepts_human_jwt(monkeypatch: pytest.MonkeyPatch) -> None:
    from app.core.dependencies import get_current_human_user

    user = human_user()

    async def not_agent(_db: object, _token: str) -> None:
        raise auth_service.AuthenticationError("not an agent key")

    async def jwt_auth(_db: object, token: str) -> User:
        assert token == "jwt-token"
        return user

    monkeypatch.setattr(auth_service, "authenticate_agent_api_key", not_agent)
    monkeypatch.setattr(auth_service, "authenticate_jwt", jwt_auth)

    assert (
        await get_current_human_user(
            None,  # type: ignore[arg-type]
            authorization="Bearer jwt-token",
            access_token=None,
        )
    ) is user
