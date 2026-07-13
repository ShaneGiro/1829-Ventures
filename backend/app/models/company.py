"""Company model — the primary CRM workspace.

A company can be created with only a name; missing fields surface as completeness
gaps rather than blocking creation. Manually curated CRM fields are the source of
truth. PostGIS `location` powers (deferred) map analytics; the pgvector
`embedding` powers semantic search and Ritchie's RAG context.
"""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING, Any

from geoalchemy2 import Geometry
from pgvector.sqlalchemy import Vector
from sqlalchemy import Boolean, DateTime, Float, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.constants import (
    DEFAULT_SECTOR,
    EMBEDDING_DIM,
    AlumniFounderStatus,
    OperationalStatus,
    RelationshipStatus,
)
from app.models.base import Base, SoftDeleteMixin, TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from app.models.company_contact import CompanyContact
    from app.models.deal import Deal
    from app.models.interaction import Interaction


class Company(UUIDPrimaryKeyMixin, TimestampMixin, SoftDeleteMixin, Base):
    __tablename__ = "companies"

    name: Mapped[str] = mapped_column(String(512), index=True, nullable=False)
    website: Mapped[str | None] = mapped_column(String(1024), nullable=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    sector: Mapped[str] = mapped_column(String(64), default=DEFAULT_SECTOR, nullable=False)
    stage: Mapped[str | None] = mapped_column(String(64), nullable=True)

    # Location: human-readable parts + PostGIS point for spatial queries.
    city: Mapped[str | None] = mapped_column(String(255), nullable=True)
    state: Mapped[str | None] = mapped_column(String(255), nullable=True)
    country: Mapped[str | None] = mapped_column(String(255), nullable=True)
    location: Mapped[object | None] = mapped_column(
        Geometry(geometry_type="POINT", srid=4326, spatial_index=True),
        nullable=True,
    )

    # Relationship lane (separate from any deal's investment status).
    relationship_status: Mapped[RelationshipStatus] = mapped_column(
        String(32), default=RelationshipStatus.IDENTIFIED, nullable=False, index=True
    )

    # RIT nexus is assumed for actively managed companies; flag avoids re-entry.
    has_rit_nexus: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    rit_source_channel: Mapped[str | None] = mapped_column(String(255), nullable=True)
    thesis_notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Ritchie enrichment is explicit, confidence-scored, and evidence-backed.
    alumni_founder_status: Mapped[AlumniFounderStatus] = mapped_column(
        String(16), default=AlumniFounderStatus.UNVERIFIED, nullable=False, index=True
    )
    alumni_founder_confidence: Mapped[float | None] = mapped_column(Float, nullable=True)
    alumni_founder_evidence: Mapped[dict[str, Any]] = mapped_column(
        JSONB, default=dict, nullable=False
    )
    alumni_founder_verified_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    operational_status: Mapped[OperationalStatus] = mapped_column(
        String(24), default=OperationalStatus.UNVERIFIED, nullable=False, index=True
    )
    operational_confidence: Mapped[float | None] = mapped_column(Float, nullable=True)
    operational_evidence: Mapped[dict[str, Any]] = mapped_column(
        JSONB, default=dict, nullable=False
    )
    operational_verified_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    rubric_fit_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    thesis_alignment_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    fit_score_confidence: Mapped[float | None] = mapped_column(Float, nullable=True)
    fit_score_reasons: Mapped[list[Any]] = mapped_column(JSONB, default=list, nullable=False)
    fit_score_version: Mapped[str | None] = mapped_column(String(32), nullable=True)
    fit_scored_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    # Dealroom / import provenance.
    dealroom_id: Mapped[str | None] = mapped_column(String(128), nullable=True, index=True)
    domain: Mapped[str | None] = mapped_column(String(512), nullable=True, index=True)
    source_system: Mapped[str | None] = mapped_column(String(64), nullable=True)
    # Per-field provenance/confidence (source, confidence, actor) keyed by field name.
    field_provenance: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict, nullable=False)

    # Dealroom-imported companies start unreviewed and are hidden from the main
    # company-flow dashboard until a human explicitly marks them reviewed.
    imported_unreviewed: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    completeness_pct: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)

    # Semantic-search / RAG embedding (populated asynchronously by a worker).
    embedding: Mapped[list[float] | None] = mapped_column(Vector(EMBEDDING_DIM), nullable=True)

    contacts: Mapped[list[CompanyContact]] = relationship(
        back_populates="company", cascade="all, delete-orphan"
    )
    deals: Mapped[list[Deal]] = relationship(back_populates="company")
    interactions: Mapped[list[Interaction]] = relationship(back_populates="company")

    def __repr__(self) -> str:
        return f"<Company {self.name}>"
