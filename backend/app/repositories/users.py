"""User repository helpers."""

from __future__ import annotations

import uuid
from typing import cast

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.constants import DEFAULT_RIT_ORGANIZATION_ID
from app.models.organization import OrganizationMembership
from app.models.user import User


async def get_user_by_id(session: AsyncSession, user_id: uuid.UUID) -> User | None:
    stmt = select(User).where(User.id == user_id, User.archived_at.is_(None))
    return cast("User | None", await session.scalar(stmt))


async def get_user_by_email(session: AsyncSession, email: str) -> User | None:
    stmt = select(User).where(User.email == email.lower(), User.archived_at.is_(None))
    return cast("User | None", await session.scalar(stmt))


async def get_agent_by_api_key_hash(session: AsyncSession, api_key_hash: str) -> User | None:
    stmt = select(User).where(
        User.api_key_hash == api_key_hash,
        User.is_agent.is_(True),
        User.is_active.is_(True),
        User.archived_at.is_(None),
    )
    return cast("User | None", await session.scalar(stmt))


async def list_users(session: AsyncSession, *, limit: int, offset: int) -> list[User]:
    stmt = (
        select(User)
        .where(User.is_agent.is_(False), User.archived_at.is_(None))
        .order_by(User.email)
        .limit(limit)
        .offset(offset)
    )
    return list(await session.scalars(stmt))


async def count_human_users(session: AsyncSession) -> int:
    stmt = (
        select(func.count())
        .select_from(User)
        .where(
            User.is_agent.is_(False),
            User.archived_at.is_(None),
        )
    )
    return int(await session.scalar(stmt) or 0)


async def upsert_human_user(
    session: AsyncSession,
    *,
    email: str,
    full_name: str | None,
    avatar_url: str | None,
) -> User:
    normalized_email = email.lower()
    user = await get_user_by_email(session, normalized_email)
    if user is None:
        user = User(email=normalized_email, full_name=full_name, avatar_url=avatar_url)
        session.add(user)
    else:
        user.full_name = full_name or user.full_name
        user.avatar_url = avatar_url or user.avatar_url
        user.is_active = True
    await session.flush()
    return user


async def ensure_default_organization_membership(
    session: AsyncSession, user: User
) -> OrganizationMembership:
    organization_id = uuid.UUID(DEFAULT_RIT_ORGANIZATION_ID)
    stmt = select(OrganizationMembership).where(
        OrganizationMembership.organization_id == organization_id,
        OrganizationMembership.user_id == user.id,
    )
    membership = await session.scalar(stmt)
    if membership is None:
        membership = OrganizationMembership(
            organization_id=organization_id,
            user_id=user.id,
            role=user.role,
            is_active=True,
        )
        session.add(membership)
    else:
        membership.role = user.role
        membership.is_active = user.is_active
    await session.flush()
    return membership
