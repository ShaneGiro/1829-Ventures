"""Domain constants: sector taxonomy, rubric thresholds, and seed status labels.

Deal statuses are configurable in the database (see deal_status model); the labels
here are only the seed/default set used to populate that table on first run.
"""

from __future__ import annotations

from enum import StrEnum

DEFAULT_RIT_ORGANIZATION_ID = "18290000-0000-4000-8000-000000000001"

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


class AlumniFounderStatus(StrEnum):
    ACTIVE = "active"
    UNCLEAR = "unclear"
    INACTIVE = "inactive"
    NOT_FOUND = "not_found"
    UNVERIFIED = "unverified"


class OperationalStatus(StrEnum):
    OPERATIONAL = "operational"
    UNCLEAR = "unclear"
    NOT_OPERATIONAL = "not_operational"
    UNVERIFIED = "unverified"


# Seed pipeline board stages, in display order. Stored in the deal_status table so
# they can be reordered/extended at runtime without a code change.
SEED_DEAL_STATUSES: tuple[str, ...] = (
    "Initial Review",
    "Outreach",
    "Intro Meeting",
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


# ─── Company completeness (v1 tracked fields) ─────────────────────────────────
# Deal diligence/rubric fields intentionally excluded — they belong to deals.
COMPANY_COMPLETENESS_FIELDS: tuple[str, ...] = (
    "website",
    "description",
    "sector",
    "location",
    "primary_contact",
    "relationship_status",
    "tags",
)


# ─── Interactions ─────────────────────────────────────────────────────────────
class InteractionType(StrEnum):
    EMAIL = "email"
    CALL = "call"
    MEETING = "meeting"
    NOTE = "note"
    INTRODUCTION = "introduction"
    DILIGENCE = "diligence"
    TOUCHPOINT = "touchpoint"


class InteractionDirection(StrEnum):
    INBOUND = "inbound"
    OUTBOUND = "outbound"
    INTERNAL = "internal"


class FollowUpStatus(StrEnum):
    NONE = "none"
    NEEDED = "needed"
    SCHEDULED = "scheduled"
    COMPLETE = "complete"


# ─── Tasks ────────────────────────────────────────────────────────────────────
class TaskStatus(StrEnum):
    OPEN = "open"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class TaskPriority(StrEnum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"


# ─── Tags ─────────────────────────────────────────────────────────────────────
class TagKind(StrEnum):
    USER = "user"  # created during normal work
    SYSTEM = "system"  # protected, controlled for analytics
    PASS_REASON = "pass_reason"  # required when passing a company/deal


# ─── Documents ────────────────────────────────────────────────────────────────
class DocumentSource(StrEnum):
    UPLOAD = "upload"
    EMAIL = "email"
    DEALROOM = "dealroom"
    EXTERNAL_LINK = "external_link"


class DocumentStatus(StrEnum):
    PENDING = "pending"
    CONFIRMED = "confirmed"
    REJECTED = "rejected"


ALLOWED_DOCUMENT_EXTENSIONS = frozenset(
    {
        ".csv",
        ".doc",
        ".docx",
        ".jpeg",
        ".jpg",
        ".markdown",
        ".md",
        ".pdf",
        ".png",
        ".txt",
        ".xls",
        ".xlsx",
    }
)
ALLOWED_DOCUMENT_MIME_TYPES = frozenset(
    {
        "application/msword",
        "application/pdf",
        "application/vnd.ms-excel",
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        "image/jpeg",
        "image/png",
        "text/csv",
        "text/markdown",
        "text/plain",
    }
)


# ─── Notifications ────────────────────────────────────────────────────────────
class NotificationChannel(StrEnum):
    EMAIL = "email"
    SLACK = "slack"  # adapter slot reserved for v1


# ─── Imports ──────────────────────────────────────────────────────────────────
class ImportStatus(StrEnum):
    UPLOADED = "uploaded"
    PREVIEWING = "previewing"
    PARTIALLY_COMMITTED = "partially_committed"
    COMMITTED = "committed"
    FAILED = "failed"


class ImportRowStatus(StrEnum):
    PENDING = "pending"
    MATCHED = "matched"
    CREATED = "created"
    CONFLICT = "conflict"
    SKIPPED = "skipped"
    COMMITTED = "committed"


# ─── Funds ────────────────────────────────────────────────────────────────────
class FundStatus(StrEnum):
    ACTIVE = "active"
    CLOSED = "closed"


class OutreachCandidateListStatus(StrEnum):
    ACTIVE = "active"
    COMPLETED = "completed"
    ARCHIVED = "archived"


class OutreachCandidateStatus(StrEnum):
    NEW = "new"
    READY_TO_CONTACT = "ready_to_contact"
    CONTACTED = "contacted"
    FOLLOW_UP_NEEDED = "follow_up_needed"
    MEETING_SCHEDULED = "meeting_scheduled"
    REVIEW_NEEDED = "review_needed"
    DEFERRED = "deferred"
    NOT_RELEVANT = "not_relevant"


class OrganizationStatus(StrEnum):
    ACTIVE = "active"
    INACTIVE = "inactive"


class LegalEntityType(StrEnum):
    FUND = "fund"
    GENERAL_PARTNER = "general_partner"
    MANAGEMENT_COMPANY = "management_company"
    SPV = "spv"
    BLOCKER = "blocker"
    FEEDER = "feeder"
    WAREHOUSING = "warehousing"
    OTHER = "other"


class LegalEntityStatus(StrEnum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    DISSOLVED = "dissolved"


class LegalEntityRelationshipType(StrEnum):
    OWNS = "owns"
    CONTROLS = "controls"
    MANAGES = "manages"
    GENERAL_PARTNER_OF = "general_partner_of"
    FEEDS_INTO = "feeds_into"
    OTHER = "other"


# ─── Diligence ────────────────────────────────────────────────────────────────
class DiligenceItemStatus(StrEnum):
    NOT_STARTED = "not_started"
    IN_PROGRESS = "in_progress"
    COMPLETE = "complete"
    NOT_APPLICABLE = "not_applicable"


# ─── Ritchie agent governance ─────────────────────────────────────────────────
class PolicyState(StrEnum):
    AUTHORIZED = "authorized"  # Ritchie executes directly, fully audited
    BLOCKED = "blocked"  # rejected at the policy gate, logged as policy_blocked


class AgentEventStatus(StrEnum):
    PENDING = "pending"
    PROCESSING = "processing"
    PROCESSED = "processed"
    POLICY_BLOCKED = "policy_blocked"
    AGENT_UNAVAILABLE = "agent_unavailable"
    FAILED = "failed"


class AiWriteStatus(StrEnum):
    PENDING = "pending"  # intent recorded before the canonical write
    COMMITTED = "committed"
    FAILED = "failed"


# Tools whose writes are blocked by default until a human authorizes them.
DEFAULT_BLOCKED_TOOLS: tuple[str, ...] = (
    "update_investment_amount",
    "update_valuation",
    "update_ownership",
    "update_deal_stage",
    "update_legal_terms",
    "record_investment_recommendation",
    "update_portfolio_mark",
    "update_rubric_score",
)


# Embedding dimensionality for pgvector columns (all-MiniLM-L6-v2 = 384).
EMBEDDING_DIM = 384
