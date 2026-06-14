"""Investment model: a fund's investment in a company (optionally tied to a deal)."""

from __future__ import annotations

import uuid
from datetime import date
from typing import TYPE_CHECKING

from sqlalchemy import Date, ForeignKey, Numeric, String
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, SoftDeleteMixin, TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from app.models.fund import Fund


class Investment(UUIDPrimaryKeyMixin, TimestampMixin, SoftDeleteMixin, Base):
    __tablename__ = "investments"

    fund_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("funds.id", ondelete="RESTRICT"), nullable=False
    )
    company_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("companies.id", ondelete="CASCADE"), nullable=False
    )
    deal_id: Mapped[uuid.UUID | None] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("deals.id", ondelete="SET NULL"), nullable=True
    )

    round_name: Mapped[str | None] = mapped_column(String(64), nullable=True)
    amount: Mapped[float | None] = mapped_column(Numeric(18, 2), nullable=True)
    currency: Mapped[str | None] = mapped_column(String(8), default="USD", nullable=True)
    investment_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    instrument: Mapped[str | None] = mapped_column(String(64), nullable=True)

    # Valuation / ownership inputs (snapshots).
    pre_money_valuation: Mapped[float | None] = mapped_column(Numeric(18, 2), nullable=True)
    post_money_valuation: Mapped[float | None] = mapped_column(Numeric(18, 2), nullable=True)
    ownership_pct: Mapped[float | None] = mapped_column(Numeric(7, 4), nullable=True)

    fund: Mapped[Fund] = relationship(back_populates="investments")

    def __repr__(self) -> str:
        return f"<Investment fund={self.fund_id} company={self.company_id}>"
