"""Task repository helpers."""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.constants import TaskStatus
from app.models.task import Task
from app.repositories import base


async def get_task(
    session: AsyncSession, task_id: uuid.UUID, *, include_archived: bool = False
) -> Task | None:
    return await base.get_by_id(session, Task, task_id, include_archived=include_archived)


async def list_tasks(
    session: AsyncSession,
    *,
    limit: int,
    offset: int,
    owner_id: uuid.UUID | None = None,
    status: TaskStatus | None = None,
    company_id: uuid.UUID | None = None,
    deal_id: uuid.UUID | None = None,
    include_unassigned: bool = False,
    include_archived: bool = False,
) -> list[Task]:
    stmt = select(Task)
    if not include_archived:
        stmt = stmt.where(Task.archived_at.is_(None))
    if owner_id is not None and include_unassigned:
        stmt = stmt.where(or_(Task.owner_id == owner_id, Task.owner_id.is_(None)))
    elif owner_id is not None:
        stmt = stmt.where(Task.owner_id == owner_id)
    elif include_unassigned:
        stmt = stmt.where(Task.owner_id.is_(None))
    if status is not None:
        stmt = stmt.where(Task.status == status)
    if company_id is not None:
        stmt = stmt.where(Task.company_id == company_id)
    if deal_id is not None:
        stmt = stmt.where(Task.deal_id == deal_id)
    stmt = stmt.order_by(Task.due_date.asc().nullslast(), Task.created_at.desc())
    stmt = stmt.limit(limit).offset(offset)
    return list(await session.scalars(stmt))


async def count_tasks(
    session: AsyncSession,
    *,
    owner_id: uuid.UUID | None = None,
    status: TaskStatus | None = None,
    company_id: uuid.UUID | None = None,
    deal_id: uuid.UUID | None = None,
    include_unassigned: bool = False,
    include_archived: bool = False,
) -> int:
    stmt = select(func.count()).select_from(Task)
    if not include_archived:
        stmt = stmt.where(Task.archived_at.is_(None))
    if owner_id is not None and include_unassigned:
        stmt = stmt.where(or_(Task.owner_id == owner_id, Task.owner_id.is_(None)))
    elif owner_id is not None:
        stmt = stmt.where(Task.owner_id == owner_id)
    elif include_unassigned:
        stmt = stmt.where(Task.owner_id.is_(None))
    if status is not None:
        stmt = stmt.where(Task.status == status)
    if company_id is not None:
        stmt = stmt.where(Task.company_id == company_id)
    if deal_id is not None:
        stmt = stmt.where(Task.deal_id == deal_id)
    return int(await session.scalar(stmt) or 0)


async def create_task(session: AsyncSession, task: Task) -> Task:
    session.add(task)
    await session.flush()
    return task


async def list_open_tasks_for_digest(
    session: AsyncSession,
    *,
    owner_id: uuid.UUID,
    today_end: datetime,
    upcoming_end: datetime,
    include_upcoming: bool,
) -> list[Task]:
    upper_bound = upcoming_end if include_upcoming else today_end
    stmt = (
        select(Task)
        .where(
            Task.archived_at.is_(None),
            Task.owner_id == owner_id,
            Task.status.in_([TaskStatus.OPEN, TaskStatus.IN_PROGRESS]),
            Task.due_date.is_not(None),
            Task.due_date <= upper_bound,
        )
        .order_by(Task.due_date.asc(), Task.priority.desc(), Task.created_at.asc())
    )
    return list(await session.scalars(stmt))
