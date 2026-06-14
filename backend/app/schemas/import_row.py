"""Import row schemas: preview row, conflict diff, commit/skip status."""

from __future__ import annotations

import uuid
from typing import Any

from app.core.constants import ImportRowStatus
from app.schemas.common import TimestampedRead


class ImportRowRead(TimestampedRead):
    batch_id: uuid.UUID
    row_number: int
    status: ImportRowStatus
    raw_data: dict[str, Any] = {}
    field_provenance: dict[str, Any] = {}
    conflicts: dict[str, Any] = {}
    skip_reason: str | None = None
    matched_company_id: uuid.UUID | None = None
