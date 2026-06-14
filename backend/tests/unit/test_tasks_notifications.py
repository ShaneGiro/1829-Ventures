"""Agent 07 task and notification service tests."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock

import pytest

from app.core.constants import TaskStatus
from app.integrations.sendgrid import EmailDeliveryResult
from app.models.task import Task
from app.models.user import User
from app.schemas.task import TaskComplete, TaskCreate
from app.services import notification_service, task_service


class FakeSession:
    def __init__(self) -> None:
        self.added: list[object] = []
        self.committed = False

    def add(self, obj: object) -> None:
        self.added.append(obj)

    async def flush(self) -> None:
        return None

    async def commit(self) -> None:
        self.committed = True

    async def refresh(self, _obj: object) -> None:
        return None


class FakeEmailClient:
    def __init__(self) -> None:
        self.sent_to: list[str] = []

    def send_email(self, *, to_email: str, subject: str, html_body: str) -> EmailDeliveryResult:
        assert subject
        assert html_body
        self.sent_to.append(to_email)
        return EmailDeliveryResult(provider_message_id="msg-1", status_code=202)


def user(email: str = "owner@g.rit.edu") -> User:
    return User(id=uuid.uuid4(), email=email, full_name="Owner")


@pytest.mark.asyncio
async def test_task_create_notifies_assigned_owner(monkeypatch: pytest.MonkeyPatch) -> None:
    actor = user("creator@g.rit.edu")
    owner = user()
    session = FakeSession()

    async def create_task(_session: FakeSession, task: Task) -> Task:
        task.id = uuid.uuid4()
        return task

    monkeypatch.setattr(task_service.user_repo, "get_user_by_id", AsyncMock(return_value=owner))
    monkeypatch.setattr(task_service.task_repo, "create_task", create_task)
    monkeypatch.setattr(task_service.audit_service, "record_create", AsyncMock())
    notify = AsyncMock()
    monkeypatch.setattr(task_service.notification_service, "notify_task_assignment", notify)

    task = await task_service.create_task(
        session,
        TaskCreate(title="Follow up", owner_id=owner.id, watcher_ids=[actor.id]),
        actor,
    )

    assert task.owner_id == owner.id
    assert task.created_by_id == actor.id
    assert task.watcher_ids == [str(actor.id)]
    notify.assert_awaited_once_with(session, task=task, owner=owner)
    assert session.committed is True


@pytest.mark.asyncio
async def test_task_reassignment_notifies_new_owner(monkeypatch: pytest.MonkeyPatch) -> None:
    actor = user("creator@g.rit.edu")
    new_owner = user("new-owner@g.rit.edu")
    task = Task(id=uuid.uuid4(), title="Review deck", owner_id=uuid.uuid4())
    session = FakeSession()

    monkeypatch.setattr(task_service, "get_task", AsyncMock(return_value=task))
    monkeypatch.setattr(task_service.user_repo, "get_user_by_id", AsyncMock(return_value=new_owner))
    monkeypatch.setattr(task_service.audit_service, "record_update", AsyncMock())
    notify = AsyncMock()
    monkeypatch.setattr(task_service.notification_service, "notify_task_assignment", notify)

    updated = await task_service.reassign_task(session, task.id, new_owner.id, actor)

    assert updated.owner_id == new_owner.id
    notify.assert_awaited_once_with(session, task=task, owner=new_owner)
    assert session.committed is True


@pytest.mark.asyncio
async def test_complete_task_records_completion_history(monkeypatch: pytest.MonkeyPatch) -> None:
    actor = user()
    task = Task(id=uuid.uuid4(), title="Call founder", status=TaskStatus.OPEN)
    session = FakeSession()

    monkeypatch.setattr(task_service, "get_task", AsyncMock(return_value=task))
    monkeypatch.setattr(task_service.audit_service, "record_update", AsyncMock())

    completed = await task_service.complete_task(
        session,
        task.id,
        TaskComplete(completion_note="Left voicemail"),
        actor,
    )

    assert completed.status == TaskStatus.COMPLETED
    assert completed.completed_by_id == actor.id
    assert completed.completion_history[0]["note"] == "Left voicemail"
    assert session.committed is True


def test_digest_selection_splits_overdue_due_today_and_upcoming() -> None:
    now = datetime(2026, 6, 14, 14, tzinfo=UTC)
    tasks = [
        Task(id=uuid.uuid4(), title="Overdue", due_date=now - timedelta(days=1)),
        Task(id=uuid.uuid4(), title="Today", due_date=now + timedelta(hours=1)),
        Task(id=uuid.uuid4(), title="Upcoming", due_date=now + timedelta(days=3)),
    ]

    overdue, due_today, upcoming = task_service.split_digest_tasks(
        tasks,
        today_start=datetime(2026, 6, 14, 0, tzinfo=UTC),
        today_end=datetime(2026, 6, 14, 23, 59, 59, tzinfo=UTC),
        upcoming_end=datetime(2026, 6, 21, 23, 59, 59, tzinfo=UTC),
    )

    assert [task.title for task in overdue] == ["Overdue"]
    assert [task.title for task in due_today] == ["Today"]
    assert [task.title for task in upcoming] == ["Upcoming"]


@pytest.mark.asyncio
async def test_task_assignment_notification_sends_email_and_records_delivery() -> None:
    owner = user()
    task = Task(id=uuid.uuid4(), title="Review notes")
    session = FakeSession()
    email_client = FakeEmailClient()

    notification = await notification_service.notify_task_assignment(
        session,
        task=task,
        owner=owner,
        email_client=email_client,
    )

    assert notification.notification_type == "task_assigned"
    assert notification.delivery_meta["status_code"] == 202
    assert email_client.sent_to == [owner.email]
