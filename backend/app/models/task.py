"""Task model: first-class workflow object.

Tracks one accountable owner, creator/source (human, Ritchie, or system),
optional watchers, due date, status, priority, and completion history. Can link
to a company, person, deal, interaction, or import. Unassigned (owner NULL)
tasks appear in the shared queue.
"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import DateTime, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.constants import ActorType, TaskPriority, TaskStatus
from app.models.base import Base, SoftDeleteMixin, TimestampMixin, UUIDPrimaryKeyMixin


class Task(UUIDPrimaryKeyMixin, TimestampMixin, SoftDeleteMixin, Base):
    __tablename__ = "tasks"

    title: Mapped[str] = mapped_column(String(512), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)

    status: Mapped[TaskStatus] = mapped_column(
        String(16), default=TaskStatus.OPEN, nullable=False, index=True
    )
    priority: Mapped[TaskPriority] = mapped_column(
        String(16), default=TaskPriority.MEDIUM, nullable=False
    )
    due_date: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True, index=True
    )

    # Owner is NULL for unassigned (shared-queue) tasks.
    owner_id: Mapped[uuid.UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    # Who/what created the task.
    created_by_type: Mapped[ActorType] = mapped_column(
        String(16), default=ActorType.HUMAN, nullable=False
    )
    created_by_id: Mapped[uuid.UUID | None] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    watcher_ids: Mapped[list[Any]] = mapped_column(JSONB, default=list, nullable=False)

    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    # Optional links to any core entity.
    company_id: Mapped[uuid.UUID | None] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("companies.id", ondelete="CASCADE"), nullable=True
    )
    person_id: Mapped[uuid.UUID | None] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("people.id", ondelete="SET NULL"), nullable=True
    )
    deal_id: Mapped[uuid.UUID | None] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("deals.id", ondelete="CASCADE"), nullable=True
    )
    interaction_id: Mapped[uuid.UUID | None] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("interactions.id", ondelete="SET NULL"), nullable=True
    )
    import_batch_id: Mapped[uuid.UUID | None] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("import_batches.id", ondelete="SET NULL"), nullable=True
    )

    def __repr__(self) -> str:
        return f"<Task {self.title} status={self.status}>"
