"""Pipeline transitions and review-needed triage workflows."""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import UTC, date, datetime, time, timedelta
from enum import StrEnum

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.constants import ActorType, InvestmentStatus, RelationshipStatus, TaskPriority
from app.core.exceptions import NotFoundError, ValidationError
from app.models.deal import Deal
from app.models.task import Task
from app.repositories import deal_statuses as status_repo
from app.repositories import deals as deal_repo
from app.services import diligence_service


class TriageOutcome(StrEnum):
    START_REVIEW = "start_review"
    MONITOR = "monitor"
    PASS = "pass"


@dataclass(frozen=True)
class TriageResult:
    outcome: TriageOutcome
    deal: Deal
    task: Task | None = None


def next_business_day(start: date) -> date:
    candidate = start + timedelta(days=1)
    while candidate.weekday() >= 5:
        candidate += timedelta(days=1)
    return candidate


def _at_start_of_day(value: date) -> datetime:
    return datetime.combine(value, time.min, tzinfo=UTC)


async def mark_review_needed(
    session: AsyncSession,
    *,
    company_id: uuid.UUID,
    owner_id: uuid.UUID | None = None,
) -> Task:
    company = await deal_repo.get_company(session, company_id)
    if company is None:
        raise NotFoundError("Company not found")
    company.relationship_status = RelationshipStatus.REVIEW_NEEDED
    task = await deal_repo.create_task(
        session,
        title=f"Triage {company.name}",
        description="Review founder/company response and choose start review, monitor, or pass.",
        due_date=_at_start_of_day(next_business_day(datetime.now(UTC).date())),
        owner_id=owner_id,
        created_by_type=ActorType.SYSTEM,
        created_by_id=owner_id,
        company_id=company.id,
        priority=TaskPriority.HIGH,
    )
    await session.commit()
    await session.refresh(task)
    return task


async def _get_or_create_triage_deal(
    session: AsyncSession,
    *,
    company_id: uuid.UUID,
    status: InvestmentStatus,
) -> Deal:
    deal = await deal_repo.get_latest_deal_for_company(session, company_id)
    if deal is not None:
        deal.investment_status = status
        return deal

    company = await deal_repo.get_company(session, company_id)
    if company is None:
        raise NotFoundError("Company not found")
    return await deal_repo.create_deal(
        session,
        company_id=company.id,
        name=f"{company.name} Review",
        investment_status=status,
    )


async def start_investment_review(
    session: AsyncSession,
    *,
    company_id: uuid.UUID,
) -> Deal:
    company = await deal_repo.get_company(session, company_id)
    if company is None:
        raise NotFoundError("Company not found")
    company.relationship_status = RelationshipStatus.ACTIVE
    deal = await _get_or_create_triage_deal(
        session,
        company_id=company_id,
        status=InvestmentStatus.INITIAL_REVIEW,
    )
    await status_repo.seed_default_deal_statuses(session)
    initial_status = await status_repo.get_deal_status_by_name(session, "Initial Review")
    if initial_status is not None:
        deal.deal_status_id = initial_status.id
    await diligence_service.initialize_diligence(session, deal.id)
    return deal


async def monitor_company(
    session: AsyncSession,
    *,
    company_id: uuid.UUID,
    next_check_date: date,
    reason_tags: list[str],
    actor_id: uuid.UUID | None,
) -> tuple[Deal, Task]:
    if next_check_date <= datetime.now(UTC).date():
        raise ValidationError("Monitor next-check date must be in the future")
    company = await deal_repo.get_company(session, company_id)
    if company is None:
        raise NotFoundError("Company not found")

    company.relationship_status = RelationshipStatus.NURTURE
    deal = await _get_or_create_triage_deal(
        session,
        company_id=company_id,
        status=InvestmentStatus.MONITOR,
    )
    deal.decision_notes = _append_decision_note(
        deal.decision_notes,
        f"Monitor until {next_check_date.isoformat()}",
    )
    for tag_name in reason_tags:
        tag = await deal_repo.get_or_create_pass_reason_tag(session, tag_name)
        await deal_repo.attach_tag_to_company(session, company_id=company.id, tag_id=tag.id)

    task = await deal_repo.create_task(
        session,
        title=f"Re-check {company.name}",
        description="Monitor date reached; reassess whether this should return to review-needed.",
        due_date=_at_start_of_day(next_check_date),
        owner_id=actor_id,
        created_by_type=ActorType.SYSTEM,
        created_by_id=actor_id,
        company_id=company.id,
        deal_id=deal.id,
        priority=TaskPriority.MEDIUM,
    )
    return deal, task


async def pass_company(
    session: AsyncSession,
    *,
    company_id: uuid.UUID,
    reason_tags: list[str],
    notes: str | None,
) -> Deal:
    cleaned_tags = [tag.strip() for tag in reason_tags if tag.strip()]
    if not cleaned_tags:
        raise ValidationError("Pass decisions require at least one reason tag")
    company = await deal_repo.get_company(session, company_id)
    if company is None:
        raise NotFoundError("Company not found")

    company.relationship_status = RelationshipStatus.INACTIVE
    deal = await _get_or_create_triage_deal(
        session,
        company_id=company_id,
        status=InvestmentStatus.PASSED,
    )
    if notes:
        deal.decision_notes = _append_decision_note(deal.decision_notes, notes)
    for tag_name in cleaned_tags:
        tag = await deal_repo.get_or_create_pass_reason_tag(session, tag_name)
        await deal_repo.attach_tag_to_company(session, company_id=company.id, tag_id=tag.id)
    return deal


def _append_decision_note(existing: str | None, note: str) -> str:
    if not existing:
        return note
    return f"{existing}\n{note}"


async def triage_review_needed(
    session: AsyncSession,
    *,
    company_id: uuid.UUID,
    outcome: TriageOutcome,
    actor_id: uuid.UUID | None,
    reason_tags: list[str] | None = None,
    next_check_date: date | None = None,
    notes: str | None = None,
) -> TriageResult:
    company = await deal_repo.get_company(session, company_id)
    if company is None:
        raise NotFoundError("Company not found")

    if outcome == TriageOutcome.START_REVIEW:
        deal = await start_investment_review(session, company_id=company_id)
        result = TriageResult(outcome=outcome, deal=deal)
    elif outcome == TriageOutcome.MONITOR:
        if next_check_date is None:
            raise ValidationError("Monitor decisions require a next-check date")
        deal, task = await monitor_company(
            session,
            company_id=company_id,
            next_check_date=next_check_date,
            reason_tags=reason_tags or [],
            actor_id=actor_id,
        )
        result = TriageResult(outcome=outcome, deal=deal, task=task)
    elif outcome == TriageOutcome.PASS:
        deal = await pass_company(
            session,
            company_id=company_id,
            reason_tags=reason_tags or [],
            notes=notes,
        )
        result = TriageResult(outcome=outcome, deal=deal)
    else:
        raise ValidationError("Unsupported triage outcome")

    await session.commit()
    await session.refresh(result.deal)
    if result.task is not None:
        await session.refresh(result.task)
    return result


async def release_due_monitor_tasks(session: AsyncSession, due_at: datetime) -> list[Task]:
    tasks = await deal_repo.list_due_monitor_tasks(session, due_at)
    for task in tasks:
        if task.company_id is None:
            continue
        company = await deal_repo.get_company(session, task.company_id)
        if company is not None:
            company.relationship_status = RelationshipStatus.REVIEW_NEEDED
    await session.commit()
    return tasks
