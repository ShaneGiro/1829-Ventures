"""Permission constants and helpers."""

from __future__ import annotations

from enum import StrEnum


class PermissionAction(StrEnum):
    READ = "read"
    CREATE = "create"
    UPDATE = "update"
    ARCHIVE = "archive"
    MANAGE = "manage"


class PermissionResource(StrEnum):
    AUTH = "auth"
    USER = "user"
    CRM = "crm"
