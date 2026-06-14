"""Interaction model: emails, calls, meetings, notes, intros, touchpoints.

Forwarded Gmail messages become email interactions with provenance (forwarding
team member, original sender/recipient, timestamp). The pgvector `embedding`
feeds semantic search and Ritchie's RAG context.
"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import TYPE_CHECKING, Any

from pgvector.sqlalchemy import Vector
from sqlalchemy import DateTime, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.constants import EMBEDDING_DIM, InteractionType
from app.models.base import Base, SoftDeleteMixin, TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from app.models.company import Company


class Interaction(UUIDPrimaryKeyMixin, TimestampMixin, SoftDeleteMixin, Base):
    __tablename__ = "interactions"

    interaction_type: Mapped[InteractionType] = mapped_column(
        String(32), default=InteractionType.NOTE, nullable=False, index=True
    )
    summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    body: Mapped[str | None] = mapped_column(Text, nullable=True)
    occurred_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    # Optional links — an interaction can attach to a company, person, and/or deal.
    company_id: Mapped[uuid.UUID | None] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("companies.id", ondelete="SET NULL"), nullable=True
    )
    person_id: Mapped[uuid.UUID | None] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("people.id", ondelete="SET NULL"), nullable=True
    )
    deal_id: Mapped[uuid.UUID | None] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("deals.id", ondelete="SET NULL"), nullable=True
    )

    # Email provenance (set for forwarded-email interactions).
    source_email_id: Mapped[str | None] = mapped_column(String(512), nullable=True)
    original_sender: Mapped[str | None] = mapped_column(String(320), nullable=True)
    original_recipient: Mapped[str | None] = mapped_column(String(320), nullable=True)
    forwarded_by: Mapped[str | None] = mapped_column(String(320), nullable=True)
    provenance: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict, nullable=False)

    embedding: Mapped[list[float] | None] = mapped_column(Vector(EMBEDDING_DIM), nullable=True)

    company: Mapped[Company | None] = relationship(back_populates="interactions")

    def __repr__(self) -> str:
        return f"<Interaction {self.interaction_type} company={self.company_id}>"
