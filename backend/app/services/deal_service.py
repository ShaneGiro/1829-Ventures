"""Deal CRUD and opportunity-level business rules."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundError
from app.models.deal import Deal
from app.repositories import deal_statuses as status_repo
from app.repositories import deals as deal_repo
from app.services import diligence_service


async def list_deals(
    session: AsyncSession,
    *,
    limit: int,
    offset: int,
    company_id: uuid.UUID | None = None,
) -> tuple[list[Deal], int]:
    deals = await deal_repo.list_deals(session, limit=limit, offset=offset, company_id=company_id)
    total = await deal_repo.count_deals(session, company_id=company_id)
    return deals, total


async def get_deal(session: AsyncSession, deal_id: uuid.UUID) -> Deal:
    deal = await deal_repo.get_deal(session, deal_id)
    if deal is None:
        raise NotFoundError("Deal not found")
    return deal


async def create_deal(
    session: AsyncSession,
    *,
    values: dict[str, Any],
    initialize_diligence: bool = False,
) -> Deal:
    company = await deal_repo.get_company(session, values["company_id"])
    if company is None:
        raise NotFoundError("Company not found")
    deal = await deal_repo.create_deal(session, **values)
    if deal.deal_status_id is None:
        await status_repo.seed_default_deal_statuses(session)
        initial_status = await status_repo.get_deal_status_by_name(session, "Initial Review")
        if initial_status is not None:
            deal.deal_status_id = initial_status.id
    if initialize_diligence:
        await diligence_service.initialize_diligence(session, deal.id)
    await session.commit()
    await session.refresh(deal)
    return deal


async def update_deal(
    session: AsyncSession,
    *,
    deal_id: uuid.UUID,
    values: dict[str, Any],
) -> Deal:
    deal = await get_deal(session, deal_id)
    if "deal_status_id" in values and values["deal_status_id"] is not None:
        status = await status_repo.get_deal_status(session, values["deal_status_id"])
        if status is None:
            raise NotFoundError("Deal status not found")
    for field, value in values.items():
        setattr(deal, field, value)
    await session.commit()
    await session.refresh(deal)
    return deal


async def archive_deal(session: AsyncSession, deal_id: uuid.UUID) -> Deal:
    deal = await get_deal(session, deal_id)
    deal.archived_at = datetime.now(UTC)
    await session.commit()
    await session.refresh(deal)
    return deal
