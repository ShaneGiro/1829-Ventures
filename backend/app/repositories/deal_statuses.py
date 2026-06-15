"""Repository helpers for configurable deal pipeline stages."""

from __future__ import annotations

import uuid
from typing import Any, cast

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.constants import SEED_DEAL_STATUSES
from app.models.deal_status import DealStatus


async def list_deal_statuses(
    session: AsyncSession,
    *,
    limit: int,
    offset: int,
) -> list[DealStatus]:
    stmt = (
        select(DealStatus)
        .order_by(DealStatus.sort_order, DealStatus.name)
        .limit(limit)
        .offset(offset)
    )
    return list(await session.scalars(stmt))


async def count_deal_statuses(session: AsyncSession) -> int:
    stmt = select(func.count()).select_from(DealStatus)
    return int(await session.scalar(stmt) or 0)


async def get_deal_status(session: AsyncSession, status_id: uuid.UUID) -> DealStatus | None:
    stmt = select(DealStatus).where(DealStatus.id == status_id)
    return cast("DealStatus | None", await session.scalar(stmt))


async def get_deal_status_by_name(session: AsyncSession, name: str) -> DealStatus | None:
    stmt = select(DealStatus).where(func.lower(DealStatus.name) == name.strip().lower())
    return cast("DealStatus | None", await session.scalar(stmt))


async def create_deal_status(session: AsyncSession, **values: Any) -> DealStatus:
    status = DealStatus(**values)
    session.add(status)
    await session.flush()
    return status


async def seed_default_deal_statuses(session: AsyncSession) -> list[DealStatus]:
    statuses: list[DealStatus] = []
    for index, name in enumerate(SEED_DEAL_STATUSES, start=1):
        status = await get_deal_status_by_name(session, name)
        if status is None:
            status = DealStatus(
                name=name,
                sort_order=index,
                is_system=True,
                is_terminal=name == "Closed/Invested",
            )
            session.add(status)
        elif status.is_system and status.sort_order != index:
            # Keep system stages aligned with SEED_DEAL_STATUSES order even if
            # they were seeded under a previous ordering.
            status.sort_order = index
        statuses.append(status)
    await session.flush()
    return statuses
