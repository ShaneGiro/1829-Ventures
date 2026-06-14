"""Notification model: in-app/API feed + delivery records.

Designed from day one to support an unread-count and feed endpoint so the v2
in-app bell is an additive UI layer with no schema migration. v1 delivery is
SendGrid email; the channel column reserves the Slack adapter slot.
"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import Boolean, DateTime, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.constants import NotificationChannel
from app.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class Notification(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "notifications"

    user_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    notification_type: Mapped[str] = mapped_column(String(64), nullable=False)
    title: Mapped[str] = mapped_column(String(512), nullable=False)
    body: Mapped[str | None] = mapped_column(Text, nullable=True)

    channel: Mapped[NotificationChannel] = mapped_column(
        String(16), default=NotificationChannel.EMAIL, nullable=False
    )
    is_read: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False, index=True)
    read_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    # Delivery tracking (e.g. SendGrid message id, sent timestamp, errors).
    delivered_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    delivery_meta: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict, nullable=False)

    # Optional deep-link target (entity type + id) for the feed.
    entity_type: Mapped[str | None] = mapped_column(String(64), nullable=True)
    entity_id: Mapped[uuid.UUID | None] = mapped_column(PG_UUID(as_uuid=True), nullable=True)

    def __repr__(self) -> str:
        return f"<Notification {self.notification_type} user={self.user_id}>"
