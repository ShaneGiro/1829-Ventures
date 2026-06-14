"""Diligence checklist item: per-deal evidence item with completion history."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.constants import DiligenceItemStatus
from app.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from app.models.deal import Deal


class DiligenceChecklistItem(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "diligence_checklist_items"

    deal_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("deals.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    label: Mapped[str] = mapped_column(String(512), nullable=False)
    status: Mapped[DiligenceItemStatus] = mapped_column(
        String(32), default=DiligenceItemStatus.NOT_STARTED, nullable=False
    )
    sort_order: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    evidence_notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    completed_by: Mapped[uuid.UUID | None] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    deal: Mapped[Deal] = relationship(back_populates="diligence_items")

    def __repr__(self) -> str:
        return f"<DiligenceChecklistItem {self.label} status={self.status}>"
