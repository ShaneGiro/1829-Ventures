"""Diligence service unit tests."""

from __future__ import annotations

import uuid

import pytest

from app.models.rubric import Rubric
from app.services.diligence_service import compute_rubric


def _passing_gates(rubric: Rubric) -> None:
    rubric.gate_rit_connection = True
    rubric.gate_thesis_alignment = True
    rubric.gate_stage_seed_to_series_a = True
    rubric.gate_tech_enabled = True


def test_compute_rubric_uses_weighted_category_averages() -> None:
    rubric = Rubric(deal_id=uuid.uuid4())
    _passing_gates(rubric)
    rubric.commercial_technical_balance = 5
    rubric.coachability_grit = 5
    rubric.talent_magnetism = 4
    rubric.ip_protection = 4
    rubric.external_validation = 4
    rubric.development_stage = 4
    rubric.capital_efficiency = 5
    rubric.path_to_revenue = 4
    rubric.market_pain = 5
    rubric.unit_economics = 4
    rubric.structural_advantage = 4
    rubric.talent_pipeline = 4
    rubric.mission_alignment = 5
    rubric.syndicate_strength = 3
    rubric.valuation_discipline = 4

    result = compute_rubric(rubric)

    assert result.knockout_passed is True
    assert result.composite_score == pytest.approx(86.17)
    assert result.recommendation == "deep_diligence"
    assert result.category_scores["team"] == pytest.approx(23.33)


def test_compute_rubric_blocks_scoring_when_knockout_gate_fails() -> None:
    rubric = Rubric(deal_id=uuid.uuid4())
    _passing_gates(rubric)
    rubric.gate_tech_enabled = False
    rubric.commercial_technical_balance = 5

    result = compute_rubric(rubric)

    assert result.knockout_passed is False
    assert result.composite_score is None
    assert result.recommendation == "pass_knockout"


def test_compute_rubric_waits_for_all_subscores() -> None:
    rubric = Rubric(deal_id=uuid.uuid4())
    _passing_gates(rubric)
    rubric.commercial_technical_balance = 5

    result = compute_rubric(rubric)

    assert result.knockout_passed is True
    assert result.composite_score is None
    assert result.recommendation is None
