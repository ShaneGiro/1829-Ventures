"""CompanyContact: company<->person join with primary-contact + role.

A company can have many contacts; exactly one is marked primary for default
workflows (enforced in the service layer, not the schema, for v1 flexibility).
"""

from __future__ import annotations

import uuid
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, ForeignKey, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from app.models.company import Company
    from app.models.person import Person


class CompanyContact(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "company_contacts"
    __table_args__ = (UniqueConstraint("company_id", "person_id", name="uq_company_person"),)

    company_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("companies.id", ondelete="CASCADE"), nullable=False
    )
    person_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("people.id", ondelete="CASCADE"), nullable=False
    )
    is_primary: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    role: Mapped[str | None] = mapped_column(String(128), nullable=True)

    company: Mapped[Company] = relationship(back_populates="contacts")
    person: Mapped[Person] = relationship(back_populates="company_links")

    def __repr__(self) -> str:
        return f"<CompanyContact company={self.company_id} person={self.person_id}>"
