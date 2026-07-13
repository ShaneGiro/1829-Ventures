"""Organization and membership schemas."""

from __future__ import annotations

import uuid

from pydantic import BaseModel, Field

from app.core.constants import OrganizationStatus, Role
from app.schemas.common import SoftDeleteRead, TimestampedRead


class OrganizationCreate(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    slug: str = Field(min_length=1, max_length=128, pattern=r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
    institutional_owner: str | None = Field(default=None, max_length=255)
    base_currency: str = Field(default="USD", min_length=3, max_length=3)
    timezone: str = Field(default="America/New_York", min_length=1, max_length=64)


class OrganizationUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=255)
    institutional_owner: str | None = Field(default=None, max_length=255)
    base_currency: str | None = Field(default=None, min_length=3, max_length=3)
    timezone: str | None = Field(default=None, min_length=1, max_length=64)
    status: OrganizationStatus | None = None


class OrganizationRead(SoftDeleteRead):
    name: str
    slug: str
    institutional_owner: str | None
    base_currency: str
    timezone: str
    status: OrganizationStatus


class OrganizationMembershipRead(TimestampedRead):
    organization_id: uuid.UUID
    user_id: uuid.UUID
    role: Role
    is_active: bool
