"""Fund model: first-class entity (Beta, Fund I).

Investments reference the fund by FK, so a fund name change propagates to all
investments automatically (name stored once, joined at query time).
"""

from __future__ import annotations

import uuid
from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, Integer, Numeric, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.constants import DEFAULT_RIT_ORGANIZATION_ID, FundStatus
from app.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from app.models.investment import Investment
    from app.models.legal_entity import LegalEntity


class Fund(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "funds"
    __table_args__ = (UniqueConstraint("name", name="uq_fund_name"),)

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    fund_number: Mapped[str | None] = mapped_column(String(64), nullable=True)
    vintage_year: Mapped[int | None] = mapped_column(Integer, nullable=True)
    committed_capital: Mapped[float | None] = mapped_column(Numeric(18, 2), nullable=True)
    status: Mapped[FundStatus] = mapped_column(
        String(16), default=FundStatus.ACTIVE, nullable=False
    )
    organization_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("organizations.id", ondelete="RESTRICT"),
        default=lambda: uuid.UUID(DEFAULT_RIT_ORGANIZATION_ID),
        nullable=False,
        index=True,
    )
    legal_entity_id: Mapped[uuid.UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("legal_entities.id", ondelete="RESTRICT"),
        nullable=True,
        unique=True,
    )

    investments: Mapped[list[Investment]] = relationship(back_populates="fund")
    legal_entity: Mapped[LegalEntity | None] = relationship(back_populates="funds")

    def __repr__(self) -> str:
        return f"<Fund {self.name}>"
