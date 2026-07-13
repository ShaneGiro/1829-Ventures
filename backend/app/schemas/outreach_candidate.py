"""Derived outreach-candidate ranking schemas."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field, model_validator

from app.core.constants import OutreachCandidateListStatus, OutreachCandidateStatus
from app.schemas.common import TimestampedRead
from app.schemas.company import CompanyRead


class CandidateScoreBreakdown(BaseModel):
    alumni_founder: float
    operational: float
    stage_fit: float
    rubric_fit: float
    thesis_alignment: float
    evidence_confidence: float
    outreach_recency: float


class OutreachCandidateRead(BaseModel):
    company: CompanyRead
    score: float = Field(ge=0, le=100)
    score_version: str
    breakdown: CandidateScoreBreakdown
    why_this_company: str
    warnings: list[str] = Field(default_factory=list)
    last_outreach_at: datetime | None = None
    follow_up_needed: bool = False


class OutreachCandidateListCreate(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    description: str | None = None
    owner_id: uuid.UUID | None = None
    default_filters: dict[str, Any] = Field(default_factory=dict)


class OutreachCandidateListUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=255)
    description: str | None = None
    owner_id: uuid.UUID | None = None
    status: OutreachCandidateListStatus | None = None
    change_reason: str | None = Field(default=None, max_length=1000)


class OutreachCandidateListItemCreate(BaseModel):
    company_id: uuid.UUID
    person_id: uuid.UUID | None = None
    assigned_to_id: uuid.UUID | None = None
    candidate_status: OutreachCandidateStatus = OutreachCandidateStatus.NEW
    rank_score: float | None = Field(default=None, ge=0, le=100)
    rank_reasons: list[Any] = Field(default_factory=list)
    score_version: str | None = Field(default=None, max_length=32)
    score_breakdown: dict[str, Any] = Field(default_factory=dict)
    why_this_company: str | None = None
    change_reason: str | None = Field(default=None, max_length=1000)


class OutreachCandidateListItemUpdate(BaseModel):
    assigned_to_id: uuid.UUID | None = None
    candidate_status: OutreachCandidateStatus | None = None
    change_reason: str | None = Field(default=None, max_length=1000)

    @model_validator(mode="after")
    def _require_work_state_change(self) -> OutreachCandidateListItemUpdate:
        changed = self.model_fields_set - {"change_reason"}
        if not changed:
            raise ValueError("Provide assigned_to_id or candidate_status")
        return self


class OutreachCandidateListItemRead(TimestampedRead):
    list_id: uuid.UUID
    company_id: uuid.UUID
    person_id: uuid.UUID | None = None
    assigned_to_id: uuid.UUID | None = None
    candidate_status: OutreachCandidateStatus
    rank_score: float | None = None
    rank_reasons: list[Any] = Field(default_factory=list)
    score_version: str | None = None
    score_breakdown: dict[str, Any] = Field(default_factory=dict)
    why_this_company: str | None = None
    change_history: list[dict[str, Any]] = Field(default_factory=list)


class OutreachCandidateListRead(TimestampedRead):
    name: str
    description: str | None = None
    status: OutreachCandidateListStatus
    default_filters: dict[str, Any] = Field(default_factory=dict)
    created_by_id: uuid.UUID | None = None
    owner_id: uuid.UUID | None = None
    change_history: list[dict[str, Any]] = Field(default_factory=list)


class OutreachCandidateListDetail(OutreachCandidateListRead):
    items: list[OutreachCandidateListItemRead] = Field(default_factory=list)
