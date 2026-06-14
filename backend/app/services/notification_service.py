"""Channel-agnostic notification creation and email dispatch."""

from __future__ import annotations

import html
import uuid
from datetime import UTC, datetime

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.constants import NotificationChannel
from app.integrations.sendgrid import SendGridEmailClient, get_email_client
from app.models.notification import Notification
from app.models.task import Task
from app.models.user import User
from app.repositories import notifications as notification_repo
from app.repositories import users as user_repo


def _task_link_label(task: Task) -> str:
    if task.company_id:
        return "company"
    if task.deal_id:
        return "deal"
    if task.person_id:
        return "person"
    return "task"


async def create_notification(
    session: AsyncSession,
    *,
    user_id: uuid.UUID,
    notification_type: str,
    title: str,
    body: str | None,
    channel: NotificationChannel = NotificationChannel.EMAIL,
    entity_type: str | None = None,
    entity_id: uuid.UUID | None = None,
) -> Notification:
    notification = Notification(
        user_id=user_id,
        notification_type=notification_type,
        title=title,
        body=body,
        channel=channel,
        entity_type=entity_type,
        entity_id=entity_id,
    )
    return await notification_repo.create_notification(session, notification)


async def notify_task_assignment(
    session: AsyncSession,
    *,
    task: Task,
    owner: User,
    email_client: SendGridEmailClient | None = None,
) -> Notification:
    title = f"Task assigned: {task.title}"
    body = f"You are now responsible for this {_task_link_label(task)} task."
    notification = await create_notification(
        session,
        user_id=owner.id,
        notification_type="task_assigned",
        title=title,
        body=body,
        entity_type="task",
        entity_id=task.id,
    )
    client = email_client or get_email_client()
    result = client.send_email(
        to_email=owner.email,
        subject=title,
        html_body=f"<p>{html.escape(body)}</p><p><strong>{html.escape(task.title)}</strong></p>",
    )
    notification.delivered_at = datetime.now(UTC) if result.status_code else None
    notification.delivery_meta = {
        "provider": "sendgrid",
        "message_id": result.provider_message_id,
        "status_code": result.status_code,
    }
    return notification


def render_task_digest_html(
    *,
    owner: User,
    overdue: list[Task],
    due_today: list[Task],
    upcoming: list[Task],
) -> str:
    def section(title: str, tasks: list[Task]) -> str:
        if not tasks:
            return ""
        items = "".join(
            f"<li>{html.escape(task.title)}"
            f"{' - ' + html.escape(task.description) if task.description else ''}</li>"
            for task in tasks
        )
        return f"<h2>{html.escape(title)}</h2><ul>{items}</ul>"

    greeting = html.escape(owner.full_name or owner.email)
    return (
        f"<p>{greeting}, here is your 1829 task digest.</p>"
        f"{section('Overdue', overdue)}"
        f"{section('Due today', due_today)}"
        f"{section('Upcoming', upcoming)}"
    )


async def send_task_digest(
    session: AsyncSession,
    *,
    owner: User,
    overdue: list[Task],
    due_today: list[Task],
    upcoming: list[Task],
    email_client: SendGridEmailClient | None = None,
) -> Notification | None:
    task_count = len(overdue) + len(due_today) + len(upcoming)
    if task_count == 0:
        return None

    title = f"Your 1829 task digest: {task_count} open task{'s' if task_count != 1 else ''}"
    body = (
        f"{len(overdue)} overdue, {len(due_today)} due today, "
        f"{len(upcoming)} upcoming."
    )
    notification = await create_notification(
        session,
        user_id=owner.id,
        notification_type="task_daily_digest",
        title=title,
        body=body,
        entity_type="task_digest",
    )
    client = email_client or get_email_client()
    result = client.send_email(
        to_email=owner.email,
        subject=title,
        html_body=render_task_digest_html(
            owner=owner,
            overdue=overdue,
            due_today=due_today,
            upcoming=upcoming,
        ),
    )
    notification.delivered_at = datetime.now(UTC) if result.status_code else None
    notification.delivery_meta = {
        "provider": "sendgrid",
        "message_id": result.provider_message_id,
        "status_code": result.status_code,
        "overdue": len(overdue),
        "due_today": len(due_today),
        "upcoming": len(upcoming),
    }
    return notification


async def get_owner(session: AsyncSession, owner_id: uuid.UUID) -> User | None:
    return await user_repo.get_user_by_id(session, owner_id)

