"""Affiliation model: RIT relationship metadata connecting a person to 1829's thesis.

Captures graduation year, college/program, and role flags (founder, operator,
investor, advisor, faculty).
"""

from __future__ import annotations

import uuid
from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, Integer, String
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from app.models.person import Person


class Affiliation(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "affiliations"

    person_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("people.id", ondelete="CASCADE"), nullable=False
    )

    rit_relationship: Mapped[str | None] = mapped_column(String(128), nullable=True)
    graduation_year: Mapped[int | None] = mapped_column(Integer, nullable=True)
    college: Mapped[str | None] = mapped_column(String(255), nullable=True)
    program: Mapped[str | None] = mapped_column(String(255), nullable=True)
    # Role flags stored as a single comma/JSON list-friendly string for v1 simplicity.
    role: Mapped[str | None] = mapped_column(String(128), nullable=True)

    person: Mapped[Person] = relationship(back_populates="affiliations")

    def __repr__(self) -> str:
        return f"<Affiliation person={self.person_id} rel={self.rit_relationship}>"
