"""Deal repository helpers."""

from __future__ import annotations

import uuid
from collections.abc import Sequence
from datetime import datetime
from typing import Any, cast

from sqlalchemy import Select, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.company import Company
from app.models.deal import Deal
from app.models.diligence_checklist_item import DiligenceChecklistItem
from app.models.rubric import Rubric
from app.models.tag import Tag, company_tags
from app.models.task import Task


def _deal_options(stmt: Select[tuple[Deal]]) -> Select[tuple[Deal]]:
    return stmt.options(selectinload(Deal.rubric), selectinload(Deal.diligence_items))


async def get_company(session: AsyncSession, company_id: uuid.UUID) -> Company | None:
    stmt = select(Company).where(Company.id == company_id, Company.archived_at.is_(None))
    return cast("Company | None", await session.scalar(stmt))


async def get_deal(session: AsyncSession, deal_id: uuid.UUID) -> Deal | None:
    stmt = _deal_options(select(Deal).where(Deal.id == deal_id, Deal.archived_at.is_(None)))
    return cast("Deal | None", await session.scalar(stmt))


async def list_deals(
    session: AsyncSession,
    *,
    limit: int,
    offset: int,
    company_id: uuid.UUID | None = None,
) -> list[Deal]:
    stmt = select(Deal).where(Deal.archived_at.is_(None))
    if company_id is not None:
        stmt = stmt.where(Deal.company_id == company_id)
    stmt = _deal_options(stmt.order_by(Deal.created_at.desc()).limit(limit).offset(offset))
    return list(await session.scalars(stmt))


async def count_deals(session: AsyncSession, *, company_id: uuid.UUID | None = None) -> int:
    stmt = select(func.count()).select_from(Deal).where(Deal.archived_at.is_(None))
    if company_id is not None:
        stmt = stmt.where(Deal.company_id == company_id)
    return int(await session.scalar(stmt) or 0)


async def get_latest_deal_for_company(session: AsyncSession, company_id: uuid.UUID) -> Deal | None:
    stmt = _deal_options(
        select(Deal)
        .where(Deal.company_id == company_id, Deal.archived_at.is_(None))
        .order_by(Deal.created_at.desc())
        .limit(1)
    )
    return cast("Deal | None", await session.scalar(stmt))


async def create_deal(session: AsyncSession, **values: Any) -> Deal:
    deal = Deal(**values)
    session.add(deal)
    await session.flush()
    return deal


async def create_rubric(session: AsyncSession, deal_id: uuid.UUID) -> Rubric:
    rubric = Rubric(deal_id=deal_id)
    session.add(rubric)
    await session.flush()
    return rubric


async def get_rubric_for_deal(session: AsyncSession, deal_id: uuid.UUID) -> Rubric | None:
    stmt = select(Rubric).where(Rubric.deal_id == deal_id)
    return cast("Rubric | None", await session.scalar(stmt))


async def create_diligence_items(
    session: AsyncSession,
    *,
    deal_id: uuid.UUID,
    labels: Sequence[str],
) -> list[DiligenceChecklistItem]:
    items = [
        DiligenceChecklistItem(deal_id=deal_id, label=label, sort_order=index)
        for index, label in enumerate(labels, start=1)
    ]
    session.add_all(items)
    await session.flush()
    return items


async def list_diligence_items(
    session: AsyncSession,
    deal_id: uuid.UUID,
) -> list[DiligenceChecklistItem]:
    stmt = (
        select(DiligenceChecklistItem)
        .where(DiligenceChecklistItem.deal_id == deal_id)
        .order_by(DiligenceChecklistItem.sort_order, DiligenceChecklistItem.created_at)
    )
    return list(await session.scalars(stmt))


async def get_diligence_item(
    session: AsyncSession,
    *,
    deal_id: uuid.UUID,
    item_id: uuid.UUID,
) -> DiligenceChecklistItem | None:
    stmt = select(DiligenceChecklistItem).where(
        DiligenceChecklistItem.id == item_id,
        DiligenceChecklistItem.deal_id == deal_id,
    )
    return cast("DiligenceChecklistItem | None", await session.scalar(stmt))


async def get_or_create_pass_reason_tag(session: AsyncSession, name: str) -> Tag:
    from app.core.constants import TagKind

    normalized = name.strip().lower()
    stmt = select(Tag).where(Tag.name == normalized, Tag.kind == TagKind.PASS_REASON)
    tag = await session.scalar(stmt)
    if tag is not None:
        return tag
    tag = Tag(name=normalized, kind=TagKind.PASS_REASON)
    session.add(tag)
    await session.flush()
    return tag


async def attach_tag_to_company(
    session: AsyncSession,
    *,
    company_id: uuid.UUID,
    tag_id: uuid.UUID,
) -> None:
    exists_stmt = select(company_tags.c.tag_id).where(
        company_tags.c.company_id == company_id,
        company_tags.c.tag_id == tag_id,
    )
    if await session.scalar(exists_stmt) is not None:
        return
    await session.execute(company_tags.insert().values(company_id=company_id, tag_id=tag_id))


async def create_task(session: AsyncSession, **values: Any) -> Task:
    task = Task(**values)
    session.add(task)
    await session.flush()
    return task


async def list_due_monitor_tasks(session: AsyncSession, due_at: datetime) -> list[Task]:
    from app.core.constants import TaskStatus

    stmt = select(Task).where(
        Task.status == TaskStatus.OPEN,
        Task.due_date <= due_at,
        Task.archived_at.is_(None),
        Task.company_id.is_not(None),
    )
    return list(await session.scalars(stmt))
