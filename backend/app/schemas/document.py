"""Document metadata and presigned-upload schemas."""

from __future__ import annotations

import uuid

from pydantic import BaseModel

from app.core.constants import DocumentSource
from app.schemas.common import SoftDeleteRead


class DocumentBase(BaseModel):
    filename: str
    content_type: str | None = None
    size_bytes: int | None = None
    source: DocumentSource = DocumentSource.UPLOAD
    external_link: str | None = None
    company_id: uuid.UUID | None = None
    deal_id: uuid.UUID | None = None
    person_id: uuid.UUID | None = None


class DocumentCreate(DocumentBase):
    pass


class DocumentRead(SoftDeleteRead, DocumentBase):
    storage_key: str | None = None
    uploaded_by: uuid.UUID | None = None


class PresignedUploadRequest(BaseModel):
    filename: str
    content_type: str | None = None
    company_id: uuid.UUID | None = None
    deal_id: uuid.UUID | None = None


class PresignedUploadResponse(BaseModel):
    document_id: uuid.UUID
    upload_url: str
    storage_key: str
