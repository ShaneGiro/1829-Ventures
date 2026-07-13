"""Interaction schemas."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field

from app.core.constants import FollowUpStatus, InteractionDirection, InteractionType
from app.schemas.common import SoftDeleteRead


class InteractionBase(BaseModel):
    interaction_type: InteractionType = InteractionType.NOTE
    summary: str | None = None
    body: str | None = None
    occurred_at: datetime | None = None
    channel: str | None = Field(default=None, max_length=32)
    direction: InteractionDirection = InteractionDirection.INTERNAL
    follow_up_status: FollowUpStatus = FollowUpStatus.NONE
    company_id: uuid.UUID | None = None
    person_id: uuid.UUID | None = None
    deal_id: uuid.UUID | None = None


class InteractionCreate(InteractionBase):
    pass


class InteractionUpdate(BaseModel):
    interaction_type: InteractionType | None = None
    summary: str | None = None
    body: str | None = None
    occurred_at: datetime | None = None
    channel: str | None = Field(default=None, max_length=32)
    direction: InteractionDirection | None = None
    follow_up_status: FollowUpStatus | None = None
    company_id: uuid.UUID | None = None
    person_id: uuid.UUID | None = None
    deal_id: uuid.UUID | None = None


class InteractionRead(SoftDeleteRead, InteractionBase):
    created_by_id: uuid.UUID | None = None
    source_email_id: str | None = None
    original_sender: str | None = None
    original_recipient: str | None = None
    forwarded_by: str | None = None
    # Provenance (forwarding info, review status, fuzzy suggestion) for reviewers.
    provenance: dict[str, Any] = Field(default_factory=dict)
