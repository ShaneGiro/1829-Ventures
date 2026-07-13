"""Central v1 permission guard."""

from __future__ import annotations

from app.core.constants import Role
from app.core.exceptions import PermissionDeniedError
from app.core.permissions import PermissionAction, PermissionResource
from app.models.user import User

_SCOPED_FUND_RESOURCES = {
    PermissionResource.ORGANIZATION,
    PermissionResource.LEGAL_ENTITY,
    PermissionResource.FUND_OPERATIONS,
}

_FUND_ROLE_ACTIONS: dict[Role, set[PermissionAction]] = {
    Role.ADMIN: set(PermissionAction),
    Role.MANAGING_DIRECTOR: set(PermissionAction),
    Role.PRINCIPAL: {
        PermissionAction.READ,
        PermissionAction.CREATE,
        PermissionAction.UPDATE,
    },
    Role.ANALYST: {PermissionAction.READ},
    Role.MEMBER: {PermissionAction.READ},
    Role.AGENT: set(),
}


def require_permission(user: User, action: str, resource: str) -> bool:
    """Enforce fund-operation roles while preserving v1 CRM access."""
    if user.is_agent:
        raise PermissionDeniedError("Agent credentials cannot access human user surfaces")
    if not user.is_active or user.is_archived:
        raise PermissionDeniedError("User is not active")

    try:
        permission_resource = PermissionResource(resource)
    except ValueError:
        # Preserve v1's fine-grained string call sites until they are migrated.
        return True

    if permission_resource in _SCOPED_FUND_RESOURCES:
        try:
            permission_action = PermissionAction(action)
        except ValueError as exc:
            raise PermissionDeniedError("Unknown permission action") from exc
        allowed = _FUND_ROLE_ACTIONS.get(user.role, set())
        if permission_action not in allowed:
            raise PermissionDeniedError(
                f"Role {user.role} cannot {permission_action} {permission_resource}"
            )
    return True
