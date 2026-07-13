"""Durable saved outreach-candidate lists and their manually worked items."""

from __future__ import annotations

import uuid
from typing import TYPE_CHECKING, Any

from sqlalchemy import Float, ForeignKey, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.constants import OutreachCandidateListStatus, OutreachCandidateStatus
from app.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from app.models.company import Company
    from app.models.person import Person
    from app.models.user import User


class OutreachCandidateList(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """A shared, saved pre-pipeline work queue."""

    __tablename__ = "outreach_candidate_lists"

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[OutreachCandidateListStatus] = mapped_column(
        String(16), default=OutreachCandidateListStatus.ACTIVE, nullable=False, index=True
    )
    default_filters: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict, nullable=False)
    created_by_id: Mapped[uuid.UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    owner_id: Mapped[uuid.UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    # Append-only summaries keep ownership/status context available even when a
    # referenced user is later deactivated. AuditLog remains the canonical trail.
    change_history: Mapped[list[Any]] = mapped_column(JSONB, default=list, nullable=False)

    created_by: Mapped[User | None] = relationship(foreign_keys=[created_by_id])
    owner: Mapped[User | None] = relationship(foreign_keys=[owner_id])
    items: Mapped[list[OutreachCandidateListItem]] = relationship(
        back_populates="candidate_list",
        order_by="OutreachCandidateListItem.created_at",
    )


class OutreachCandidateListItem(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """A company snapshot plus manual work state within a saved list."""

    __tablename__ = "outreach_candidate_list_items"
    __table_args__ = (
        UniqueConstraint("list_id", "company_id", name="uq_outreach_candidate_item_company"),
    )

    list_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("outreach_candidate_lists.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    company_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("companies.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    person_id: Mapped[uuid.UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("people.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    assigned_to_id: Mapped[uuid.UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    candidate_status: Mapped[OutreachCandidateStatus] = mapped_column(
        String(24), default=OutreachCandidateStatus.NEW, nullable=False, index=True
    )

    # Ranking is a snapshot. Refresh can replace these fields later without
    # touching candidate_status, assigned_to_id, or change_history.
    rank_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    rank_reasons: Mapped[list[Any]] = mapped_column(JSONB, default=list, nullable=False)
    score_version: Mapped[str | None] = mapped_column(String(32), nullable=True)
    score_breakdown: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict, nullable=False)
    why_this_company: Mapped[str | None] = mapped_column(Text, nullable=True)

    change_history: Mapped[list[Any]] = mapped_column(JSONB, default=list, nullable=False)

    candidate_list: Mapped[OutreachCandidateList] = relationship(back_populates="items")
    company: Mapped[Company] = relationship()
    person: Mapped[Person | None] = relationship()
    assigned_to: Mapped[User | None] = relationship()
