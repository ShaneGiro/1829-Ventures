"""Interaction repository helpers."""

from __future__ import annotations

import difflib
import uuid
from dataclasses import dataclass
from typing import cast

from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.company import Company
from app.models.company_contact import CompanyContact
from app.models.interaction import Interaction
from app.models.person import Person
from app.repositories import base

# Minimum lexical similarity for a fuzzy company suggestion to be surfaced.
FUZZY_MATCH_THRESHOLD = 0.6
FUZZY_CANDIDATE_LIMIT = 25


@dataclass(frozen=True)
class EmailMatch:
    company_id: uuid.UUID | None = None
    person_id: uuid.UUID | None = None


@dataclass(frozen=True)
class FuzzyCompanySuggestion:
    """A low-confidence company candidate for an otherwise-unmatched email.

    Surfaced in the review queue to assist manual linking; never auto-attached,
    so human-curated relationships remain the source of truth.
    """

    company_id: uuid.UUID
    company_name: str
    confidence: float
    reason: str


def _normalize_email(value: str | None) -> str | None:
    if not value:
        return None
    normalized = value.strip().lower()
    return normalized or None


def _email_domain(email: str | None) -> str | None:
    normalized = _normalize_email(email)
    if normalized is None or "@" not in normalized:
        return None
    return normalized.rsplit("@", 1)[1]


def _domain_root(domain: str | None) -> str | None:
    """Strip the TLD: 'startup.com' -> 'startup', 'sub.acme.io' -> 'acme'."""
    if not domain:
        return None
    parts = domain.split(".")
    if len(parts) >= 2:
        return parts[-2]
    return parts[0] or None


def _similarity(a: str, b: str) -> float:
    return difflib.SequenceMatcher(None, a.lower(), b.lower()).ratio()


def score_company_candidate(root: str, *, name: str, domain: str | None) -> float:
    """Best similarity of the sender domain root against a company's name/domain.

    Pure function (no I/O) so the ranking is unit-testable on its own.
    """
    scores = [_similarity(root, name)]
    # Token-level: catch "startup" vs "Startup Labs Inc".
    scores.extend(_similarity(root, token) for token in name.split())
    candidate_domain_root = _domain_root(domain)
    if candidate_domain_root:
        scores.append(_similarity(root, candidate_domain_root))
    return max(scores) if scores else 0.0


async def get_interaction(
    session: AsyncSession, interaction_id: uuid.UUID, *, include_archived: bool = False
) -> Interaction | None:
    return await base.get_by_id(
        session, Interaction, interaction_id, include_archived=include_archived
    )


async def list_interactions(
    session: AsyncSession,
    *,
    limit: int,
    offset: int,
    company_id: uuid.UUID | None = None,
    person_id: uuid.UUID | None = None,
    deal_id: uuid.UUID | None = None,
    interaction_type: str | None = None,
    channel: str | None = None,
    direction: str | None = None,
    follow_up_status: str | None = None,
    created_by_id: uuid.UUID | None = None,
    include_archived: bool = False,
) -> list[Interaction]:
    stmt = select(Interaction)
    if not include_archived:
        stmt = stmt.where(Interaction.archived_at.is_(None))
    if company_id is not None:
        stmt = stmt.where(Interaction.company_id == company_id)
    if person_id is not None:
        stmt = stmt.where(Interaction.person_id == person_id)
    if deal_id is not None:
        stmt = stmt.where(Interaction.deal_id == deal_id)
    if interaction_type is not None:
        stmt = stmt.where(Interaction.interaction_type == interaction_type)
    if channel is not None:
        stmt = stmt.where(Interaction.channel == channel)
    if direction is not None:
        stmt = stmt.where(Interaction.direction == direction)
    if follow_up_status is not None:
        stmt = stmt.where(Interaction.follow_up_status == follow_up_status)
    if created_by_id is not None:
        stmt = stmt.where(Interaction.created_by_id == created_by_id)
    stmt = stmt.order_by(Interaction.occurred_at.desc().nullslast(), Interaction.created_at.desc())
    stmt = stmt.limit(limit).offset(offset)
    return list(await session.scalars(stmt))


async def count_interactions(
    session: AsyncSession,
    *,
    company_id: uuid.UUID | None = None,
    person_id: uuid.UUID | None = None,
    deal_id: uuid.UUID | None = None,
    interaction_type: str | None = None,
    channel: str | None = None,
    direction: str | None = None,
    follow_up_status: str | None = None,
    created_by_id: uuid.UUID | None = None,
    include_archived: bool = False,
) -> int:
    from sqlalchemy import func

    stmt = select(func.count()).select_from(Interaction)
    if not include_archived:
        stmt = stmt.where(Interaction.archived_at.is_(None))
    if company_id is not None:
        stmt = stmt.where(Interaction.company_id == company_id)
    if person_id is not None:
        stmt = stmt.where(Interaction.person_id == person_id)
    if deal_id is not None:
        stmt = stmt.where(Interaction.deal_id == deal_id)
    if interaction_type is not None:
        stmt = stmt.where(Interaction.interaction_type == interaction_type)
    if channel is not None:
        stmt = stmt.where(Interaction.channel == channel)
    if direction is not None:
        stmt = stmt.where(Interaction.direction == direction)
    if follow_up_status is not None:
        stmt = stmt.where(Interaction.follow_up_status == follow_up_status)
    if created_by_id is not None:
        stmt = stmt.where(Interaction.created_by_id == created_by_id)
    return int(await session.scalar(stmt) or 0)


async def create_interaction(session: AsyncSession, interaction: Interaction) -> Interaction:
    session.add(interaction)
    await session.flush()
    return interaction


async def find_email_match(session: AsyncSession, sender_email: str) -> EmailMatch:
    normalized = _normalize_email(sender_email)
    if normalized is None:
        return EmailMatch()

    person = await session.scalar(
        select(Person).where(
            func.lower(Person.email) == normalized,
            Person.archived_at.is_(None),
        )
    )
    if person is not None:
        contact = await session.scalar(
            select(CompanyContact).where(CompanyContact.person_id == person.id).limit(1)
        )
        return EmailMatch(
            company_id=contact.company_id if contact is not None else None,
            person_id=person.id,
        )

    domain = _email_domain(normalized)
    if domain is None:
        return EmailMatch()
    company = await session.scalar(
        select(Company).where(
            func.lower(Company.domain) == domain,
            Company.archived_at.is_(None),
        )
    )
    return EmailMatch(company_id=company.id if company is not None else None)


async def suggest_company_match(
    session: AsyncSession, sender_email: str
) -> FuzzyCompanySuggestion | None:
    """AI-assisted fuzzy fallback for emails the deterministic matcher misses.

    Lexical (difflib) only — no synchronous LLM/embedding calls, so the request
    path stays fast. Returns at most one candidate above FUZZY_MATCH_THRESHOLD.
    Callers must treat this as a suggestion for manual linking, not a match.
    """
    domain = _email_domain(sender_email)
    root = _domain_root(domain)
    if not root or len(root) < 2:
        return None

    # Bound the candidate set with a cheap SQL prefilter before scoring in Python.
    pattern = f"%{root}%"
    candidates = list(
        await session.scalars(
            select(Company)
            .where(
                Company.archived_at.is_(None),
                or_(
                    func.lower(Company.name).ilike(pattern),
                    func.lower(Company.domain).ilike(pattern),
                ),
            )
            .limit(FUZZY_CANDIDATE_LIMIT)
        )
    )

    best: FuzzyCompanySuggestion | None = None
    for company in candidates:
        score = score_company_candidate(root, name=company.name, domain=company.domain)
        if score >= FUZZY_MATCH_THRESHOLD and (best is None or score > best.confidence):
            best = FuzzyCompanySuggestion(
                company_id=company.id,
                company_name=company.name,
                confidence=round(score, 3),
                reason=f"Sender domain '{domain}' ~ company '{company.name}'",
            )
    return best


async def get_company_for_email_ingestion(
    session: AsyncSession, company_id: uuid.UUID
) -> Company | None:
    return cast(
        "Company | None",
        await session.scalar(select(Company).where(Company.id == company_id)),
    )


async def list_email_review_queue(
    session: AsyncSession,
    *,
    limit: int,
    offset: int,
) -> list[Interaction]:
    stmt = (
        select(Interaction)
        .where(
            Interaction.interaction_type == "email",
            Interaction.archived_at.is_(None),
            Interaction.provenance["review_status"].astext.in_(["parse_failed", "unmatched"]),
        )
        .order_by(Interaction.created_at.desc())
        .limit(limit)
        .offset(offset)
    )
    return list(await session.scalars(stmt))


async def count_email_review_queue(session: AsyncSession) -> int:
    stmt = (
        select(func.count())
        .select_from(Interaction)
        .where(
            Interaction.interaction_type == "email",
            Interaction.archived_at.is_(None),
            Interaction.provenance["review_status"].astext.in_(["parse_failed", "unmatched"]),
        )
    )
    return int(await session.scalar(stmt) or 0)
