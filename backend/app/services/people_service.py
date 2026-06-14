"""People, company contacts, and RIT affiliation service."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.audit import actor_from_user
from app.core.exceptions import ConflictError, NotFoundError, ValidationError
from app.models.affiliation import Affiliation
from app.models.company_contact import CompanyContact
from app.models.person import Person
from app.models.user import User
from app.repositories import people as people_repo
from app.schemas.company_contact import CompanyContactCreate, CompanyContactUpdate
from app.schemas.person import AffiliationCreate, AffiliationUpdate, PersonCreate, PersonUpdate
from app.services import audit_service, company_service


async def get_person(
    session: AsyncSession, person_id: uuid.UUID, *, include_archived: bool = False
) -> Person:
    person = await people_repo.get_person(session, person_id, include_archived=include_archived)
    if person is None:
        raise NotFoundError("Person not found")
    return person


async def create_person(session: AsyncSession, payload: PersonCreate, actor: User) -> Person:
    person = Person(**payload.model_dump(exclude_none=True))
    await people_repo.create_person(session, person)
    await audit_service.record_create(session, actor=actor_from_user(actor), entity=person)
    await session.commit()
    await session.refresh(person)
    return person


async def update_person(
    session: AsyncSession, person_id: uuid.UUID, payload: PersonUpdate, actor: User
) -> Person:
    person = await get_person(session, person_id)
    updates = payload.model_dump(exclude_unset=True)
    if "full_name" in updates and updates["full_name"] is None:
        raise ValidationError("full_name cannot be null")
    changes: dict[str, tuple[Any, Any]] = {}
    for field, value in updates.items():
        old_value = getattr(person, field)
        if old_value != value:
            changes[field] = (old_value, value)
            setattr(person, field, value)
    if changes:
        await audit_service.record_update(
            session, actor=actor_from_user(actor), entity=person, changes=changes
        )
    await session.commit()
    await session.refresh(person)
    return person


async def archive_person(session: AsyncSession, person_id: uuid.UUID, actor: User) -> Person:
    person = await get_person(session, person_id)
    old_snapshot = audit_service.snapshot_model(person)
    person.archived_at = datetime.now(UTC)
    await audit_service.record_archive(
        session,
        actor=actor_from_user(actor),
        entity=person,
        old_snapshot=old_snapshot,
    )
    await session.commit()
    await session.refresh(person)
    return person


async def create_company_contact(
    session: AsyncSession, payload: CompanyContactCreate, actor: User
) -> CompanyContact:
    company = await company_service.get_company(session, payload.company_id)
    await get_person(session, payload.person_id)
    existing = await people_repo.get_contact_by_pair(
        session, company_id=payload.company_id, person_id=payload.person_id
    )
    if existing is not None:
        raise ConflictError("Company contact already exists")
    if payload.is_primary:
        await people_repo.clear_primary_contacts(session, payload.company_id)
    contact = CompanyContact(**payload.model_dump())
    await people_repo.create_contact(session, contact)
    await company_service.refresh_completeness(session, company)
    await audit_service.record_create(session, actor=actor_from_user(actor), entity=contact)
    await session.commit()
    await session.refresh(contact)
    return contact


async def update_company_contact(
    session: AsyncSession,
    contact_id: uuid.UUID,
    payload: CompanyContactUpdate,
    actor: User,
) -> CompanyContact:
    contact = await people_repo.get_contact(session, contact_id)
    if contact is None:
        raise NotFoundError("Company contact not found")
    updates = payload.model_dump(exclude_unset=True)
    if "is_primary" in updates and updates["is_primary"] is None:
        raise ValidationError("is_primary cannot be null")
    if updates.get("is_primary") is True:
        await people_repo.clear_primary_contacts(session, contact.company_id)
    changes: dict[str, tuple[Any, Any]] = {}
    for field, value in updates.items():
        old_value = getattr(contact, field)
        if old_value != value:
            changes[field] = (old_value, value)
            setattr(contact, field, value)
    company = await company_service.get_company(session, contact.company_id)
    await company_service.refresh_completeness(session, company)
    if changes:
        await audit_service.record_update(
            session, actor=actor_from_user(actor), entity=contact, changes=changes
        )
    await session.commit()
    await session.refresh(contact)
    return contact


async def create_affiliation(
    session: AsyncSession, payload: AffiliationCreate, actor: User
) -> Affiliation:
    await get_person(session, payload.person_id)
    affiliation = Affiliation(**payload.model_dump(exclude_none=True))
    await people_repo.create_affiliation(session, affiliation)
    await audit_service.record_create(session, actor=actor_from_user(actor), entity=affiliation)
    await session.commit()
    await session.refresh(affiliation)
    return affiliation


async def update_affiliation(
    session: AsyncSession,
    affiliation_id: uuid.UUID,
    payload: AffiliationUpdate,
    actor: User,
) -> Affiliation:
    affiliation = await people_repo.get_affiliation(session, affiliation_id)
    if affiliation is None:
        raise NotFoundError("Affiliation not found")
    updates = payload.model_dump(exclude_unset=True)
    changes: dict[str, tuple[Any, Any]] = {}
    for field, value in updates.items():
        old_value = getattr(affiliation, field)
        if old_value != value:
            changes[field] = (old_value, value)
            setattr(affiliation, field, value)
    if changes:
        await audit_service.record_update(
            session, actor=actor_from_user(actor), entity=affiliation, changes=changes
        )
    await session.commit()
    await session.refresh(affiliation)
    return affiliation
