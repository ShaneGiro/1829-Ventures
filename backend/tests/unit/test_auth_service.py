"""Auth service unit tests."""

from __future__ import annotations

import uuid

import pytest

from app.core.constants import Role
from app.core.exceptions import AuthenticationError, PermissionDeniedError
from app.core.security import hash_api_key
from app.integrations.google_oauth import GoogleProfile
from app.models.user import User
from app.services import auth_service


class FakeSession:
    def __init__(self) -> None:
        self.committed = False

    async def commit(self) -> None:
        self.committed = True

    async def flush(self) -> None:
        return None


def make_user(*, is_agent: bool = False, is_active: bool = True) -> User:
    return User(
        id=uuid.uuid4(),
        email="user@g.rit.edu" if not is_agent else auth_service.AGENT_EMAIL,
        full_name="Test User",
        role=Role.AGENT if is_agent else Role.MEMBER,
        is_agent=is_agent,
        is_active=is_active,
    )


def test_allowed_domain_accepts_g_rit() -> None:
    assert auth_service.is_allowed_email("founder@g.rit.edu") is True


def test_allowed_domain_accepts_rit_domain_case_insensitive() -> None:
    assert auth_service.is_allowed_email("Analyst@RIT.EDU") is True


def test_allowed_domain_rejects_lookalike_domain() -> None:
    assert auth_service.is_allowed_email("person@g.rit.edu.example.com") is False


@pytest.mark.asyncio
async def test_oauth_profile_rejects_ineligible_domain(monkeypatch: pytest.MonkeyPatch) -> None:
    async def fail_if_called(*_args: object, **_kwargs: object) -> User:
        raise AssertionError("ineligible profile should not create a user")

    monkeypatch.setattr(auth_service.user_repo, "upsert_human_user", fail_if_called)

    with pytest.raises(PermissionDeniedError):
        await auth_service.authenticate_oauth_profile(
            FakeSession(),  # type: ignore[arg-type]
            GoogleProfile(email="person@example.com"),
        )


@pytest.mark.asyncio
async def test_agent_key_auth_accepts_configured_env_key(monkeypatch: pytest.MonkeyPatch) -> None:
    async def no_db_agent(*_args: object, **_kwargs: object) -> None:
        return None

    monkeypatch.setattr(auth_service.settings, "agent_api_key", "secret-agent-key")
    monkeypatch.setattr(auth_service.user_repo, "get_agent_by_api_key_hash", no_db_agent)

    user = await auth_service.authenticate_agent_api_key(
        FakeSession(),  # type: ignore[arg-type]
        "secret-agent-key",
    )

    assert user.is_agent is True
    assert user.role == Role.AGENT


@pytest.mark.asyncio
async def test_agent_key_auth_accepts_database_hash(monkeypatch: pytest.MonkeyPatch) -> None:
    agent = make_user(is_agent=True)
    agent.api_key_hash = hash_api_key("stored-key")

    async def db_agent(*_args: object, **_kwargs: object) -> User:
        return agent

    monkeypatch.setattr(auth_service.user_repo, "get_agent_by_api_key_hash", db_agent)

    assert (
        await auth_service.authenticate_agent_api_key(
            FakeSession(),  # type: ignore[arg-type]
            "stored-key",
        )
        is agent
    )


@pytest.mark.asyncio
async def test_agent_key_auth_rejects_invalid_key(monkeypatch: pytest.MonkeyPatch) -> None:
    async def no_db_agent(*_args: object, **_kwargs: object) -> None:
        return None

    monkeypatch.setattr(auth_service.settings, "agent_api_key", "secret-agent-key")
    monkeypatch.setattr(auth_service.user_repo, "get_agent_by_api_key_hash", no_db_agent)

    with pytest.raises(AuthenticationError):
        await auth_service.authenticate_agent_api_key(
            FakeSession(),  # type: ignore[arg-type]
            "wrong-key",
        )
