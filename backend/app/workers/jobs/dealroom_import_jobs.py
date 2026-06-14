"""Celery jobs for Dealroom imports."""

from __future__ import annotations

import asyncio
import uuid

from app.core.database import AsyncSessionLocal
from app.schemas.import_batch import ImportCommitRequest
from app.services import dealroom_import_service
from app.workers.celery_app import celery_app


@celery_app.task(name="imports.dealroom.preview")
def preview_dealroom_import(content: bytes, filename: str | None, uploaded_by: str | None) -> str:
    """Parse and preview a Dealroom import in the background."""

    async def _run() -> str:
        async with AsyncSessionLocal() as session:
            preview = await dealroom_import_service.preview_upload(
                session,
                content=content,
                filename=filename,
                uploaded_by=uuid.UUID(uploaded_by) if uploaded_by else None,
            )
            return str(preview.batch.id)

    return asyncio.run(_run())


@celery_app.task(name="imports.dealroom.commit")
def commit_dealroom_import(
    batch_id: str,
    *,
    commit_clean: bool = True,
    skip_conflicts: bool = True,
) -> str:
    """Commit clean Dealroom import rows in the background."""

    async def _run() -> str:
        async with AsyncSessionLocal() as session:
            preview = await dealroom_import_service.commit_import(
                session,
                batch_id=uuid.UUID(batch_id),
                request=ImportCommitRequest(
                    commit_clean=commit_clean,
                    skip_conflicts=skip_conflicts,
                ),
            )
            if preview is None:
                raise ValueError("Import batch not found")
            return str(preview.batch.id)

    return asyncio.run(_run())
