"""Dealroom import preview and commit workflow."""

from __future__ import annotations

import uuid
from collections import Counter
from dataclasses import dataclass
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.constants import ImportRowStatus, ImportStatus
from app.integrations.dealroom_csv import DealroomParsedRow, parse_dealroom_csv
from app.models.company import Company
from app.models.import_batch import ImportBatch
from app.models.import_row import ImportRow
from app.repositories import imports as import_repo
from app.schemas.import_batch import ImportCommitRequest

CONFLICT_FIELDS = ("website", "description", "sector", "stage", "city", "state", "country")


@dataclass(frozen=True)
class DealroomPreview:
    batch: ImportBatch
    rows: list[ImportRow]


async def preview_upload(
    session: AsyncSession,
    *,
    content: bytes,
    filename: str | None,
    uploaded_by: uuid.UUID | None,
) -> DealroomPreview:
    parsed = parse_dealroom_csv(content)
    batch = await import_repo.create_batch(
        session,
        filename=filename,
        uploaded_by=uploaded_by,
        column_mapping={
            "header_row_number": parsed.header_row_number,
            "metadata_row_count": len(parsed.metadata_rows),
            "headers": parsed.headers,
        },
        total_rows=len(parsed.rows),
    )

    rows: list[ImportRow] = []
    for row in parsed.rows:
        status, conflicts, skip_reason, matched_company_id = await _classify_row(session, row)
        rows.append(
            await import_repo.create_row(
                session,
                batch_id=batch.id,
                parsed=row,
                status=status,
                field_provenance=field_provenance(row),
                conflicts=conflicts,
                skip_reason=skip_reason,
                matched_company_id=matched_company_id,
            )
        )

    summary = summarize_rows(rows)
    await import_repo.mark_batch_summary(
        session,
        batch=batch,
        summary=summary,
        status=ImportStatus.UPLOADED,
    )
    await session.commit()
    return DealroomPreview(batch=batch, rows=rows)


async def get_import_batch(session: AsyncSession, batch_id: uuid.UUID) -> DealroomPreview | None:
    batch = await import_repo.get_batch(session, batch_id)
    if batch is None:
        return None
    rows = await import_repo.list_rows(session, batch_id)
    return DealroomPreview(batch=batch, rows=rows)


async def commit_import(
    session: AsyncSession,
    *,
    batch_id: uuid.UUID,
    request: ImportCommitRequest,
) -> DealroomPreview | None:
    batch = await import_repo.get_batch(session, batch_id)
    if batch is None:
        return None
    rows = await import_repo.list_rows(session, batch_id)

    for row in rows:
        if row.status == ImportRowStatus.CREATED and request.commit_clean:
            parsed = import_repo.parsed_from_payload(row.raw_data)
            company = await import_repo.create_company_from_row(
                session,
                parsed=parsed,
                provenance=row.field_provenance,
            )
            row.matched_company_id = company.id
            row.status = ImportRowStatus.COMMITTED
        elif row.status == ImportRowStatus.MATCHED and request.commit_clean:
            if row.matched_company_id is None:
                row.status = ImportRowStatus.SKIPPED
                row.skip_reason = "Matched row had no company ID"
                continue
            matched_company = await session.get(Company, row.matched_company_id)
            if matched_company is None:
                row.status = ImportRowStatus.SKIPPED
                row.skip_reason = "Matched company no longer exists"
                continue
            parsed = import_repo.parsed_from_payload(row.raw_data)
            await import_repo.enrich_empty_company_fields(
                session,
                company=matched_company,
                parsed=parsed,
                provenance=row.field_provenance,
            )
            row.status = ImportRowStatus.COMMITTED
        elif row.status == ImportRowStatus.CONFLICT and request.skip_conflicts:
            row.status = ImportRowStatus.SKIPPED
            row.skip_reason = "Unresolved conflict skipped during partial commit"

    updated_rows = await import_repo.list_rows(session, batch_id)
    summary = summarize_rows(updated_rows)
    unresolved = summary.get(ImportRowStatus.CONFLICT.value, 0) + summary.get(
        ImportRowStatus.SKIPPED.value, 0
    )
    status = ImportStatus.PARTIALLY_COMMITTED if unresolved else ImportStatus.COMMITTED
    await import_repo.mark_batch_summary(session, batch=batch, summary=summary, status=status)
    await session.commit()
    return DealroomPreview(batch=batch, rows=updated_rows)


def field_provenance(row: DealroomParsedRow) -> dict[str, Any]:
    source = {
        "source": "dealroom",
        "source_row": row.row_number,
        "dealroom_id": row.dealroom_id,
        "confidence": 1.0,
    }
    return {
        "name": source,
        "website": source,
        "description": source,
        "sector": {
            **source,
            "warnings": row.sector_warnings,
            "industries": row.industries,
            "sub_industries": row.sub_industries,
        },
        "stage": source,
        "city": source,
        "state": source,
        "country": source,
        "location": {
            **source,
            "latitude": str(row.latitude) if row.latitude is not None else None,
            "longitude": str(row.longitude) if row.longitude is not None else None,
        },
        "dealroom_id": source,
        "domain": source,
        "founders": source,
        "funding_rounds": source,
        "raw_payload": source,
    }


def summarize_rows(rows: list[ImportRow]) -> dict[str, Any]:
    counts = Counter(row.status.value for row in rows)
    return {
        "total": len(rows),
        "created": counts[ImportRowStatus.CREATED.value],
        "matched": counts[ImportRowStatus.MATCHED.value],
        "conflict": counts[ImportRowStatus.CONFLICT.value],
        "skipped": counts[ImportRowStatus.SKIPPED.value],
        "committed": counts[ImportRowStatus.COMMITTED.value],
    }


async def _classify_row(
    session: AsyncSession, row: DealroomParsedRow
) -> tuple[ImportRowStatus, dict[str, Any], str | None, uuid.UUID | None]:
    if not row.name:
        return ImportRowStatus.SKIPPED, {}, "Missing company name", None

    matches = await import_repo.find_company_matches(session, row)
    if not matches:
        return ImportRowStatus.CREATED, {}, None, None

    match = matches[0]
    conflicts = company_conflicts(match, row)
    if conflicts:
        return ImportRowStatus.CONFLICT, conflicts, None, match.id
    return ImportRowStatus.MATCHED, {}, None, match.id


def company_conflicts(company: Company, row: DealroomParsedRow) -> dict[str, Any]:
    conflicts: dict[str, Any] = {}
    incoming = {
        "website": row.website,
        "description": row.description,
        "sector": row.sector,
        "stage": row.stage,
        "city": row.city,
        "state": row.state,
        "country": row.country,
    }
    for field_name in CONFLICT_FIELDS:
        current_value = getattr(company, field_name)
        incoming_value = incoming[field_name]
        if not current_value or incoming_value is None:
            continue
        if str(current_value).strip().lower() != str(incoming_value).strip().lower():
            conflicts[field_name] = {
                "existing": current_value,
                "incoming": incoming_value,
                "resolution": "review_required",
            }
    return conflicts
