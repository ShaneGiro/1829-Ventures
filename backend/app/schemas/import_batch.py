"""Import batch schemas."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel

from app.core.constants import ImportStatus
from app.schemas.common import TimestampedRead


class ImportBatchRead(TimestampedRead):
    source: str
    filename: str | None = None
    status: ImportStatus
    uploaded_by: uuid.UUID | None = None
    committed_at: datetime | None = None
    summary: dict[str, Any] = {}
    column_mapping: dict[str, Any] = {}
    total_rows: int


class ImportCommitRequest(BaseModel):
    """Commit clean rows; unresolved conflict rows can be skipped or preserved."""

    commit_clean: bool = True
    skip_conflicts: bool = True
