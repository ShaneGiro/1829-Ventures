"""Permission guard tests."""

from __future__ import annotations

import uuid

import pytest

from app.core.constants import Role
from app.core.exceptions import PermissionDeniedError
from app.core.permissions import PermissionAction, PermissionResource
from app.models.user import User
from app.services.permission_service import require_permission


def make_user(role: Role) -> User:
    return User(
        id=uuid.uuid4(),
        email=f"{role.value}@g.rit.edu",
        role=role,
        is_active=True,
        is_agent=False,
    )


@pytest.mark.parametrize(
    "role",
    [Role.ADMIN, Role.MANAGING_DIRECTOR, Role.PRINCIPAL, Role.ANALYST, Role.MEMBER],
)
def test_all_human_roles_have_equal_v1_access(role: Role) -> None:
    assert require_permission(make_user(role), "update", "company") is True


def test_agent_user_is_not_a_human_permission_subject() -> None:
    agent = make_user(Role.AGENT)
    agent.is_agent = True

    with pytest.raises(PermissionDeniedError):
        require_permission(agent, "read", "user")


@pytest.mark.parametrize("role", [Role.ADMIN, Role.MANAGING_DIRECTOR])
def test_fund_leaders_can_manage_legal_entities(role: Role) -> None:
    assert (
        require_permission(
            make_user(role), PermissionAction.MANAGE, PermissionResource.LEGAL_ENTITY
        )
        is True
    )


@pytest.mark.parametrize("role", [Role.ANALYST, Role.MEMBER])
def test_non_leaders_cannot_mutate_legal_entities(role: Role) -> None:
    with pytest.raises(PermissionDeniedError):
        require_permission(
            make_user(role), PermissionAction.UPDATE, PermissionResource.LEGAL_ENTITY
        )


@pytest.mark.parametrize("role", [Role.ANALYST, Role.MEMBER, Role.PRINCIPAL])
def test_human_fund_roles_can_read_legal_entities(role: Role) -> None:
    assert (
        require_permission(
            make_user(role), PermissionAction.READ, PermissionResource.LEGAL_ENTITY
        )
        is True
    )
