"""Company repository helpers."""

from __future__ import annotations

import uuid

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.company import Company
from app.models.company_contact import CompanyContact
from app.models.tag import company_tags
from app.repositories import base


async def get_company(
    session: AsyncSession, company_id: uuid.UUID, *, include_archived: bool = False
) -> Company | None:
    return await base.get_by_id(session, Company, company_id, include_archived=include_archived)


async def list_companies(
    session: AsyncSession, *, limit: int, offset: int, include_archived: bool = False
) -> list[Company]:
    return await base.list_rows(
        session,
        Company,
        limit=limit,
        offset=offset,
        include_archived=include_archived,
        order_by=Company.name,
    )


async def count_companies(session: AsyncSession, *, include_archived: bool = False) -> int:
    return await base.count_rows(session, Company, include_archived=include_archived)


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
