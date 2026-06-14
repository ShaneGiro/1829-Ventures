"""Diligence checklist item schemas."""

from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel

from app.core.constants import DiligenceItemStatus
from app.schemas.common import TimestampedRead


class DiligenceItemBase(BaseModel):
    label: str
    sort_order: int = 0
    evidence_notes: str | None = None


class DiligenceItemCreate(DiligenceItemBase):
    deal_id: uuid.UUID


class DiligenceItemUpdate(BaseModel):
    label: str | None = None
    status: DiligenceItemStatus | None = None
    sort_order: int | None = None
    evidence_notes: str | None = None


class DiligenceItemRead(TimestampedRead, DiligenceItemBase):
    deal_id: uuid.UUID
    status: DiligenceItemStatus
    completed_by: uuid.UUID | None = None
    completed_at: datetime | None = None
