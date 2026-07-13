"""Company schemas, including the completeness response."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field

from app.core.constants import AlumniFounderStatus, OperationalStatus, RelationshipStatus
from app.schemas.common import SoftDeleteRead


class CompanyBase(BaseModel):
    name: str = Field(min_length=1, max_length=512)
    website: str | None = None
    description: str | None = None
    sector: str | None = None
    stage: str | None = None
    city: str | None = None
    state: str | None = None
    country: str | None = None
    thesis_notes: str | None = None
    rit_source_channel: str | None = None


class CompanyCreate(CompanyBase):
    """Minimal-create supported: only `name` is required."""

    relationship_status: RelationshipStatus = RelationshipStatus.IDENTIFIED
    has_rit_nexus: bool = True


class CompanyUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=512)
    website: str | None = None
    description: str | None = None
    sector: str | None = None
    stage: str | None = None
    city: str | None = None
    state: str | None = None
    country: str | None = None
    relationship_status: RelationshipStatus | None = None
    has_rit_nexus: bool | None = None
    rit_source_channel: str | None = None
    thesis_notes: str | None = None
    alumni_founder_status: AlumniFounderStatus | None = None
    alumni_founder_confidence: float | None = Field(default=None, ge=0, le=1)
    alumni_founder_evidence: dict[str, Any] | None = None
    alumni_founder_verified_at: datetime | None = None
    operational_status: OperationalStatus | None = None
    operational_confidence: float | None = Field(default=None, ge=0, le=1)
    operational_evidence: dict[str, Any] | None = None
    operational_verified_at: datetime | None = None
    rubric_fit_score: float | None = Field(default=None, ge=0, le=100)
    thesis_alignment_score: float | None = Field(default=None, ge=0, le=100)
    fit_score_confidence: float | None = Field(default=None, ge=0, le=1)
    fit_score_reasons: list[str] | None = None
    fit_score_version: str | None = None
    fit_scored_at: datetime | None = None


class CompanyRead(SoftDeleteRead, CompanyBase):
    relationship_status: RelationshipStatus
    has_rit_nexus: bool
    dealroom_id: str | None = None
    domain: str | None = None
    source_system: str | None = None
    imported_unreviewed: bool
    completeness_pct: float
    alumni_founder_status: AlumniFounderStatus
    alumni_founder_confidence: float | None = None
    alumni_founder_evidence: dict[str, Any] = Field(default_factory=dict)
    alumni_founder_verified_at: datetime | None = None
    operational_status: OperationalStatus
    operational_confidence: float | None = None
    operational_evidence: dict[str, Any] = Field(default_factory=dict)
    operational_verified_at: datetime | None = None
    rubric_fit_score: float | None = None
    thesis_alignment_score: float | None = None
    fit_score_confidence: float | None = None
    fit_score_reasons: list[str] = Field(default_factory=list)
    fit_score_version: str | None = None
    fit_scored_at: datetime | None = None


class CompanyCompleteness(BaseModel):
    company_id: str
    completeness_pct: float
    missing_fields: list[str]


class CompanyDealroomData(BaseModel):
    company_id: str
    import_row_id: str | None = None
    batch_id: str | None = None
    row_number: int | None = None
    status: str | None = None
    raw: dict[str, Any] = {}
    normalized: dict[str, Any] = {}
