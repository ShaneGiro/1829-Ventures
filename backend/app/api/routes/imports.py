"""Dealroom import routes."""

from __future__ import annotations

import uuid

from fastapi import APIRouter, File, UploadFile

from app.core.dependencies import CurrentUser, DbSession
from app.core.exceptions import NotFoundError, ValidationError
from app.schemas.import_batch import ImportBatchRead, ImportCommitRequest
from app.schemas.import_row import ImportRowRead
from app.services import dealroom_import_service

router = APIRouter()


@router.post("/dealroom", response_model=ImportBatchRead)
async def upload_dealroom_csv(
    db: DbSession,
    current_user: CurrentUser,
    file: UploadFile = File(...),
) -> ImportBatchRead:
    if not file.filename or not file.filename.lower().endswith(".csv"):
        raise ValidationError("A Dealroom CSV file is required")
    content = await file.read()
    preview = await dealroom_import_service.preview_upload(
        db,
        content=content,
        filename=file.filename,
        uploaded_by=current_user.id,
    )
    return ImportBatchRead.model_validate(preview.batch)


@router.get("/{batch_id}", response_model=ImportBatchRead)
async def get_import_batch(
    db: DbSession, _current_user: CurrentUser, batch_id: uuid.UUID
) -> ImportBatchRead:
    preview = await dealroom_import_service.get_import_batch(db, batch_id)
    if preview is None:
        raise NotFoundError("Import batch not found")
    return ImportBatchRead.model_validate(preview.batch)


@router.get("/{batch_id}/rows", response_model=list[ImportRowRead])
async def list_import_rows(
    db: DbSession, _current_user: CurrentUser, batch_id: uuid.UUID
) -> list[ImportRowRead]:
    preview = await dealroom_import_service.get_import_batch(db, batch_id)
    if preview is None:
        raise NotFoundError("Import batch not found")
    return [ImportRowRead.model_validate(row) for row in preview.rows]


@router.post("/{batch_id}/commit", response_model=ImportBatchRead)
async def commit_import_batch(
    db: DbSession,
    _current_user: CurrentUser,
    batch_id: uuid.UUID,
    request: ImportCommitRequest,
) -> ImportBatchRead:
    preview = await dealroom_import_service.commit_import(db, batch_id=batch_id, request=request)
    if preview is None:
        raise NotFoundError("Import batch not found")
    return ImportBatchRead.model_validate(preview.batch)
