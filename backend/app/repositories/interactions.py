"""Interaction repository helpers."""

from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.interaction import Interaction
from app.repositories import base


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
