"""Email ingestion routes."""

from __future__ import annotations

from fastapi import APIRouter, Query

from app.core.dependencies import CurrentUser, DbSession
from app.repositories import interactions as interaction_repo
from app.schemas.common import PaginatedResponse
from app.schemas.email import GmailForwardedEmailIngest, GmailIngestResult
from app.schemas.interaction import InteractionRead
from app.services.gmail_ingestion_service import ingest_forwarded_email

router = APIRouter()


@router.post("/gmail", response_model=GmailIngestResult)
async def ingest_gmail_forward(
    payload: GmailForwardedEmailIngest,
    db: DbSession,
    current_user: CurrentUser,
) -> GmailIngestResult:
    return await ingest_forwarded_email(db, payload, actor=current_user)


@router.get("/gmail/review", response_model=PaginatedResponse[InteractionRead])
async def list_gmail_review_queue(
    db: DbSession,
    _current_user: CurrentUser,
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
) -> PaginatedResponse[InteractionRead]:
    interactions = await interaction_repo.list_email_review_queue(db, limit=limit, offset=offset)
    total = await interaction_repo.count_email_review_queue(db)
    return PaginatedResponse(
        items=[InteractionRead.model_validate(interaction) for interaction in interactions],
        total=total,
        limit=limit,
        offset=offset,
    )
