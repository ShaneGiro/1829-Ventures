"""Legal entities and effective-dated relationships managed by RIT."""

from __future__ import annotations

import uuid
from datetime import date
from typing import TYPE_CHECKING, Any

from sqlalchemy import Date, ForeignKey, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.constants import (
    LegalEntityRelationshipType,
    LegalEntityStatus,
    LegalEntityType,
)
from app.models.base import Base, SoftDeleteMixin, TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from app.models.fund import Fund
    from app.models.organization import Organization


class LegalEntity(UUIDPrimaryKeyMixin, TimestampMixin, SoftDeleteMixin, Base):
    __tablename__ = "legal_entities"
    __table_args__ = (
        UniqueConstraint("organization_id", "legal_name", name="uq_org_legal_entity_name"),
    )

    organization_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("organizations.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    legal_name: Mapped[str] = mapped_column(String(255), nullable=False)
    display_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    entity_type: Mapped[LegalEntityType] = mapped_column(String(32), nullable=False, index=True)
    status: Mapped[LegalEntityStatus] = mapped_column(
        String(16), default=LegalEntityStatus.ACTIVE, nullable=False
    )
    jurisdiction: Mapped[str | None] = mapped_column(String(128), nullable=True)
    formation_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    external_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    base_currency: Mapped[str] = mapped_column(String(3), default="USD", nullable=False)
    extra_metadata: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict, nullable=False)

    organization: Mapped[Organization] = relationship(back_populates="legal_entities")
    funds: Mapped[list[Fund]] = relationship(back_populates="legal_entity")
    parent_relationships: Mapped[list[LegalEntityRelationship]] = relationship(
        foreign_keys="LegalEntityRelationship.parent_entity_id",
        back_populates="parent_entity",
        cascade="all, delete-orphan",
    )
    child_relationships: Mapped[list[LegalEntityRelationship]] = relationship(
        foreign_keys="LegalEntityRelationship.child_entity_id",
        back_populates="child_entity",
        cascade="all, delete-orphan",
    )


class LegalEntityRelationship(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "legal_entity_relationships"
    __table_args__ = (
        UniqueConstraint(
            "parent_entity_id",
            "child_entity_id",
            "relationship_type",
            "effective_from",
            name="uq_legal_entity_relationship_version",
        ),
    )

    parent_entity_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("legal_entities.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    child_entity_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("legal_entities.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    relationship_type: Mapped[LegalEntityRelationshipType] = mapped_column(
        String(32), nullable=False
    )
    effective_from: Mapped[date] = mapped_column(Date, nullable=False)
    effective_to: Mapped[date | None] = mapped_column(Date, nullable=True)

    parent_entity: Mapped[LegalEntity] = relationship(
        foreign_keys=[parent_entity_id], back_populates="parent_relationships"
    )
    child_entity: Mapped[LegalEntity] = relationship(
        foreign_keys=[child_entity_id], back_populates="child_relationships"
    )
