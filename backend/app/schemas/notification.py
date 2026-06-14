"""Notification schemas (feed + unread support, ready for the v2 in-app bell)."""

from __future__ import annotations

import uuid
from datetime import datetime

from app.core.constants import NotificationChannel
from app.schemas.common import TimestampedRead


class NotificationRead(TimestampedRead):
    user_id: uuid.UUID
    notification_type: str
    title: str
    body: str | None = None
    channel: NotificationChannel
    is_read: bool
    read_at: datetime | None = None
    entity_type: str | None = None
    entity_id: uuid.UUID | None = None
