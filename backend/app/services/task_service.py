"""Task business rules: assignment, completion, queues, and digests."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime, time, timedelta
from zoneinfo import ZoneInfo

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.audit import actor_from_user
from app.core.config import settings
from app.core.constants import ActorType, TaskStatus
from app.core.exceptions import NotFoundError, ValidationError
from app.models.task import Task
from app.models.user import User
from app.repositories import tasks as task_repo
from app.repositories import users as user_repo
from app.schemas.task import TaskComplete, TaskCreate, TaskUpdate
from app.services import audit_service, notification_service


def _history_entry(actor: User, note: str | None = None) -> dict[str, str | None]:
    return {
        "completed_at": datetime.now(UTC).isoformat(),
        "completed_by_id": str(actor.id),
        "note": note,
    }


async def _validate_owner(session: AsyncSession, owner_id: uuid.UUID | None) -> User | None:
    if owner_id is None:
        return None
    owner = await user_repo.get_user_by_id(session, owner_id)
    if owner is None:
        raise ValidationError("Task owner does not exist")
    return owner


async def get_task(
    session: AsyncSession, task_id: uuid.UUID, *, include_archived: bool = False
) -> Task:
    task = await task_repo.get_task(session, task_id, include_archived=include_archived)
    if task is None:
        raise NotFoundError("Task not found")
    return task


async def create_task(session: AsyncSession, payload: TaskCreate, actor: User) -> Task:
    owner = await _validate_owner(session, payload.owner_id)
    task = Task(
        **payload.model_dump(exclude={"watcher_ids"}),
        watcher_ids=[str(watcher_id) for watcher_id in payload.watcher_ids],
        created_by_type=ActorType.AGENT if actor.is_agent else ActorType.HUMAN,
        created_by_id=actor.id,
    )
    await task_repo.create_task(session, task)
    await audit_service.record_create(session, actor=actor_from_user(actor), entity=task)
    if owner is not None:
        await notification_service.notify_task_assignment(session, task=task, owner=owner)
    await session.commit()
    await session.refresh(task)
    return task


async def update_task(
    session: AsyncSession, task_id: uuid.UUID, payload: TaskUpdate, actor: User
) -> Task:
    task = await get_task(session, task_id)
    updates = payload.model_dump(exclude_unset=True)
    new_owner: User | None = None
    if "owner_id" in updates:
        new_owner = await _validate_owner(session, updates["owner_id"])
    changes: dict[str, tuple[object, object]] = {}
    for field, value in updates.items():
        if field == "watcher_ids" and value is not None:
            value = [str(watcher_id) for watcher_id in value]
        old_value = getattr(task, field)
        if old_value != value:
            changes[field] = (old_value, value)
            setattr(task, field, value)
    if changes:
        await audit_service.record_update(
            session, actor=actor_from_user(actor), entity=task, changes=changes
        )
        if "owner_id" in changes and new_owner is not None:
            await notification_service.notify_task_assignment(
                session, task=task, owner=new_owner
            )
    await session.commit()
    await session.refresh(task)
    return task


async def reassign_task(
    session: AsyncSession, task_id: uuid.UUID, owner_id: uuid.UUID | None, actor: User
) -> Task:
    task = await get_task(session, task_id)
    old_owner_id = task.owner_id
    new_owner = await _validate_owner(session, owner_id)
    task.owner_id = owner_id
    if old_owner_id != owner_id:
        await audit_service.record_update(
            session,
            actor=actor_from_user(actor),
            entity=task,
            changes={"owner_id": (old_owner_id, owner_id)},
            reason="task_reassigned",
        )
        if new_owner is not None:
            await notification_service.notify_task_assignment(
                session, task=task, owner=new_owner
            )
    await session.commit()
    await session.refresh(task)
    return task


async def complete_task(
    session: AsyncSession, task_id: uuid.UUID, payload: TaskComplete, actor: User
) -> Task:
    task = await get_task(session, task_id)
    now = datetime.now(UTC)
    old_status = task.status
    old_completed_at = task.completed_at
    old_completed_by_id = task.completed_by_id
    task.status = TaskStatus.COMPLETED
    task.completed_at = now
    task.completed_by_id = actor.id
    history = task.completion_history or []
    task.completion_history = [*history, _history_entry(actor, payload.completion_note)]
    await audit_service.record_update(
        session,
        actor=actor_from_user(actor),
        entity=task,
        changes={
            "status": (old_status, task.status),
            "completed_at": (old_completed_at, task.completed_at),
            "completed_by_id": (old_completed_by_id, task.completed_by_id),
        },
        reason="task_completed",
    )
    await session.commit()
    await session.refresh(task)
    return task


async def archive_task(session: AsyncSession, task_id: uuid.UUID, actor: User) -> Task:
    task = await get_task(session, task_id)
    old_snapshot = audit_service.snapshot_model(task)
    task.archived_at = datetime.now(UTC)
    await audit_service.record_archive(
        session,
        actor=actor_from_user(actor),
        entity=task,
        old_snapshot=old_snapshot,
    )
    await session.commit()
    await session.refresh(task)
    return task


def split_digest_tasks(
    tasks: list[Task],
    *,
    today_start: datetime,
    today_end: datetime,
    upcoming_end: datetime,
) -> tuple[list[Task], list[Task], list[Task]]:
    overdue: list[Task] = []
    due_today: list[Task] = []
    upcoming: list[Task] = []
    for task in tasks:
        if task.due_date is None:
            continue
        due_date = task.due_date
        if due_date < today_start:
            overdue.append(task)
        elif due_date <= today_end:
            due_today.append(task)
        elif due_date <= upcoming_end:
            upcoming.append(task)
    return overdue, due_today, upcoming


async def select_digest_tasks(
    session: AsyncSession,
    *,
    owner_id: uuid.UUID,
    now: datetime | None = None,
    include_upcoming: bool = True,
) -> tuple[list[Task], list[Task], list[Task]]:
    tz = ZoneInfo(settings.timezone)
    current = now.astimezone(tz) if now is not None else datetime.now(tz)
    today_start = datetime.combine(current.date(), time.min, tzinfo=tz)
    today_end = datetime.combine(current.date(), time.max, tzinfo=tz)
    upcoming_end = today_end + timedelta(days=7)
    tasks = await task_repo.list_open_tasks_for_digest(
        session,
        owner_id=owner_id,
        today_end=today_end.astimezone(UTC),
        upcoming_end=upcoming_end.astimezone(UTC),
        include_upcoming=include_upcoming,
    )
    return split_digest_tasks(
        tasks,
        today_start=today_start.astimezone(UTC),
        today_end=today_end.astimezone(UTC),
        upcoming_end=upcoming_end.astimezone(UTC),
    )
