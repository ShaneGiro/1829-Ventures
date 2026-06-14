"""Interaction schemas."""

from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel

from app.core.constants import InteractionType
from app.schemas.common import SoftDeleteRead


class InteractionBase(BaseModel):
    interaction_type: InteractionType = InteractionType.NOTE
    summary: str | None = None
    body: str | None = None
    occurred_at: datetime | None = None
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
    company_id: uuid.UUID | None = None
    person_id: uuid.UUID | None = None
    deal_id: uuid.UUID | None = None


class InteractionRead(SoftDeleteRead, InteractionBase):
    source_email_id: str | None = None
    original_sender: str | None = None
    original_recipient: str | None = None
    forwarded_by: str | None = None
