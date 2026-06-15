"""Interaction repository helpers."""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from typing import cast

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.company import Company
from app.models.company_contact import CompanyContact
from app.models.interaction import Interaction
from app.models.person import Person
from app.repositories import base


@dataclass(frozen=True)
class EmailMatch:
    company_id: uuid.UUID | None = None
    person_id: uuid.UUID | None = None


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
    stmt = stmt.order_by(Interaction.occurred_at.desc().nullslast(), Interaction.created_at.desc())
    stmt = stmt.limit(limit).offset(offset)
    return list(await session.scalars(stmt))


async def count_interactions(
    session: AsyncSession,
    *,
    company_id: uuid.UUID | None = None,
    person_id: uuid.UUID | None = None,
    deal_id: uuid.UUID | None = None,
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
