"""Person model: founders, alumni, LP contacts, advisors, faculty, co-investors.

People link to companies through CompanyContact and carry RIT relationship detail
through Affiliation.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from sqlalchemy import String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, SoftDeleteMixin, TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from app.models.affiliation import Affiliation
    from app.models.company_contact import CompanyContact


class Person(UUIDPrimaryKeyMixin, TimestampMixin, SoftDeleteMixin, Base):
    __tablename__ = "people"

    full_name: Mapped[str] = mapped_column(String(255), index=True, nullable=False)
    email: Mapped[str | None] = mapped_column(String(320), index=True, nullable=True)
    phone: Mapped[str | None] = mapped_column(String(64), nullable=True)
    linkedin_url: Mapped[str | None] = mapped_column(String(1024), nullable=True)
    title: Mapped[str | None] = mapped_column(String(255), nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    source_system: Mapped[str | None] = mapped_column(String(64), nullable=True)
    field_provenance: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict, nullable=False)

    affiliations: Mapped[list[Affiliation]] = relationship(
        back_populates="person", cascade="all, delete-orphan"
    )
    company_links: Mapped[list[CompanyContact]] = relationship(
        back_populates="person", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<Person {self.full_name}>"
