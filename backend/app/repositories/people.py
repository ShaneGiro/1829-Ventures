"""People, company contact, and affiliation repository helpers."""

from __future__ import annotations

import uuid
from typing import cast

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.affiliation import Affiliation
from app.models.company_contact import CompanyContact
from app.models.person import Person
from app.repositories import base


async def get_person(
    session: AsyncSession, person_id: uuid.UUID, *, include_archived: bool = False
) -> Person | None:
    return await base.get_by_id(session, Person, person_id, include_archived=include_archived)


async def list_people(
    session: AsyncSession, *, limit: int, offset: int, include_archived: bool = False
) -> list[Person]:
    return await base.list_rows(
        session,
        Person,
        limit=limit,
        offset=offset,
        include_archived=include_archived,
        order_by=Person.full_name,
    )


async def count_people(session: AsyncSession, *, include_archived: bool = False) -> int:
    return await base.count_rows(session, Person, include_archived=include_archived)


async def create_person(session: AsyncSession, person: Person) -> Person:
    session.add(person)
    await session.flush()
    return person


async def get_contact(session: AsyncSession, contact_id: uuid.UUID) -> CompanyContact | None:
    return await base.get_by_id(session, CompanyContact, contact_id)


async def get_contact_by_pair(
    session: AsyncSession, *, company_id: uuid.UUID, person_id: uuid.UUID
) -> CompanyContact | None:
    stmt = select(CompanyContact).where(
        CompanyContact.company_id == company_id,
        CompanyContact.person_id == person_id,
    )
    return cast("CompanyContact | None", await session.scalar(stmt))


async def list_company_contacts(
    session: AsyncSession, company_id: uuid.UUID
) -> list[CompanyContact]:
    stmt = (
        select(CompanyContact)
        .where(CompanyContact.company_id == company_id)
        .order_by(
            CompanyContact.is_primary.desc(),
            CompanyContact.created_at,
        )
    )
    return list(await session.scalars(stmt))


async def create_contact(session: AsyncSession, contact: CompanyContact) -> CompanyContact:
    session.add(contact)
    await session.flush()
    return contact


async def clear_primary_contacts(session: AsyncSession, company_id: uuid.UUID) -> None:
    contacts = await list_company_contacts(session, company_id)
    for contact in contacts:
        contact.is_primary = False
    await session.flush()


async def get_affiliation(session: AsyncSession, affiliation_id: uuid.UUID) -> Affiliation | None:
    return await base.get_by_id(session, Affiliation, affiliation_id)


async def list_person_affiliations(
    session: AsyncSession, person_id: uuid.UUID
) -> list[Affiliation]:
    stmt = (
        select(Affiliation)
        .where(Affiliation.person_id == person_id)
        .order_by(Affiliation.created_at)
    )
    return list(await session.scalars(stmt))


async def create_affiliation(session: AsyncSession, affiliation: Affiliation) -> Affiliation:
    session.add(affiliation)
    await session.flush()
    return affiliation
