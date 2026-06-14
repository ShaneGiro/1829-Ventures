"""Document model: metadata in Postgres, file bodies in S3-compatible storage.

Tracks the storage key, external links, source system, and the related
company/deal/person. File bytes live in MinIO (v1) / R2 (v2).
"""

from __future__ import annotations

import uuid
from typing import Any

from sqlalchemy import BigInteger, ForeignKey, String
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.constants import DocumentSource
from app.models.base import Base, SoftDeleteMixin, TimestampMixin, UUIDPrimaryKeyMixin


class Document(UUIDPrimaryKeyMixin, TimestampMixin, SoftDeleteMixin, Base):
    __tablename__ = "documents"

    filename: Mapped[str] = mapped_column(String(512), nullable=False)
    content_type: Mapped[str | None] = mapped_column(String(255), nullable=True)
    size_bytes: Mapped[int | None] = mapped_column(BigInteger, nullable=True)

    # Storage key in object storage, or an external link for linked-only docs.
    storage_key: Mapped[str | None] = mapped_column(String(1024), nullable=True)
    external_link: Mapped[str | None] = mapped_column(String(2048), nullable=True)
    source: Mapped[DocumentSource] = mapped_column(
        String(32), default=DocumentSource.UPLOAD, nullable=False
    )

    company_id: Mapped[uuid.UUID | None] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("companies.id", ondelete="CASCADE"), nullable=True
    )
    deal_id: Mapped[uuid.UUID | None] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("deals.id", ondelete="CASCADE"), nullable=True
    )
    person_id: Mapped[uuid.UUID | None] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("people.id", ondelete="SET NULL"), nullable=True
    )
    uploaded_by: Mapped[uuid.UUID | None] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    extra_metadata: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict, nullable=False)

    def __repr__(self) -> str:
        return f"<Document {self.filename}>"
