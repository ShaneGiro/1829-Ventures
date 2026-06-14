"""Central v1 permission guard."""

from __future__ import annotations

from app.core.exceptions import PermissionDeniedError
from app.models.user import User


def require_permission(user: User, action: str, resource: str) -> bool:
    """Return True for every active authenticated human in v1."""
    if user.is_agent:
        raise PermissionDeniedError("Agent credentials cannot access human user surfaces")
    if not user.is_active or user.is_archived:
        raise PermissionDeniedError("User is not active")
    _ = (action, resource)
    return True
