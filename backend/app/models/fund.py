"""Fund model: first-class entity (Beta, Fund I).

Investments reference the fund by FK, so a fund name change propagates to all
investments automatically (name stored once, joined at query time).
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import Integer, Numeric, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.constants import FundStatus
from app.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from app.models.investment import Investment


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

    investments: Mapped[list[Investment]] = relationship(back_populates="fund")

    def __repr__(self) -> str:
        return f"<Fund {self.name}>"
