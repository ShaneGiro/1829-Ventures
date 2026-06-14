"""Screening rubric schemas: knockout gates, 15 sub-scores, computed composite.

Sub-scores accept 1-5 (validated here); the composite is computed server-side by
the diligence service and is read-only on the response.
"""

from __future__ import annotations

import uuid

from pydantic import BaseModel, Field

from app.core.constants import RUBRIC_SUBSCORE_MAX, RUBRIC_SUBSCORE_MIN
from app.schemas.common import TimestampedRead

SubScore = int | None
_score_field = Field(default=None, ge=RUBRIC_SUBSCORE_MIN, le=RUBRIC_SUBSCORE_MAX)


class RubricScores(BaseModel):
    # Knockout gates (binary).
    gate_rit_connection: bool | None = None
    gate_thesis_alignment: bool | None = None
    gate_stage_seed_to_series_a: bool | None = None
    gate_tech_enabled: bool | None = None

    # Team (x5)
    commercial_technical_balance: SubScore = _score_field
    coachability_grit: SubScore = _score_field
    talent_magnetism: SubScore = _score_field
    # Tech (x4)
    ip_protection: SubScore = _score_field
    external_validation: SubScore = _score_field
    development_stage: SubScore = _score_field
    # Commercial (x5)
    capital_efficiency: SubScore = _score_field
    path_to_revenue: SubScore = _score_field
    market_pain: SubScore = _score_field
    unit_economics: SubScore = _score_field
    # RIT Fit (x4)
    structural_advantage: SubScore = _score_field
    talent_pipeline: SubScore = _score_field
    mission_alignment: SubScore = _score_field
    # Deal Dynamics (x2)
    syndicate_strength: SubScore = _score_field
    valuation_discipline: SubScore = _score_field

    notes: str | None = None


class RubricUpdate(RubricScores):
    """Partial update — every field optional; service recomputes the composite."""


class RubricRead(TimestampedRead, RubricScores):
    deal_id: uuid.UUID
    composite_score: float | None = None
