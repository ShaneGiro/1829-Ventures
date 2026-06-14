"""Typed application exception hierarchy.

Services raise these; the API layer maps them to HTTP responses in main.py. This
keeps services free of FastAPI/HTTP concerns.
"""

from __future__ import annotations


class AppError(Exception):
    """Base class for all application errors."""

    status_code: int = 500
    code: str = "internal_error"

    def __init__(self, message: str | None = None) -> None:
        self.message = message or self.__class__.__doc__ or "Application error"
        super().__init__(self.message)


class NotFoundError(AppError):
    """The requested resource was not found."""

    status_code = 404
    code = "not_found"


class ValidationError(AppError):
    """The request was understood but failed validation."""

    status_code = 422
    code = "validation_error"


class ConflictError(AppError):
    """The request conflicts with the current state of the resource."""

    status_code = 409
    code = "conflict"


class AuthenticationError(AppError):
    """Authentication is required or the provided credentials are invalid."""

    status_code = 401
    code = "authentication_error"


class PermissionDeniedError(AppError):
    """The authenticated actor is not permitted to perform this action."""

    status_code = 403
    code = "permission_denied"


class PolicyBlockedError(AppError):
    """A Ritchie tool/field is blocked by the runtime authorization policy."""

    status_code = 403
    code = "policy_blocked"


class RateLimitError(AppError):
    """The actor has exceeded the rate limit for this endpoint tier."""

    status_code = 429
    code = "rate_limited"
