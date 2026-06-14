"""AgentEventLog: every event emitted to Ritchie and its processing outcome.

Includes `policy_blocked` rejections (logged with tool, payload hash, rationale,
confidence) and `agent_unavailable` outcomes for graceful degradation.
"""

from __future__ import annotations

from typing import Any

from sqlalchemy import Float, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.core.constants import AgentEventStatus
from app.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class AgentEventLog(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "agent_event_logs"

    event_type: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    entity_type: Mapped[str | None] = mapped_column(String(64), nullable=True)
    entity_id: Mapped[str | None] = mapped_column(String(64), nullable=True)

    status: Mapped[AgentEventStatus] = mapped_column(
        String(32), default=AgentEventStatus.PENDING, nullable=False, index=True
    )

    payload: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict, nullable=False)
    payload_hash: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True)

    # Set for policy_blocked rejections.
    blocked_tool: Mapped[str | None] = mapped_column(String(128), nullable=True)
    rationale: Mapped[str | None] = mapped_column(Text, nullable=True)
    confidence: Mapped[float | None] = mapped_column(Float, nullable=True)

    response_summary: Mapped[str | None] = mapped_column(Text, nullable=True)

    def __repr__(self) -> str:
        return f"<AgentEventLog {self.event_type} status={self.status}>"
