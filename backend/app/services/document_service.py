"""Document metadata and presigned-upload service boundary."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.audit import actor_from_user
from app.core.constants import DocumentSource
from app.core.exceptions import NotFoundError, ValidationError
from app.models.document import Document
from app.models.user import User
from app.repositories import documents as document_repo
from app.schemas.document import DocumentCreate, DocumentUpdate, PresignedUploadRequest
from app.services import audit_service


def _storage_key(document_id: uuid.UUID, filename: str) -> str:
    safe_name = filename.replace("/", "_").replace("\\", "_")
    return f"documents/{document_id}/{safe_name}"


async def get_document(
    session: AsyncSession, document_id: uuid.UUID, *, include_archived: bool = False
) -> Document:
    document = await document_repo.get_document(
        session, document_id, include_archived=include_archived
    )
    if document is None:
        raise NotFoundError("Document not found")
    return document


async def create_document(session: AsyncSession, payload: DocumentCreate, actor: User) -> Document:
    if payload.source == DocumentSource.EXTERNAL_LINK and not payload.external_link:
        raise ValidationError("external_link is required for external-link documents")
    document = Document(
        **payload.model_dump(exclude_none=True),
        uploaded_by=actor.id,
    )
    await document_repo.create_document(session, document)
    await audit_service.record_create(session, actor=actor_from_user(actor), entity=document)
    await session.commit()
    await session.refresh(document)
    return document


async def update_document(
    session: AsyncSession, document_id: uuid.UUID, payload: DocumentUpdate, actor: User
) -> Document:
    document = await get_document(session, document_id)
    updates = payload.model_dump(exclude_unset=True)
    required_fields = {"filename", "source"}
    null_required = sorted(field for field in required_fields if updates.get(field) is None)
    if null_required:
        raise ValidationError(
            f"Required document fields cannot be null: {', '.join(null_required)}"
        )
    changes: dict[str, tuple[Any, Any]] = {}
    for field, value in updates.items():
        old_value = getattr(document, field)
        if old_value != value:
            changes[field] = (old_value, value)
            setattr(document, field, value)
    if changes:
        await audit_service.record_update(
            session, actor=actor_from_user(actor), entity=document, changes=changes
        )
    await session.commit()
    await session.refresh(document)
    return document


async def archive_document(session: AsyncSession, document_id: uuid.UUID, actor: User) -> Document:
    document = await get_document(session, document_id)
    old_snapshot = audit_service.snapshot_model(document)
    document.archived_at = datetime.now(UTC)
    await audit_service.record_archive(
        session,
        actor=actor_from_user(actor),
        entity=document,
        old_snapshot=old_snapshot,
    )
    await session.commit()
    await session.refresh(document)
    return document


async def create_presigned_upload(
    session: AsyncSession, payload: PresignedUploadRequest, actor: User
) -> tuple[Document, str]:
    document = Document(
        filename=payload.filename,
        content_type=payload.content_type,
        source=DocumentSource.UPLOAD,
        company_id=payload.company_id,
        deal_id=payload.deal_id,
        uploaded_by=actor.id,
    )
    await document_repo.create_document(session, document)
    document.storage_key = _storage_key(document.id, document.filename)
    await audit_service.record_create(session, actor=actor_from_user(actor), entity=document)
    await session.commit()
    await session.refresh(document)
    upload_url = f"s3://local-dev/{document.storage_key}"
    return document, upload_url
