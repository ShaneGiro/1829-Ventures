"""PortfolioMetric model: per-company reporting snapshot for a period.

Stores raw inputs (revenue, runway, headcount, valuation marks) and the
TVPI/DPI/IRR inputs; analytics are computed per-fund and across the portfolio.
"""

from __future__ import annotations

import uuid
from datetime import date

from sqlalchemy import Date, ForeignKey, Integer, Numeric, String
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class PortfolioMetric(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "portfolio_metrics"

    company_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("companies.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    investment_id: Mapped[uuid.UUID | None] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("investments.id", ondelete="SET NULL"), nullable=True
    )

    reporting_period: Mapped[str | None] = mapped_column(String(32), nullable=True)
    reporting_date: Mapped[date | None] = mapped_column(Date, nullable=True, index=True)

    revenue: Mapped[float | None] = mapped_column(Numeric(18, 2), nullable=True)
    runway_months: Mapped[float | None] = mapped_column(Numeric(6, 1), nullable=True)
    headcount: Mapped[int | None] = mapped_column(Integer, nullable=True)
    valuation_mark: Mapped[float | None] = mapped_column(Numeric(18, 2), nullable=True)

    # Performance inputs (calculations live in the analytics service).
    tvpi: Mapped[float | None] = mapped_column(Numeric(10, 4), nullable=True)
    dpi: Mapped[float | None] = mapped_column(Numeric(10, 4), nullable=True)
    irr: Mapped[float | None] = mapped_column(Numeric(10, 4), nullable=True)

    def __repr__(self) -> str:
        return f"<PortfolioMetric company={self.company_id} period={self.reporting_period}>"
