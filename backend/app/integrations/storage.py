"""S3-compatible document storage interface."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol


@dataclass(frozen=True)
class PresignedUpload:
    upload_url: str
    storage_key: str


class DocumentStorage(Protocol):
    def create_presigned_upload(
        self,
        *,
        storage_key: str,
        content_type: str | None,
        expires_in: int = 3600,
    ) -> PresignedUpload:
        """Return a browser/client-upload URL for a document object."""

    def put_object(
        self,
        *,
        storage_key: str,
        body: bytes,
        content_type: str | None,
    ) -> None:
        """Store an object body directly from a trusted backend worker/request."""
