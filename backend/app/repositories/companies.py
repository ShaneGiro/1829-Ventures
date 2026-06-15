"""Company repository helpers."""

from __future__ import annotations

import uuid

from sqlalchemy import ColumnElement, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.company import Company
from app.models.company_contact import CompanyContact
from app.models.tag import company_tags
from app.repositories import base


def _search_filter(search: str) -> ColumnElement[bool]:
    """Case-insensitive match across name, domain, and website."""
    like = f"%{search.strip()}%"
    return or_(
        Company.name.ilike(like),
        Company.domain.ilike(like),
        Company.website.ilike(like),
    )


async def get_company(
    session: AsyncSession, company_id: uuid.UUID, *, include_archived: bool = False
) -> Company | None:
    return await base.get_by_id(session, Company, company_id, include_archived=include_archived)


async def list_companies(
    session: AsyncSession,
    *,
    limit: int,
    offset: int,
    include_archived: bool = False,
    search: str | None = None,
) -> list[Company]:
    if not (search and search.strip()):
        return await base.list_rows(
            session,
            Company,
            limit=limit,
            offset=offset,
            include_archived=include_archived,
            order_by=Company.name,
        )
    stmt = select(Company).where(_search_filter(search))
    if not include_archived:
        stmt = stmt.where(Company.archived_at.is_(None))
    stmt = stmt.order_by(Company.name).limit(limit).offset(offset)
    return list(await session.scalars(stmt))


async def search_company_ids(
    session: AsyncSession,
    *,
    search: str,
    limit: int,
    include_archived: bool = False,
) -> list[uuid.UUID]:
    """Exact/substring matches (name, domain, website), ordered by name."""
    stmt = select(Company.id).where(_search_filter(search))
    if not include_archived:
        stmt = stmt.where(Company.archived_at.is_(None))
    stmt = stmt.order_by(Company.name).limit(limit)
    return list(await session.scalars(stmt))


async def get_companies_by_ids(session: AsyncSession, ids: list[uuid.UUID]) -> list[Company]:
    """Fetch companies by id, preserving the order of ``ids``."""
    if not ids:
        return []
    rows = list(await session.scalars(select(Company).where(Company.id.in_(ids))))
    by_id = {company.id: company for company in rows}
    return [by_id[cid] for cid in ids if cid in by_id]


async def count_companies(
    session: AsyncSession, *, include_archived: bool = False, search: str | None = None
) -> int:
    if not (search and search.strip()):
        return await base.count_rows(session, Company, include_archived=include_archived)
    stmt = select(func.count()).select_from(Company).where(_search_filter(search))
    if not include_archived:
        stmt = stmt.where(Company.archived_at.is_(None))
    return int(await session.scalar(stmt) or 0)


async def create_company(session: AsyncSession, company: Company) -> Company:
    session.add(company)
    await session.flush()
    return company


async def has_primary_contact(session: AsyncSession, company_id: uuid.UUID) -> bool:
    stmt = select(CompanyContact.id).where(
        CompanyContact.company_id == company_id,
        CompanyContact.is_primary.is_(True),
    )
    return await session.scalar(stmt) is not None


async def count_company_tags(session: AsyncSession, company_id: uuid.UUID) -> int:
    stmt = (
        select(func.count())
        .select_from(company_tags)
        .where(company_tags.c.company_id == company_id)
    )
    return int(await session.scalar(stmt) or 0)
