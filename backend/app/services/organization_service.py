"""Institutional organization and legal-entity services."""

from __future__ import annotations

import uuid
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.audit import actor_from_user
from app.core.exceptions import ConflictError, NotFoundError, PermissionDeniedError, ValidationError
from app.models.legal_entity import LegalEntity, LegalEntityRelationship
from app.models.organization import Organization, OrganizationMembership
from app.models.user import User
from app.repositories import organizations as organization_repo
from app.schemas.legal_entity import (
    LegalEntityCreate,
    LegalEntityRelationshipCreate,
    LegalEntityUpdate,
)
from app.schemas.organization import OrganizationCreate, OrganizationUpdate
from app.services import audit_service


async def require_membership(
    session: AsyncSession, organization_id: uuid.UUID, actor: User
) -> OrganizationMembership:
    membership = await organization_repo.get_membership(session, organization_id, actor.id)
    if membership is None:
        raise PermissionDeniedError("User does not have access to this organization")
    return membership


async def get_organization(
    session: AsyncSession, organization_id: uuid.UUID, actor: User
) -> Organization:
    organization = await organization_repo.get_organization(session, organization_id)
    if organization is None:
        raise NotFoundError("Organization not found")
    await require_membership(session, organization_id, actor)
    return organization


async def create_organization(
    session: AsyncSession, payload: OrganizationCreate, actor: User
) -> Organization:
    organization = Organization(
        **payload.model_dump(), base_currency=payload.base_currency.upper()
    )
    session.add(organization)
    await session.flush()
    session.add(
        OrganizationMembership(
            organization_id=organization.id,
            user_id=actor.id,
            role=actor.role,
            is_active=True,
        )
    )
    await audit_service.record_create(
        session, actor=actor_from_user(actor), entity=organization
    )
    await session.commit()
    await session.refresh(organization)
    return organization


async def update_organization(
    session: AsyncSession,
    organization_id: uuid.UUID,
    payload: OrganizationUpdate,
    actor: User,
) -> Organization:
    organization = await get_organization(session, organization_id, actor)
    updates = payload.model_dump(exclude_unset=True)
    if updates.get("name") is None and "name" in updates:
        raise ValidationError("Organization name cannot be null")
    if updates.get("base_currency") is not None:
        updates["base_currency"] = updates["base_currency"].upper()
    changes: dict[str, tuple[Any, Any]] = {}
    for field, value in updates.items():
        old_value = getattr(organization, field)
        if old_value != value:
            changes[field] = (old_value, value)
            setattr(organization, field, value)
    if changes:
        await audit_service.record_update(
            session,
            actor=actor_from_user(actor),
            entity=organization,
            changes=changes,
        )
    await session.commit()
    await session.refresh(organization)
    return organization


async def get_legal_entity(
    session: AsyncSession, entity_id: uuid.UUID, actor: User
) -> LegalEntity:
    entity = await organization_repo.get_legal_entity(session, entity_id)
    if entity is None:
        raise NotFoundError("Legal entity not found")
    await require_membership(session, entity.organization_id, actor)
    return entity


async def create_legal_entity(
    session: AsyncSession, payload: LegalEntityCreate, actor: User
) -> LegalEntity:
    await get_organization(session, payload.organization_id, actor)
    entity = LegalEntity(
        **payload.model_dump(), base_currency=payload.base_currency.upper()
    )
    session.add(entity)
    await session.flush()
    await audit_service.record_create(session, actor=actor_from_user(actor), entity=entity)
    await session.commit()
    await session.refresh(entity)
    return entity


async def update_legal_entity(
    session: AsyncSession,
    entity_id: uuid.UUID,
    payload: LegalEntityUpdate,
    actor: User,
) -> LegalEntity:
    entity = await get_legal_entity(session, entity_id, actor)
    updates = payload.model_dump(exclude_unset=True)
    if updates.get("legal_name") is None and "legal_name" in updates:
        raise ValidationError("Legal entity name cannot be null")
    if updates.get("base_currency") is not None:
        updates["base_currency"] = updates["base_currency"].upper()
    changes: dict[str, tuple[Any, Any]] = {}
    for field, value in updates.items():
        old_value = getattr(entity, field)
        if old_value != value:
            changes[field] = (old_value, value)
            setattr(entity, field, value)
    if changes:
        await audit_service.record_update(
            session, actor=actor_from_user(actor), entity=entity, changes=changes
        )
    await session.commit()
    await session.refresh(entity)
    return entity


async def create_relationship(
    session: AsyncSession,
    payload: LegalEntityRelationshipCreate,
    actor: User,
) -> LegalEntityRelationship:
    parent = await get_legal_entity(session, payload.parent_entity_id, actor)
    child = await get_legal_entity(session, payload.child_entity_id, actor)
    if parent.organization_id != child.organization_id:
        raise ValidationError("Related legal entities must belong to the same organization")
    if await organization_repo.relationship_would_create_cycle(
        session,
        parent_entity_id=parent.id,
        child_entity_id=child.id,
        as_of=payload.effective_from,
    ):
        raise ConflictError("Legal entity relationship would create a cycle")
    relationship = LegalEntityRelationship(**payload.model_dump())
    session.add(relationship)
    await session.flush()
    await audit_service.record_create(
        session, actor=actor_from_user(actor), entity=relationship
    )
    await session.commit()
    await session.refresh(relationship)
    return relationship
