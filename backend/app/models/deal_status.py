"""DealStatus: configurable pipeline stage stored in the database.

Stages are data, not a hardcoded enum, so they can be reordered/extended at
runtime without a code change. Seeded from constants.SEED_DEAL_STATUSES.
System stages are protected from deletion.
"""

from __future__ import annotations

from sqlalchemy import Boolean, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class DealStatus(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "deal_statuses"
    __table_args__ = (UniqueConstraint("name", name="uq_deal_status_name"),)

    name: Mapped[str] = mapped_column(String(128), nullable=False)
    sort_order: Mapped[int] = mapped_column(Integer, default=0, nullable=False, index=True)
    color: Mapped[str | None] = mapped_column(String(32), nullable=True)
    is_system: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    # Passed deals render in a separate swimlane below the main board.
    is_terminal: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    def __repr__(self) -> str:
        return f"<DealStatus {self.name} order={self.sort_order}>"
