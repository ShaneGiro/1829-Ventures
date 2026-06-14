"""Small shared SQLAlchemy query helpers for repositories."""

from __future__ import annotations

import uuid
from typing import Any, TypeVar, cast

from sqlalchemy import Select, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.base import Base

ModelT = TypeVar("ModelT", bound=Base)


def active_filter(model: type[ModelT]) -> Any:
    return model.__table__.c.archived_at.is_(None)


async def get_by_id(
    session: AsyncSession,
    model: type[ModelT],
    entity_id: uuid.UUID,
    *,
    include_archived: bool = False,
) -> ModelT | None:
    stmt = select(model).where(model.__table__.c.id == entity_id)
    if not include_archived and hasattr(model, "archived_at"):
        stmt = stmt.where(active_filter(model))
    return cast("ModelT | None", await session.scalar(stmt))


async def list_rows(
    session: AsyncSession,
    model: type[ModelT],
    *,
    limit: int,
    offset: int,
    include_archived: bool = False,
    order_by: Any | None = None,
) -> list[ModelT]:
    stmt: Select[tuple[ModelT]] = select(model)
    if not include_archived and hasattr(model, "archived_at"):
        stmt = stmt.where(active_filter(model))
    default_order = model.__table__.c.created_at.desc()
    stmt = stmt.order_by(order_by if order_by is not None else default_order)
    stmt = stmt.limit(limit).offset(offset)
    return list(await session.scalars(stmt))


async def count_rows(
    session: AsyncSession,
    model: type[ModelT],
    *,
    include_archived: bool = False,
) -> int:
    stmt = select(func.count()).select_from(model)
    if not include_archived and hasattr(model, "archived_at"):
        stmt = stmt.where(active_filter(model))
    return int(await session.scalar(stmt) or 0)
