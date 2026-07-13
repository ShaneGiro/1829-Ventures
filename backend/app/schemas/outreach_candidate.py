"""Derived outreach-candidate ranking schemas."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field

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
