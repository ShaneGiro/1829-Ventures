"""User schemas."""

from __future__ import annotations

from pydantic import BaseModel, EmailStr

from app.core.constants import Role
from app.schemas.common import SoftDeleteRead


class UserBase(BaseModel):
    email: EmailStr
    full_name: str | None = None
    avatar_url: str | None = None


class UserCreate(UserBase):
    role: Role = Role.MEMBER


class UserUpdate(BaseModel):
    full_name: str | None = None
    avatar_url: str | None = None
    role: Role | None = None
    is_active: bool | None = None


class UserRead(SoftDeleteRead, UserBase):
    role: Role
    is_active: bool
    is_agent: bool
