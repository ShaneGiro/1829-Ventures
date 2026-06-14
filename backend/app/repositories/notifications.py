"""Notification repository helpers."""

from __future__ import annotations

import uuid

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.notification import Notification


async def create_notification(session: AsyncSession, notification: Notification) -> Notification:
    session.add(notification)
    await session.flush()
    return notification


async def list_notifications(
    session: AsyncSession,
    *,
    user_id: uuid.UUID,
    limit: int,
    offset: int,
    unread_only: bool = False,
) -> list[Notification]:
    stmt = select(Notification).where(Notification.user_id == user_id)
    if unread_only:
        stmt = stmt.where(Notification.is_read.is_(False))
    stmt = stmt.order_by(Notification.created_at.desc()).limit(limit).offset(offset)
    return list(await session.scalars(stmt))


async def count_notifications(
    session: AsyncSession, *, user_id: uuid.UUID, unread_only: bool = False
) -> int:
    stmt = select(func.count()).select_from(Notification).where(Notification.user_id == user_id)
    if unread_only:
        stmt = stmt.where(Notification.is_read.is_(False))
    return int(await session.scalar(stmt) or 0)
