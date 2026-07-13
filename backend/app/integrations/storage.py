"""S3-compatible document storage interface."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol


@dataclass(frozen=True)
class PresignedUpload:
    upload_url: str
    storage_key: str
    fields: dict[str, str]


@dataclass(frozen=True)
class ObjectMetadata:
    size_bytes: int
    content_type: str | None


class DocumentStorage(Protocol):
    def create_presigned_upload(
        self,
        *,
        storage_key: str,
        content_type: str | None,
        max_size_bytes: int,
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

    def head_object(self, *, storage_key: str) -> ObjectMetadata:
        """Return persisted object metadata."""

    def read_object_prefix(self, *, storage_key: str, size: int = 8192) -> bytes:
        """Read a bounded prefix for server-side type verification."""

    def create_presigned_download(self, *, storage_key: str, expires_in: int = 300) -> str:
        """Return a short-lived browser/client download URL."""

    def delete_object(self, *, storage_key: str) -> None:
        """Delete a rejected object before it becomes available."""
