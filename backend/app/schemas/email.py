"""Forwarded Gmail ingestion schemas."""

from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, Field

from app.schemas.interaction import InteractionRead


class ForwardedEmailAttachment(BaseModel):
    filename: str
    content_type: str | None = None
    size_bytes: int = Field(ge=0)
    content_base64: str | None = None


class GmailForwardedEmailIngest(BaseModel):
    source_email_id: str
    forwarded_by: str
    raw_message: str
    received_at: datetime | None = None
    attachments: list[ForwardedEmailAttachment] = Field(default_factory=list)


class GmailIngestResult(BaseModel):
    status: str
    interaction: InteractionRead
    document_ids: list[uuid.UUID] = Field(default_factory=list)
    review_reason: str | None = None
