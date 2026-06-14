"""ImportRow: per-record raw payload, field provenance, status, and match/conflict info.

The raw source row is always preserved for auditability, even for skipped or
conflicting rows.
"""

from __future__ import annotations

import uuid
from typing import TYPE_CHECKING, Any

from sqlalchemy import ForeignKey, Integer, String
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.constants import ImportRowStatus
from app.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from app.models.import_batch import ImportBatch


class ImportRow(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "import_rows"

    batch_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("import_batches.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    row_number: Mapped[int] = mapped_column(Integer, nullable=False)
    status: Mapped[ImportRowStatus] = mapped_column(
        String(16), default=ImportRowStatus.PENDING, nullable=False, index=True
    )

    raw_data: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict, nullable=False)
    # Per-field source metadata + confidence captured during parsing.
    field_provenance: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict, nullable=False)
    # Conflict diffs (curated value vs incoming value) surfaced in preview.
    conflicts: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict, nullable=False)
    skip_reason: Mapped[str | None] = mapped_column(String(512), nullable=True)

    # Set once a row is committed/matched to a company.
    matched_company_id: Mapped[uuid.UUID | None] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("companies.id", ondelete="SET NULL"), nullable=True
    )

    batch: Mapped[ImportBatch] = relationship(back_populates="rows")

    def __repr__(self) -> str:
        return f"<ImportRow batch={self.batch_id} #{self.row_number} {self.status}>"
