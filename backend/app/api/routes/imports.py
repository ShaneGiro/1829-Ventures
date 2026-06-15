"""Dealroom import routes."""

from __future__ import annotations

import uuid
from pathlib import PurePosixPath

from fastapi import APIRouter, File, UploadFile
from fastapi.responses import Response

from app.core.dependencies import CurrentUser, DbSession
from app.core.exceptions import NotFoundError, ValidationError
from app.integrations.dealroom_columns import SUPPORTED_UPLOAD_EXTENSIONS
from app.integrations.dealroom_csv import build_template_csv
from app.schemas.common import PaginatedResponse
from app.schemas.import_batch import ImportBatchRead, ImportCommitRequest
from app.schemas.import_row import ImportRowRead
from app.services import dealroom_import_service

router = APIRouter()

TEMPLATE_FILENAME = "dealroom_import_template.csv"


@router.get("/dealroom/template")
async def download_dealroom_template(_current_user: CurrentUser) -> Response:
    """Download the canonical Dealroom column template (CSV, header row only)."""
    return Response(
        content=build_template_csv(),
        media_type="text/csv",
        headers={"Content-Disposition": f'attachment; filename="{TEMPLATE_FILENAME}"'},
    )


@router.delete("/uncommitted")
async def discard_uncommitted_imports(
    db: DbSession, _current_user: CurrentUser
) -> dict[str, int]:
    """Erase staged import batches that were never committed (called on page load)."""
    deleted = await dealroom_import_service.discard_uncommitted_imports(db)
    return {"deleted": deleted}


@router.post("/dealroom", response_model=ImportBatchRead)
async def upload_dealroom_file(
    db: DbSession,
    current_user: CurrentUser,
    file: UploadFile = File(...),
) -> ImportBatchRead:
    extension = PurePosixPath(file.filename).suffix.lower() if file.filename else ""
    if extension not in SUPPORTED_UPLOAD_EXTENSIONS:
        supported = ", ".join(SUPPORTED_UPLOAD_EXTENSIONS)
        raise ValidationError(f"A Dealroom export file is required ({supported})")
    content = await file.read()
    try:
        preview = await dealroom_import_service.preview_upload(
            db,
            content=content,
            filename=file.filename,
            uploaded_by=current_user.id,
        )
    except ValueError as exc:
        # UnsupportedDealroomFile and the header-detection error both subclass ValueError.
        raise ValidationError(str(exc)) from exc
    return ImportBatchRead.model_validate(preview.batch)


@router.get("/{batch_id}", response_model=ImportBatchRead)
async def get_import_batch(
    db: DbSession, _current_user: CurrentUser, batch_id: uuid.UUID
) -> ImportBatchRead:
    preview = await dealroom_import_service.get_import_batch(db, batch_id)
    if preview is None:
        raise NotFoundError("Import batch not found")
    return ImportBatchRead.model_validate(preview.batch)


@router.get("/{batch_id}/rows", response_model=PaginatedResponse[ImportRowRead])
async def list_import_rows(
    db: DbSession, _current_user: CurrentUser, batch_id: uuid.UUID
) -> PaginatedResponse[ImportRowRead]:
    preview = await dealroom_import_service.get_import_batch(db, batch_id)
    if preview is None:
        raise NotFoundError("Import batch not found")
    items = [ImportRowRead.model_validate(row) for row in preview.rows]
    return PaginatedResponse[ImportRowRead](
        items=items, total=len(items), limit=len(items), offset=0
    )


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
