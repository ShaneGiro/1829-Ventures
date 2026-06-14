"""Domain constants: sector taxonomy, rubric thresholds, and seed status labels.

Deal statuses are configurable in the database (see deal_status model); the labels
here are only the seed/default set used to populate that table on first run.
"""

from __future__ import annotations

from enum import StrEnum

# ─── Sector taxonomy (1829's five focus areas) ────────────────────────────────
SECTOR_TAXONOMY: tuple[str, ...] = (
    "Photonics, Imaging & Quantum",
    "Clean Tech & Energy",
    "Life Sciences & Health Tech",
    "Intelligent Systems, AI & Cyber",
    "Other",
)
DEFAULT_SECTOR = "Other"


# ─── Pipeline status lanes ────────────────────────────────────────────────────
class RelationshipStatus(StrEnum):
    IDENTIFIED = "identified"
    CONTACTED = "contacted"
    REVIEW_NEEDED = "review_needed"
    ACTIVE = "active"
    NURTURE = "nurture"
    STRATEGIC = "strategic"
    INACTIVE = "inactive"


class InvestmentStatus(StrEnum):
    SOURCED = "sourced"
    INITIAL_REVIEW = "initial_review"
    DILIGENCE = "diligence"
    IC_REVIEW = "ic_review"
    TERM_SHEET = "term_sheet"
    INVESTED = "invested"
    PASSED = "passed"
    MONITOR = "monitor"


# Seed pipeline board stages, in display order. Stored in the deal_status table so
# they can be reordered/extended at runtime without a code change.
SEED_DEAL_STATUSES: tuple[str, ...] = (
    "Outreach",
    "Intro Meeting",
    "Initial Review",
    "Diligence",
    "IC Review",
    "Term Sheet",
    "Closed/Invested",
)


# ─── Screening rubric ─────────────────────────────────────────────────────────
# Weighted categories: (key, label, weight, max_points). Total max = 100.
RUBRIC_CATEGORIES: tuple[tuple[str, str, int, int], ...] = (
    ("team", "Team (Builders)", 5, 25),
    ("tech", "Tech (Defensibility)", 4, 20),
    ("commercial", "Commercial (Efficiency)", 5, 25),
    ("rit_fit", "RIT Fit (Leverage)", 4, 20),
    ("deal_dynamics", "Deal Dynamics", 2, 10),
)

# The 15 individually-stored sub-scores (1-5 each), grouped by category.
RUBRIC_SUBSCORES: dict[str, tuple[str, ...]] = {
    "team": ("commercial_technical_balance", "coachability_grit", "talent_magnetism"),
    "tech": ("ip_protection", "external_validation", "development_stage"),
    "commercial": ("capital_efficiency", "path_to_revenue", "market_pain", "unit_economics"),
    "rit_fit": ("structural_advantage", "talent_pipeline", "mission_alignment"),
    "deal_dynamics": ("syndicate_strength", "valuation_discipline"),
}

RUBRIC_KNOCKOUT_GATES: tuple[str, ...] = (
    "rit_connection",
    "thesis_alignment",
    "stage_seed_to_series_a",
    "tech_enabled",
)

# Composite score thresholds (out of 100).
SCORE_THRESHOLD_DEEP_DILIGENCE = 80  # 80-100: move to deep diligence
SCORE_THRESHOLD_HOLD = 70  # 70-79: hold, assess fixability; <70: pass
RUBRIC_SUBSCORE_MIN = 1
RUBRIC_SUBSCORE_MAX = 5


# ─── Actor types for the audit log ────────────────────────────────────────────
class ActorType(StrEnum):
    HUMAN = "human"
    IMPORT = "import"
    SYSTEM = "system"
    AGENT = "agent"  # Ritchie


# ─── Roles (role column exists from day one; not enforced in v1) ───────────────
class Role(StrEnum):
    ADMIN = "admin"
    MANAGING_DIRECTOR = "managing_director"
    PRINCIPAL = "principal"
    ANALYST = "analyst"
    MEMBER = "member"  # default for human users in v1
    AGENT = "agent"  # Ritchie's scoped API-key identity
