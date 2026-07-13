"""User model: authenticated human users and Ritchie's agent identity.

Humans authenticate via Google OAuth; Ritchie authenticates via a scoped API key
(only the key hash is stored). The `role` column exists from day one for future
permission work but is not enforced in v1.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import Boolean, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.constants import Role
from app.models.base import Base, SoftDeleteMixin, TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from app.models.organization import OrganizationMembership


class User(UUIDPrimaryKeyMixin, TimestampMixin, SoftDeleteMixin, Base):
    __tablename__ = "users"

    email: Mapped[str] = mapped_column(String(320), unique=True, index=True, nullable=False)
    full_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    avatar_url: Mapped[str | None] = mapped_column(String(1024), nullable=True)

    # Role exists for future permissions; v1 grants all humans equal access.
    role: Mapped[Role] = mapped_column(String(32), default=Role.MEMBER, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    # Set only for the Ritchie agent identity; humans have no API key.
    is_agent: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    api_key_hash: Mapped[str | None] = mapped_column(String(128), nullable=True, index=True)

    organization_memberships: Mapped[list[OrganizationMembership]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<User {self.email} role={self.role}>"
