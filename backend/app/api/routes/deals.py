"""Deal, pipeline triage, diligence, and rubric routes."""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Query

from app.core.constants import InvestmentStatus
from app.core.dependencies import CurrentUser, DbSession
from app.core.permissions import PermissionAction, PermissionResource
from app.schemas.common import PaginatedResponse
from app.schemas.deal import (
    DealCreate,
    DealRead,
    DealUpdate,
    ReviewNeededTaskRead,
    TriageRequest,
    TriageResponse,
)
from app.schemas.diligence_checklist_item import DiligenceItemRead, DiligenceItemUpdate
from app.schemas.rubric import RubricRead, RubricUpdate
from app.schemas.task import TaskRead
from app.services import deal_service, diligence_service, pipeline_service
from app.services.permission_service import require_permission

router = APIRouter()


@router.get("", response_model=PaginatedResponse[DealRead])
async def list_deals(
    db: DbSession,
    current_user: CurrentUser,
    company_id: uuid.UUID | None = None,
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
) -> PaginatedResponse[DealRead]:
    require_permission(current_user, PermissionAction.READ, PermissionResource.CRM)
    deals, total = await deal_service.list_deals(
        db,
        limit=limit,
        offset=offset,
        company_id=company_id,
    )
    return PaginatedResponse(
        items=[DealRead.model_validate(deal) for deal in deals],
        total=total,
        limit=limit,
        offset=offset,
    )


@router.post("", response_model=DealRead)
async def create_deal(
    payload: DealCreate,
    db: DbSession,
    current_user: CurrentUser,
) -> DealRead:
    require_permission(current_user, PermissionAction.CREATE, PermissionResource.CRM)
    deal = await deal_service.create_deal(
        db,
        values=payload.model_dump(),
        initialize_diligence=payload.investment_status == InvestmentStatus.INITIAL_REVIEW,
    )
    return DealRead.model_validate(deal)


@router.get("/{deal_id}", response_model=DealRead)
async def get_deal(
    deal_id: uuid.UUID,
    db: DbSession,
    current_user: CurrentUser,
) -> DealRead:
    require_permission(current_user, PermissionAction.READ, PermissionResource.CRM)
    return DealRead.model_validate(await deal_service.get_deal(db, deal_id))


@router.patch("/{deal_id}", response_model=DealRead)
async def update_deal(
    deal_id: uuid.UUID,
    payload: DealUpdate,
    db: DbSession,
    current_user: CurrentUser,
) -> DealRead:
    require_permission(current_user, PermissionAction.UPDATE, PermissionResource.CRM)
    deal = await deal_service.update_deal(
        db,
        deal_id=deal_id,
        values=payload.model_dump(exclude_unset=True),
    )
    return DealRead.model_validate(deal)


@router.post("/{deal_id}/archive", response_model=DealRead)
async def archive_deal(
    deal_id: uuid.UUID,
    db: DbSession,
    current_user: CurrentUser,
) -> DealRead:
    require_permission(current_user, PermissionAction.ARCHIVE, PermissionResource.CRM)
    return DealRead.model_validate(await deal_service.archive_deal(db, deal_id))


@router.post("/companies/{company_id}/review-needed", response_model=ReviewNeededTaskRead)
async def mark_review_needed(
    company_id: uuid.UUID,
    db: DbSession,
    current_user: CurrentUser,
) -> ReviewNeededTaskRead:
    require_permission(current_user, PermissionAction.UPDATE, PermissionResource.CRM)
    task = await pipeline_service.mark_review_needed(
        db,
        company_id=company_id,
        owner_id=current_user.id,
    )
    return ReviewNeededTaskRead(task=TaskRead.model_validate(task))


@router.post("/companies/{company_id}/triage", response_model=TriageResponse)
async def triage_review_needed(
    company_id: uuid.UUID,
    payload: TriageRequest,
    db: DbSession,
    current_user: CurrentUser,
) -> TriageResponse:
    require_permission(current_user, PermissionAction.UPDATE, PermissionResource.CRM)
    result = await pipeline_service.triage_review_needed(
        db,
        company_id=company_id,
        outcome=pipeline_service.TriageOutcome(payload.outcome),
        actor_id=current_user.id,
        reason_tags=payload.reason_tags,
        next_check_date=payload.next_check_date,
        notes=payload.notes,
    )
    return TriageResponse(
        outcome=result.outcome.value,
        deal=DealRead.model_validate(result.deal),
        task=TaskRead.model_validate(result.task) if result.task is not None else None,
    )


@router.get("/{deal_id}/rubric", response_model=RubricRead)
async def get_rubric(
    deal_id: uuid.UUID,
    db: DbSession,
    current_user: CurrentUser,
) -> RubricRead:
    require_permission(current_user, PermissionAction.READ, PermissionResource.CRM)
    return RubricRead.model_validate(await diligence_service.get_rubric(db, deal_id))


@router.patch("/{deal_id}/rubric", response_model=RubricRead)
async def update_rubric(
    deal_id: uuid.UUID,
    payload: RubricUpdate,
    db: DbSession,
    current_user: CurrentUser,
) -> RubricRead:
    require_permission(current_user, PermissionAction.UPDATE, PermissionResource.CRM)
    rubric = await diligence_service.update_rubric(
        db,
        deal_id=deal_id,
        values=payload.model_dump(exclude_unset=True),
    )
    return RubricRead.model_validate(rubric)


@router.get("/{deal_id}/diligence", response_model=list[DiligenceItemRead])
async def list_diligence_items(
    deal_id: uuid.UUID,
    db: DbSession,
    current_user: CurrentUser,
) -> list[DiligenceItemRead]:
    require_permission(current_user, PermissionAction.READ, PermissionResource.CRM)
    items = await diligence_service.list_checklist_items(db, deal_id)
    return [DiligenceItemRead.model_validate(item) for item in items]


@router.patch("/{deal_id}/diligence/{item_id}", response_model=DiligenceItemRead)
async def update_diligence_item(
    deal_id: uuid.UUID,
    item_id: uuid.UUID,
    payload: DiligenceItemUpdate,
    db: DbSession,
    current_user: CurrentUser,
) -> DiligenceItemRead:
    require_permission(current_user, PermissionAction.UPDATE, PermissionResource.CRM)
    item = await diligence_service.update_checklist_item(
        db,
        deal_id=deal_id,
        item_id=item_id,
        values=payload.model_dump(exclude_unset=True),
        actor_id=current_user.id,
    )
    return DiligenceItemRead.model_validate(item)
