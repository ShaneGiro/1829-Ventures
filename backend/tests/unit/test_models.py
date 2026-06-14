"""Model-structure unit tests (no database required).

Verifies the metadata registry, soft-delete mixin behavior, relationship wiring,
and that the rubric exposes all 15 sub-score columns.
"""

from __future__ import annotations

from datetime import UTC, datetime

from app.core.constants import RUBRIC_SUBSCORES
from app.models import Base
from app.models.company import Company
from app.models.deal import Deal
from app.models.rubric import Rubric

EXPECTED_TABLES = {
    "users",
    "companies",
    "people",
    "affiliations",
    "company_contacts",
    "interactions",
    "deals",
    "rubrics",
    "diligence_checklist_items",
    "deal_statuses",
    "funds",
    "investments",
    "portfolio_metrics",
    "documents",
    "tasks",
    "tags",
    "company_tags",
    "import_batches",
    "import_rows",
    "audit_logs",
    "ai_audit_logs",
    "agent_event_logs",
    "agent_policies",
    "notifications",
}


def test_all_tables_registered() -> None:
    assert EXPECTED_TABLES.issubset(set(Base.metadata.tables.keys()))


def test_soft_delete_mixin_default_and_property() -> None:
    company = Company(name="Acme")
    assert company.archived_at is None
    assert company.is_archived is False
    company.archived_at = datetime.now(UTC)
    assert company.is_archived is True


def test_company_relationships_configured() -> None:
    mapper = Company.__mapper__
    assert {"contacts", "deals", "interactions"}.issubset(mapper.relationships.keys())


def test_deal_has_rubric_one_to_one() -> None:
    rel = Deal.__mapper__.relationships["rubric"]
    assert rel.uselist is False


def test_rubric_exposes_all_15_subscores() -> None:
    columns = set(Rubric.__table__.columns.keys())
    all_subscores = {name for group in RUBRIC_SUBSCORES.values() for name in group}
    assert len(all_subscores) == 15
    assert all_subscores.issubset(columns)


def test_rubric_has_four_knockout_gates() -> None:
    columns = set(Rubric.__table__.columns.keys())
    gates = {
        "gate_rit_connection",
        "gate_thesis_alignment",
        "gate_stage_seed_to_series_a",
        "gate_tech_enabled",
    }
    assert gates.issubset(columns)
