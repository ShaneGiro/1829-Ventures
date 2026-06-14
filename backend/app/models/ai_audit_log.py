"""AiAuditLog: Ritchie's writes, recorded as intent BEFORE the canonical write.

Status starts `pending` (intent recorded), then becomes `committed` or `failed`.
Stores the tool, entity, old/new value, source (email/import/document),
confidence, and the idempotency key so retries never double-write. This gives a
complete, rollback-ready history of everything Ritchie changed.
"""

from __future__ import annotations

import uuid
from typing import Any

from sqlalchemy import Float, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.constants import AiWriteStatus
from app.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class AiAuditLog(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "ai_audit_logs"

    tool: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    entity_type: Mapped[str | None] = mapped_column(String(64), nullable=True)
    entity_id: Mapped[uuid.UUID | None] = mapped_column(
        PG_UUID(as_uuid=True), nullable=True, index=True
    )

    status: Mapped[AiWriteStatus] = mapped_column(
        String(16), default=AiWriteStatus.PENDING, nullable=False, index=True
    )

    field_name: Mapped[str | None] = mapped_column(String(128), nullable=True)
    old_value: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)
    new_value: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)

    source: Mapped[str | None] = mapped_column(String(512), nullable=True)
    confidence: Mapped[float | None] = mapped_column(Float, nullable=True)

    # Derived from event ID + tool name + entity ID; unique so retries are no-ops.
    idempotency_key: Mapped[str] = mapped_column(
        String(255), unique=True, nullable=False, index=True
    )
    error: Mapped[str | None] = mapped_column(Text, nullable=True)

    def __repr__(self) -> str:
        return f"<AiAuditLog {self.tool} status={self.status}>"
