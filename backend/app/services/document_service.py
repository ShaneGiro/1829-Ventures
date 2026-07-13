"""Document metadata and presigned-upload service boundary."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.audit import actor_from_user
from app.core.config import settings
from app.core.constants import (
    ALLOWED_DOCUMENT_EXTENSIONS,
    ALLOWED_DOCUMENT_MIME_TYPES,
    DocumentSource,
    DocumentStatus,
)
from app.core.exceptions import NotFoundError, ValidationError
from app.integrations.minio_storage import get_document_storage
from app.integrations.storage import DocumentStorage, PresignedUpload
from app.models.document import Document
from app.models.user import User
from app.repositories import documents as document_repo
from app.schemas.document import DocumentCreate, DocumentUpdate, PresignedUploadRequest
from app.services import audit_service

_MIME_TYPES_BY_EXTENSION: dict[str, frozenset[str]] = {
    ".csv": frozenset({"text/csv", "text/plain"}),
    ".doc": frozenset({"application/msword"}),
    ".docx": frozenset({"application/vnd.openxmlformats-officedocument.wordprocessingml.document"}),
    ".jpeg": frozenset({"image/jpeg"}),
    ".jpg": frozenset({"image/jpeg"}),
    ".markdown": frozenset({"text/markdown", "text/plain"}),
    ".md": frozenset({"text/markdown", "text/plain"}),
    ".pdf": frozenset({"application/pdf"}),
    ".png": frozenset({"image/png"}),
    ".txt": frozenset({"text/plain"}),
    ".xls": frozenset({"application/vnd.ms-excel"}),
    ".xlsx": frozenset({"application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"}),
}


def _storage_key(document_id: uuid.UUID, filename: str) -> str:
    safe_name = filename.replace("/", "_").replace("\\", "_")
    return f"documents/{document_id}/{safe_name}"


def _validate_upload_request(payload: PresignedUploadRequest) -> None:
    extension = Path(payload.filename).suffix.lower()
    if extension not in ALLOWED_DOCUMENT_EXTENSIONS:
        raise ValidationError(f"Unsupported document extension: {extension or '(none)'}")
    if payload.content_type and payload.content_type not in ALLOWED_DOCUMENT_MIME_TYPES:
        raise ValidationError(f"Unsupported document content type: {payload.content_type}")
    if payload.size_bytes is not None and payload.size_bytes > settings.s3_max_upload_mb * 1024**2:
        raise ValidationError(f"Document exceeds the {settings.s3_max_upload_mb} MB upload limit")


def _sniff_content_type(body: bytes) -> str:
    """Return a MIME type based on bytes, never on the browser declaration."""
    import magic

    return str(magic.from_buffer(body, mime=True)).split(";", 1)[0].strip().lower()


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
    session: AsyncSession,
    payload: PresignedUploadRequest,
    actor: User,
    storage: DocumentStorage | None = None,
) -> tuple[Document, PresignedUpload]:
    _validate_upload_request(payload)
    document = Document(
        filename=payload.filename,
        content_type=payload.content_type,
        size_bytes=payload.size_bytes,
        source=DocumentSource.UPLOAD,
        company_id=payload.company_id,
        deal_id=payload.deal_id,
        person_id=payload.person_id,
        uploaded_by=actor.id,
        status=DocumentStatus.PENDING,
    )
    await document_repo.create_document(session, document)
    document.storage_key = _storage_key(document.id, document.filename)
    storage_client = storage or get_document_storage()
    upload = storage_client.create_presigned_upload(
        storage_key=document.storage_key,
        content_type=document.content_type,
        max_size_bytes=settings.s3_max_upload_mb * 1024**2,
    )
    await audit_service.record_create(session, actor=actor_from_user(actor), entity=document)
    await session.commit()
    await session.refresh(document)
    return document, upload


async def confirm_upload(
    session: AsyncSession,
    document_id: uuid.UUID,
    actor: User,
    storage: DocumentStorage | None = None,
) -> Document:
    document = await get_document(session, document_id)
    if document.status == DocumentStatus.CONFIRMED:
        return document
    if document.status == DocumentStatus.REJECTED:
        raise ValidationError("Rejected document uploads cannot be confirmed")
    if not document.storage_key:
        raise ValidationError("Document has no storage object")

    storage_client = storage or get_document_storage()
    metadata = storage_client.head_object(storage_key=document.storage_key)
    prefix = storage_client.read_object_prefix(storage_key=document.storage_key)
    detected_type = _sniff_content_type(prefix)
    max_size_bytes = settings.s3_max_upload_mb * 1024**2
    rejection_reason: str | None = None
    if metadata.size_bytes <= 0 or metadata.size_bytes > max_size_bytes:
        rejection_reason = "invalid_size"
    elif detected_type not in ALLOWED_DOCUMENT_MIME_TYPES:
        rejection_reason = f"unsupported_content_type:{detected_type}"
    elif detected_type not in _MIME_TYPES_BY_EXTENSION.get(
        Path(document.filename).suffix.lower(), frozenset()
    ):
        rejection_reason = f"extension_content_type_mismatch:{detected_type}"

    if rejection_reason:
        document.status = DocumentStatus.REJECTED
        document.extra_metadata = {
            **(document.extra_metadata or {}),
            "rejection_reason": rejection_reason,
        }
        storage_client.delete_object(storage_key=document.storage_key)
        await audit_service.record_update(
            session,
            actor=actor_from_user(actor),
            entity=document,
            changes={"status": (DocumentStatus.PENDING, DocumentStatus.REJECTED)},
        )
        await session.commit()
        raise ValidationError("Uploaded document failed server-side validation")

    changes: dict[str, tuple[Any, Any]] = {
        "status": (document.status, DocumentStatus.CONFIRMED),
        "size_bytes": (document.size_bytes, metadata.size_bytes),
        "content_type": (document.content_type, detected_type),
    }
    document.status = DocumentStatus.CONFIRMED
    document.size_bytes = metadata.size_bytes
    document.content_type = detected_type
    await audit_service.record_update(
        session, actor=actor_from_user(actor), entity=document, changes=changes
    )
    await session.commit()
    await session.refresh(document)
    return document


async def create_download_url(
    session: AsyncSession,
    document_id: uuid.UUID,
    storage: DocumentStorage | None = None,
) -> str:
    document = await get_document(session, document_id)
    if document.status != DocumentStatus.CONFIRMED or not document.storage_key:
        raise ValidationError("Document is not ready for download")
    return (storage or get_document_storage()).create_presigned_download(
        storage_key=document.storage_key,
        expires_in=300,
    )
