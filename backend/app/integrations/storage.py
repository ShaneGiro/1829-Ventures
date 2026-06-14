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
