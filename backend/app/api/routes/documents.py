"""Document metadata routes."""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Query

from app.core.dependencies import CurrentUser, DbSession
from app.core.permissions import PermissionAction, PermissionResource
from app.repositories import documents as document_repo
from app.schemas.common import PaginatedResponse
from app.schemas.document import (
    DocumentCreate,
    DocumentDownloadResponse,
    DocumentRead,
    DocumentUpdate,
    PresignedUploadRequest,
    PresignedUploadResponse,
)
from app.services import document_service
from app.services.permission_service import require_permission

router = APIRouter()


@router.get("", response_model=PaginatedResponse[DocumentRead])
async def list_documents(
    db: DbSession,
    current_user: CurrentUser,
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    company_id: uuid.UUID | None = None,
    person_id: uuid.UUID | None = None,
    deal_id: uuid.UUID | None = None,
    include_archived: bool = False,
) -> PaginatedResponse[DocumentRead]:
    require_permission(current_user, PermissionAction.READ, PermissionResource.CRM)
    documents = await document_repo.list_documents(
        db,
        limit=limit,
        offset=offset,
        company_id=company_id,
        person_id=person_id,
        deal_id=deal_id,
        include_archived=include_archived,
    )
    total = await document_repo.count_documents(
        db,
        company_id=company_id,
        person_id=person_id,
        deal_id=deal_id,
        include_archived=include_archived,
    )
    return PaginatedResponse(
        items=[DocumentRead.model_validate(document) for document in documents],
        total=total,
        limit=limit,
        offset=offset,
    )


@router.post("", response_model=DocumentRead, status_code=201)
async def create_document(
    payload: DocumentCreate, db: DbSession, current_user: CurrentUser
) -> DocumentRead:
    require_permission(current_user, PermissionAction.CREATE, PermissionResource.CRM)
    document = await document_service.create_document(db, payload, current_user)
    return DocumentRead.model_validate(document)


@router.post("/presigned-upload", response_model=PresignedUploadResponse, status_code=201)
async def create_presigned_upload(
    payload: PresignedUploadRequest, db: DbSession, current_user: CurrentUser
) -> PresignedUploadResponse:
    require_permission(current_user, PermissionAction.CREATE, PermissionResource.CRM)
    document, upload = await document_service.create_presigned_upload(db, payload, current_user)
    return PresignedUploadResponse(
        document_id=document.id,
        upload_url=upload.upload_url,
        storage_key=document.storage_key or "",
        fields=upload.fields,
    )


@router.post("/{document_id}/confirm", response_model=DocumentRead)
async def confirm_upload(
    document_id: uuid.UUID, db: DbSession, current_user: CurrentUser
) -> DocumentRead:
    require_permission(current_user, PermissionAction.CREATE, PermissionResource.CRM)
    document = await document_service.confirm_upload(db, document_id, current_user)
    return DocumentRead.model_validate(document)


@router.get("/{document_id}/download", response_model=DocumentDownloadResponse)
async def download_document(
    document_id: uuid.UUID, db: DbSession, current_user: CurrentUser
) -> DocumentDownloadResponse:
    require_permission(current_user, PermissionAction.READ, PermissionResource.CRM)
    download_url = await document_service.create_download_url(db, document_id)
    return DocumentDownloadResponse(download_url=download_url)


@router.get("/{document_id}", response_model=DocumentRead)
async def get_document(
    document_id: uuid.UUID,
    db: DbSession,
    current_user: CurrentUser,
    include_archived: bool = False,
) -> DocumentRead:
    require_permission(current_user, PermissionAction.READ, PermissionResource.CRM)
    document = await document_service.get_document(
        db, document_id, include_archived=include_archived
    )
    return DocumentRead.model_validate(document)


@router.patch("/{document_id}", response_model=DocumentRead)
async def update_document(
    document_id: uuid.UUID,
    payload: DocumentUpdate,
    db: DbSession,
    current_user: CurrentUser,
) -> DocumentRead:
    require_permission(current_user, PermissionAction.UPDATE, PermissionResource.CRM)
    document = await document_service.update_document(db, document_id, payload, current_user)
    return DocumentRead.model_validate(document)


@router.post("/{document_id}/archive", response_model=DocumentRead)
async def archive_document(
    document_id: uuid.UUID, db: DbSession, current_user: CurrentUser
) -> DocumentRead:
    require_permission(current_user, PermissionAction.ARCHIVE, PermissionResource.CRM)
    document = await document_service.archive_document(db, document_id, current_user)
    return DocumentRead.model_validate(document)
