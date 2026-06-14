"""AgentPolicy: the runtime binary authorization policy for Ritchie.

Each row is one tool (optionally narrowed to a field) tagged `authorized` or
`blocked`. Changes are made at runtime via the policy service, take effect
immediately (no restart), and are themselves audited. There is no proposal or
per-change approval workflow — the policy is strictly binary.
"""

from __future__ import annotations

import uuid

from sqlalchemy import String, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.constants import PolicyState
from app.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class AgentPolicy(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "agent_policies"
    __table_args__ = (UniqueConstraint("tool", "field_name", name="uq_policy_tool_field"),)

    tool: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    # NULL field_name = the whole tool/action; otherwise field-level for record writes.
    field_name: Mapped[str | None] = mapped_column(String(128), nullable=True)

    state: Mapped[PolicyState] = mapped_column(
        String(16), default=PolicyState.BLOCKED, nullable=False
    )
    updated_by: Mapped[uuid.UUID | None] = mapped_column(PG_UUID(as_uuid=True), nullable=True)

    def __repr__(self) -> str:
        return f"<AgentPolicy {self.tool}.{self.field_name}={self.state}>"
