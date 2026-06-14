"""ImportBatch: job-level metadata for a Dealroom CSV import."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import TYPE_CHECKING, Any

from sqlalchemy import DateTime, ForeignKey, Integer, String
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.constants import ImportStatus
from app.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from app.models.import_row import ImportRow


class ImportBatch(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "import_batches"

    source: Mapped[str] = mapped_column(String(64), default="dealroom", nullable=False)
    filename: Mapped[str | None] = mapped_column(String(512), nullable=True)
    status: Mapped[ImportStatus] = mapped_column(
        String(32), default=ImportStatus.UPLOADED, nullable=False, index=True
    )

    uploaded_by: Mapped[uuid.UUID | None] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    committed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    # Summary counts (detected/created/matched/conflict/skipped) + column mapping.
    summary: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict, nullable=False)
    column_mapping: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict, nullable=False)
    total_rows: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    rows: Mapped[list[ImportRow]] = relationship(
        back_populates="batch", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<ImportBatch {self.source} status={self.status}>"
