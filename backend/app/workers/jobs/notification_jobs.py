"""Notification worker jobs."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime, time, timedelta
from zoneinfo import ZoneInfo

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.constants import NotificationChannel, TaskStatus
from app.core.database import SyncSessionLocal
from app.integrations.sendgrid import get_email_client
from app.models.notification import Notification
from app.models.task import Task
from app.models.user import User
from app.services.notification_service import render_task_digest_html
from app.services.task_service import split_digest_tasks
from app.workers.celery_app import celery_app


def _open_digest_tasks(
    session: Session,
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
        .order_by(Task.due_date.asc(), Task.created_at.asc())
    )
    return list(session.scalars(stmt))


def _send_digest_for_owner(
    session: Session,
    *,
    owner: User,
    now: datetime,
    include_upcoming: bool,
) -> int:
    tz = ZoneInfo(settings.timezone)
    local_now = now.astimezone(tz)
    today_start = datetime.combine(local_now.date(), time.min, tzinfo=tz).astimezone(UTC)
    today_end = datetime.combine(local_now.date(), time.max, tzinfo=tz).astimezone(UTC)
    upcoming_end = datetime.combine(local_now.date(), time.max, tzinfo=tz) + timedelta(days=7)
    upcoming_end = upcoming_end.astimezone(UTC)
    tasks = _open_digest_tasks(
        session,
        owner_id=owner.id,
        today_end=today_end,
        upcoming_end=upcoming_end,
        include_upcoming=include_upcoming,
    )
    overdue, due_today, upcoming = split_digest_tasks(
        tasks,
        today_start=today_start,
        today_end=today_end,
        upcoming_end=upcoming_end,
    )
    task_count = len(overdue) + len(due_today) + len(upcoming)
    if task_count == 0:
        return 0

    title = f"Your 1829 task digest: {task_count} open task{'s' if task_count != 1 else ''}"
    body = f"{len(overdue)} overdue, {len(due_today)} due today, {len(upcoming)} upcoming."
    result = get_email_client().send_email(
        to_email=owner.email,
        subject=title,
        html_body=render_task_digest_html(
            owner=owner,
            overdue=overdue,
            due_today=due_today,
            upcoming=upcoming,
        ),
    )
    notification = Notification(
        user_id=owner.id,
        notification_type="task_daily_digest",
        title=title,
        body=body,
        channel=NotificationChannel.EMAIL,
        delivered_at=datetime.now(UTC) if result.status_code else None,
        delivery_meta={
            "provider": "sendgrid",
            "message_id": result.provider_message_id,
            "status_code": result.status_code,
            "overdue": len(overdue),
            "due_today": len(due_today),
            "upcoming": len(upcoming),
        },
        entity_type="task_digest",
    )
    session.add(notification)
    return task_count


@celery_app.task(name="notifications.send_daily_task_digests")
def send_daily_task_digests(include_upcoming: bool = True) -> dict[str, int]:
    """Send one daily task digest per user with assigned open due tasks."""
    now = datetime.now(UTC)
    sent = 0
    task_count = 0
    with SyncSessionLocal() as session:
        owners = list(
            session.scalars(
                select(User).where(
                    User.is_agent.is_(False),
                    User.is_active.is_(True),
                    User.archived_at.is_(None),
                )
            )
        )
        for owner in owners:
            owner_task_count = _send_digest_for_owner(
                session,
                owner=owner,
                now=now,
                include_upcoming=include_upcoming,
            )
            if owner_task_count:
                sent += 1
                task_count += owner_task_count
        session.commit()
    return {"digests_sent": sent, "tasks_included": task_count}
