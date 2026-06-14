"""AuditLog: every create/update/archive across the CRM.

Records actor (human, import, system, or Ritchie), timestamp, entity, the changed
field(s), old value, new value, and optional reason/context. This is the canonical
human/system audit trail; Ritchie's writes also get a richer AiAuditLog entry.
"""

from __future__ import annotations

import uuid
from typing import Any

from sqlalchemy import String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.constants import ActorType
from app.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class AuditLog(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "audit_logs"

    actor_type: Mapped[ActorType] = mapped_column(String(16), nullable=False, index=True)
    actor_id: Mapped[uuid.UUID | None] = mapped_column(PG_UUID(as_uuid=True), nullable=True)
    actor_label: Mapped[str | None] = mapped_column(String(255), nullable=True)

    action: Mapped[str] = mapped_column(String(32), nullable=False)  # create|update|archive
    entity_type: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    entity_id: Mapped[uuid.UUID | None] = mapped_column(
        PG_UUID(as_uuid=True), nullable=True, index=True
    )

    field_name: Mapped[str | None] = mapped_column(String(128), nullable=True)
    old_value: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)
    new_value: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)
    reason: Mapped[str | None] = mapped_column(Text, nullable=True)

    def __repr__(self) -> str:
        return f"<AuditLog {self.action} {self.entity_type}:{self.entity_id}>"
