"""Deal model: an investment opportunity (initial or follow-on) for a company.

A company can have many deals over time. Relationship status lives on the company;
the deal carries the investment status. Round details are optional because 1829
often does outbound alumni outreach before a company is fundraising.
"""

from __future__ import annotations

import uuid
from datetime import date
from typing import TYPE_CHECKING

from sqlalchemy import Date, ForeignKey, Numeric, String, Text
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.constants import InvestmentStatus
from app.models.base import Base, SoftDeleteMixin, TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from app.models.company import Company
    from app.models.diligence_checklist_item import DiligenceChecklistItem
    from app.models.rubric import Rubric


class Deal(UUIDPrimaryKeyMixin, TimestampMixin, SoftDeleteMixin, Base):
    __tablename__ = "deals"

    company_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("companies.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    name: Mapped[str | None] = mapped_column(String(512), nullable=True)

    investment_status: Mapped[InvestmentStatus] = mapped_column(
        String(32), default=InvestmentStatus.SOURCED, nullable=False, index=True
    )
    # FK to the configurable pipeline stage (deal_statuses table) for board display.
    deal_status_id: Mapped[uuid.UUID | None] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("deal_statuses.id", ondelete="SET NULL"), nullable=True
    )

    # Optional round details.
    round_type: Mapped[str | None] = mapped_column(String(64), nullable=True)
    round_amount: Mapped[float | None] = mapped_column(Numeric(18, 2), nullable=True)
    round_currency: Mapped[str | None] = mapped_column(String(8), nullable=True)
    round_date: Mapped[date | None] = mapped_column(Date, nullable=True)

    thesis_fit_notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    decision_notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_follow_on: Mapped[bool] = mapped_column(default=False, nullable=False)

    company: Mapped[Company] = relationship(back_populates="deals")
    rubric: Mapped[Rubric | None] = relationship(
        back_populates="deal", uselist=False, cascade="all, delete-orphan"
    )
    diligence_items: Mapped[list[DiligenceChecklistItem]] = relationship(
        back_populates="deal", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<Deal company={self.company_id} status={self.investment_status}>"
