"""Task schemas."""

from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel

from app.core.constants import ActorType, TaskPriority, TaskStatus
from app.schemas.common import SoftDeleteRead


class TaskBase(BaseModel):
    title: str
    description: str | None = None
    priority: TaskPriority = TaskPriority.MEDIUM
    due_date: datetime | None = None
    owner_id: uuid.UUID | None = None
    company_id: uuid.UUID | None = None
    person_id: uuid.UUID | None = None
    deal_id: uuid.UUID | None = None
    interaction_id: uuid.UUID | None = None


class TaskCreate(TaskBase):
    pass


class TaskUpdate(BaseModel):
    title: str | None = None
    description: str | None = None
    status: TaskStatus | None = None
    priority: TaskPriority | None = None
    due_date: datetime | None = None
    owner_id: uuid.UUID | None = None


class TaskRead(SoftDeleteRead, TaskBase):
    status: TaskStatus
    created_by_type: ActorType
    created_by_id: uuid.UUID | None = None
    watcher_ids: list[uuid.UUID] = []
    completed_at: datetime | None = None
