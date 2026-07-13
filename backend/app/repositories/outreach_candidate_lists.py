"""Persistence helpers for durable outreach-candidate lists."""

from __future__ import annotations

import uuid
from typing import cast

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.constants import OutreachCandidateListStatus
from app.models.outreach_candidate_list import (
    OutreachCandidateList,
    OutreachCandidateListItem,
)


async def create_list(
    session: AsyncSession, candidate_list: OutreachCandidateList
) -> OutreachCandidateList:
    session.add(candidate_list)
    await session.flush()
    return candidate_list


async def get_list(
    session: AsyncSession,
    list_id: uuid.UUID,
    *,
    include_archived: bool = False,
    with_items: bool = False,
) -> OutreachCandidateList | None:
    stmt = select(OutreachCandidateList).where(OutreachCandidateList.id == list_id)
    if not include_archived:
        stmt = stmt.where(OutreachCandidateList.status != OutreachCandidateListStatus.ARCHIVED)
    if with_items:
        stmt = stmt.options(selectinload(OutreachCandidateList.items))
    return cast("OutreachCandidateList | None", await session.scalar(stmt))


async def list_lists(
    session: AsyncSession,
    *,
    limit: int,
    offset: int,
    include_archived: bool = False,
) -> list[OutreachCandidateList]:
    stmt = select(OutreachCandidateList)
    if not include_archived:
        stmt = stmt.where(OutreachCandidateList.status != OutreachCandidateListStatus.ARCHIVED)
    stmt = stmt.order_by(OutreachCandidateList.updated_at.desc()).limit(limit).offset(offset)
    return list(await session.scalars(stmt))


async def count_lists(session: AsyncSession, *, include_archived: bool = False) -> int:
    stmt = select(func.count()).select_from(OutreachCandidateList)
    if not include_archived:
        stmt = stmt.where(OutreachCandidateList.status != OutreachCandidateListStatus.ARCHIVED)
    return int(await session.scalar(stmt) or 0)


async def get_item(
    session: AsyncSession, *, list_id: uuid.UUID, item_id: uuid.UUID
) -> OutreachCandidateListItem | None:
    stmt = select(OutreachCandidateListItem).where(
        OutreachCandidateListItem.id == item_id,
        OutreachCandidateListItem.list_id == list_id,
    )
    return cast("OutreachCandidateListItem | None", await session.scalar(stmt))


async def get_item_by_company(
    session: AsyncSession, *, list_id: uuid.UUID, company_id: uuid.UUID
) -> OutreachCandidateListItem | None:
    stmt = select(OutreachCandidateListItem).where(
        OutreachCandidateListItem.list_id == list_id,
        OutreachCandidateListItem.company_id == company_id,
    )
    return cast("OutreachCandidateListItem | None", await session.scalar(stmt))


async def create_item(
    session: AsyncSession, item: OutreachCandidateListItem
) -> OutreachCandidateListItem:
    session.add(item)
    await session.flush()
    return item
