"""Tests for the explainable outreach-candidate scoring rules."""

from __future__ import annotations

import uuid

from app.core.constants import AlumniFounderStatus, OperationalStatus, RelationshipStatus
from app.models.company import Company
from app.services.outreach_candidate_service import score_candidate


def _company(**updates: object) -> Company:
    values: dict[str, object] = {
        "id": uuid.uuid4(),
        "name": "Acme",
        "stage": "Seed",
        "relationship_status": RelationshipStatus.IDENTIFIED,
        "alumni_founder_status": AlumniFounderStatus.ACTIVE,
        "alumni_founder_confidence": 0.9,
        "operational_status": OperationalStatus.OPERATIONAL,
        "operational_confidence": 0.8,
        "rubric_fit_score": 80.0,
        "thesis_alignment_score": 90.0,
        "fit_score_reasons": ["Strong technical differentiation"],
    }
    values.update(updates)
    return Company(**values)


def test_score_candidate_rewards_verified_fit_and_target_stage() -> None:
    score = score_candidate(_company(), recently_contacted=False)

    assert score.total == 87.88
    assert score.breakdown.stage_fit == 15.0
    assert score.breakdown.outreach_recency == 5.0
    assert "active RIT alumni founder" in score.why
    assert not score.warnings


def test_score_candidate_explains_uncertainty_and_recent_outreach() -> None:
    score = score_candidate(
        _company(
            stage=None,
            alumni_founder_status=AlumniFounderStatus.UNCLEAR,
            operational_status=OperationalStatus.UNVERIFIED,
            rubric_fit_score=None,
            thesis_alignment_score=None,
        ),
        recently_contacted=True,
    )

    assert score.breakdown.outreach_recency == 0.0
    assert "RIT alumni founder evidence is unclear" in score.warnings
    assert "Operational status needs verification" in score.warnings
    assert "Funding stage is outside or missing from the target range" in score.warnings
    assert "1829 fit scoring is incomplete" in score.warnings
