"""Organization, membership, and legal-entity repository helpers."""

from __future__ import annotations

import uuid
from datetime import date
from typing import cast

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.legal_entity import LegalEntity, LegalEntityRelationship
from app.models.organization import Organization, OrganizationMembership


async def get_organization(
    session: AsyncSession, organization_id: uuid.UUID
) -> Organization | None:
    stmt = select(Organization).where(
        Organization.id == organization_id, Organization.archived_at.is_(None)
    )
    return cast("Organization | None", await session.scalar(stmt))


async def list_organizations_for_user(
    session: AsyncSession, user_id: uuid.UUID, *, limit: int, offset: int
) -> list[Organization]:
    stmt = (
        select(Organization)
        .join(
            OrganizationMembership,
            OrganizationMembership.organization_id == Organization.id,
        )
        .where(
            OrganizationMembership.user_id == user_id,
            OrganizationMembership.is_active.is_(True),
            Organization.archived_at.is_(None),
        )
        .order_by(Organization.name)
        .limit(limit)
        .offset(offset)
    )
    return list(await session.scalars(stmt))


async def count_organizations_for_user(session: AsyncSession, user_id: uuid.UUID) -> int:
    stmt = (
        select(func.count())
        .select_from(OrganizationMembership)
        .join(Organization, Organization.id == OrganizationMembership.organization_id)
        .where(
            OrganizationMembership.user_id == user_id,
            OrganizationMembership.is_active.is_(True),
            Organization.archived_at.is_(None),
        )
    )
    return int(await session.scalar(stmt) or 0)


async def get_membership(
    session: AsyncSession, organization_id: uuid.UUID, user_id: uuid.UUID
) -> OrganizationMembership | None:
    stmt = select(OrganizationMembership).where(
        OrganizationMembership.organization_id == organization_id,
        OrganizationMembership.user_id == user_id,
        OrganizationMembership.is_active.is_(True),
    )
    return cast("OrganizationMembership | None", await session.scalar(stmt))


async def get_legal_entity(
    session: AsyncSession, entity_id: uuid.UUID, *, include_archived: bool = False
) -> LegalEntity | None:
    stmt = select(LegalEntity).where(LegalEntity.id == entity_id)
    if not include_archived:
        stmt = stmt.where(LegalEntity.archived_at.is_(None))
    return cast("LegalEntity | None", await session.scalar(stmt))


async def list_legal_entities(
    session: AsyncSession,
    organization_id: uuid.UUID,
    *,
    limit: int,
    offset: int,
) -> list[LegalEntity]:
    stmt = (
        select(LegalEntity)
        .where(
            LegalEntity.organization_id == organization_id,
            LegalEntity.archived_at.is_(None),
        )
        .order_by(LegalEntity.legal_name)
        .limit(limit)
        .offset(offset)
    )
    return list(await session.scalars(stmt))


async def count_legal_entities(session: AsyncSession, organization_id: uuid.UUID) -> int:
    stmt = (
        select(func.count())
        .select_from(LegalEntity)
        .where(
            LegalEntity.organization_id == organization_id,
            LegalEntity.archived_at.is_(None),
        )
    )
    return int(await session.scalar(stmt) or 0)


async def list_relationships(
    session: AsyncSession, organization_id: uuid.UUID
) -> list[LegalEntityRelationship]:
    stmt = (
        select(LegalEntityRelationship)
        .join(
            LegalEntity,
            LegalEntity.id == LegalEntityRelationship.parent_entity_id,
        )
        .where(LegalEntity.organization_id == organization_id)
        .order_by(
            LegalEntityRelationship.effective_from,
            LegalEntityRelationship.created_at,
        )
    )
    return list(await session.scalars(stmt))


async def relationship_would_create_cycle(
    session: AsyncSession,
    *,
    parent_entity_id: uuid.UUID,
    child_entity_id: uuid.UUID,
    as_of: date,
) -> bool:
    """Return whether parent is reachable from child through active relationships."""
    current = {child_entity_id}
    visited: set[uuid.UUID] = set()
    while current:
        if parent_entity_id in current:
            return True
        visited.update(current)
        stmt = select(LegalEntityRelationship.child_entity_id).where(
            LegalEntityRelationship.parent_entity_id.in_(current),
            LegalEntityRelationship.effective_from <= as_of,
            (
                LegalEntityRelationship.effective_to.is_(None)
                | (LegalEntityRelationship.effective_to >= as_of)
            ),
        )
        current = set(await session.scalars(stmt)) - visited
    return False
