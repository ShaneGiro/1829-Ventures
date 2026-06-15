"""Diligence checklist and 1829 screening rubric behavior."""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.constants import (
    RUBRIC_CATEGORIES,
    RUBRIC_KNOCKOUT_GATES,
    RUBRIC_SUBSCORE_MAX,
    RUBRIC_SUBSCORE_MIN,
    RUBRIC_SUBSCORES,
    SCORE_THRESHOLD_DEEP_DILIGENCE,
    SCORE_THRESHOLD_HOLD,
    DiligenceItemStatus,
    InvestmentStatus,
)
from app.core.exceptions import NotFoundError, ValidationError
from app.models.deal import Deal
from app.models.diligence_checklist_item import DiligenceChecklistItem
from app.models.rubric import Rubric
from app.repositories import deal_statuses as status_repo
from app.repositories import deals as deal_repo

DEFAULT_DILIGENCE_CHECKLIST: tuple[str, ...] = (
    "Founder and RIT connection confirmed",
    "Thesis alignment documented",
    "Round and stage verified",
    "Technology/IP diligence collected",
    "Commercial traction reviewed",
    "Reference calls completed",
    "Investment memo prepared",
)


@dataclass(frozen=True)
class RubricComputation:
    composite_score: float | None
    recommendation: str | None
    category_scores: dict[str, float | None]
    knockout_passed: bool | None


def knockout_gate_field(gate: str) -> str:
    return f"gate_{gate}"


def all_subscore_fields() -> tuple[str, ...]:
    return tuple(field for fields in RUBRIC_SUBSCORES.values() for field in fields)


def _all_gates_answered(rubric: Rubric) -> bool:
    return all(
        getattr(rubric, knockout_gate_field(gate)) is not None for gate in RUBRIC_KNOCKOUT_GATES
    )


def _all_gates_passed(rubric: Rubric) -> bool:
    return all(getattr(rubric, knockout_gate_field(gate)) is True for gate in RUBRIC_KNOCKOUT_GATES)


def _score_value(rubric: Rubric, field: str) -> int | None:
    value = getattr(rubric, field)
    if value is None:
        return None
    if not RUBRIC_SUBSCORE_MIN <= value <= RUBRIC_SUBSCORE_MAX:
        raise ValidationError(f"{field} must be between 1 and 5")
    return int(value)


def compute_rubric(rubric: Rubric) -> RubricComputation:
    """Compute category scores and composite from the 15 stored sub-scores.

    Category score = average of the category's sub-scores, multiplied by the
    category weight. This preserves the planned max points per category.
    """
    if _all_gates_answered(rubric) and not _all_gates_passed(rubric):
        return RubricComputation(
            composite_score=None,
            recommendation="pass_knockout",
            category_scores={key: None for key, _, _, _ in RUBRIC_CATEGORIES},
            knockout_passed=False,
        )

    category_scores: dict[str, float | None] = {}
    composite = 0.0
    complete = True
    for key, _, weight, _ in RUBRIC_CATEGORIES:
        scores = [_score_value(rubric, field) for field in RUBRIC_SUBSCORES[key]]
        if any(score is None for score in scores):
            category_scores[key] = None
            complete = False
            continue
        category_score = (
            sum(score for score in scores if score is not None) / len(scores)
        ) * weight
        category_scores[key] = round(category_score, 2)
        composite += category_score

    if not complete or not _all_gates_passed(rubric):
        return RubricComputation(
            composite_score=None,
            recommendation=None,
            category_scores=category_scores,
            knockout_passed=True if _all_gates_passed(rubric) else None,
        )

    rounded = round(composite, 2)
    if rounded >= SCORE_THRESHOLD_DEEP_DILIGENCE:
        recommendation = "deep_diligence"
    elif rounded >= SCORE_THRESHOLD_HOLD:
        recommendation = "hold"
    else:
        recommendation = "pass"
    return RubricComputation(
        composite_score=rounded,
        recommendation=recommendation,
        category_scores=category_scores,
        knockout_passed=True,
    )


async def initialize_diligence(
    session: AsyncSession,
    deal_id: uuid.UUID,
) -> tuple[Rubric, list[DiligenceChecklistItem]]:
    deal = await deal_repo.get_deal(session, deal_id)
    if deal is None:
        raise NotFoundError("Deal not found")

    rubric = await deal_repo.get_rubric_for_deal(session, deal_id)
    if rubric is None:
        rubric = await deal_repo.create_rubric(session, deal_id)

    items = await deal_repo.list_diligence_items(session, deal_id)
    if not items:
        items = await deal_repo.create_diligence_items(
            session,
            deal_id=deal_id,
            labels=DEFAULT_DILIGENCE_CHECKLIST,
        )
    await session.flush()
    return rubric, items


async def get_rubric(session: AsyncSession, deal_id: uuid.UUID) -> Rubric:
    await initialize_diligence(session, deal_id)
    rubric = await deal_repo.get_rubric_for_deal(session, deal_id)
    if rubric is None:
        raise NotFoundError("Rubric not found")
    return rubric


async def update_rubric(
    session: AsyncSession,
    *,
    deal_id: uuid.UUID,
    values: dict[str, Any],
) -> Rubric:
    rubric = await get_rubric(session, deal_id)
    writable = (
        set(all_subscore_fields())
        | {knockout_gate_field(gate) for gate in RUBRIC_KNOCKOUT_GATES}
        | {"notes"}
    )
    for field, value in values.items():
        if field not in writable:
            continue
        setattr(rubric, field, value)

    computation = compute_rubric(rubric)
    rubric.composite_score = computation.composite_score
    await session.commit()
    await session.refresh(rubric)
    return rubric


async def get_company_rubric(session: AsyncSession, company_id: uuid.UUID) -> Rubric:
    deal = await _get_or_create_company_screening_deal(session, company_id)
    return await get_rubric(session, deal.id)


async def update_company_rubric(
    session: AsyncSession,
    *,
    company_id: uuid.UUID,
    values: dict[str, Any],
) -> Rubric:
    deal = await _get_or_create_company_screening_deal(session, company_id)
    return await update_rubric(session, deal_id=deal.id, values=values)


async def _get_or_create_company_screening_deal(
    session: AsyncSession, company_id: uuid.UUID
) -> Deal:
    company = await deal_repo.get_company(session, company_id)
    if company is None:
        raise NotFoundError("Company not found")
    deal = await deal_repo.get_latest_deal_for_company(session, company_id)
    if deal is not None:
        await initialize_diligence(session, deal.id)
        return deal

    deal = await deal_repo.create_deal(
        session,
        company_id=company_id,
        name="Screening rubric",
        investment_status=InvestmentStatus.INITIAL_REVIEW,
    )
    await status_repo.seed_default_deal_statuses(session)
    initial_status = await status_repo.get_deal_status_by_name(session, "Initial Review")
    if initial_status is not None:
        deal.deal_status_id = initial_status.id
    await initialize_diligence(session, deal.id)
    await session.commit()
    await session.refresh(deal)
    return deal


async def list_checklist_items(
    session: AsyncSession,
    deal_id: uuid.UUID,
) -> list[DiligenceChecklistItem]:
    deal = await deal_repo.get_deal(session, deal_id)
    if deal is None:
        raise NotFoundError("Deal not found")
    await initialize_diligence(session, deal_id)
    return await deal_repo.list_diligence_items(session, deal_id)


async def update_checklist_item(
    session: AsyncSession,
    *,
    deal_id: uuid.UUID,
    item_id: uuid.UUID,
    values: dict[str, Any],
    actor_id: uuid.UUID | None,
) -> DiligenceChecklistItem:
    item = await deal_repo.get_diligence_item(session, deal_id=deal_id, item_id=item_id)
    if item is None:
        raise NotFoundError("Diligence checklist item not found")

    previous_status = item.status
    for field in ("label", "sort_order", "evidence_notes"):
        if field in values:
            setattr(item, field, values[field])
    if "status" in values and values["status"] is not None:
        item.status = values["status"]

    if (
        item.status == DiligenceItemStatus.COMPLETE
        and previous_status != DiligenceItemStatus.COMPLETE
    ):
        item.completed_by = actor_id
        item.completed_at = datetime.now(UTC)
    elif item.status != DiligenceItemStatus.COMPLETE:
        item.completed_by = None
        item.completed_at = None

    await session.commit()
    await session.refresh(item)
    return item
