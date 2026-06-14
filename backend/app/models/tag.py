"""Tag model and the company<->tag association.

Hybrid tags: users create tags during normal work; admins merge/rename/archive;
protected system tags stay controlled for analytics. Pass-reason tags (kind =
pass_reason) are required when a company/deal is passed.
"""

from __future__ import annotations

import uuid

from sqlalchemy import Column, ForeignKey, String, Table, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.constants import TagKind
from app.models.base import Base, SoftDeleteMixin, TimestampMixin, UUIDPrimaryKeyMixin

# Association table: companies <-> tags (many-to-many).
company_tags = Table(
    "company_tags",
    Base.metadata,
    Column(
        "company_id",
        PG_UUID(as_uuid=True),
        ForeignKey("companies.id", ondelete="CASCADE"),
        primary_key=True,
    ),
    Column(
        "tag_id",
        PG_UUID(as_uuid=True),
        ForeignKey("tags.id", ondelete="CASCADE"),
        primary_key=True,
    ),
)


class Tag(UUIDPrimaryKeyMixin, TimestampMixin, SoftDeleteMixin, Base):
    __tablename__ = "tags"
    __table_args__ = (UniqueConstraint("name", "kind", name="uq_tag_name_kind"),)

    name: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    kind: Mapped[TagKind] = mapped_column(String(16), default=TagKind.USER, nullable=False)
    # When a tag is merged into another, point to the survivor for analytics.
    merged_into_id: Mapped[uuid.UUID | None] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("tags.id", ondelete="SET NULL"), nullable=True
    )

    def __repr__(self) -> str:
        return f"<Tag {self.name} kind={self.kind}>"
