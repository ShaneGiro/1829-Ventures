"""Import repository helpers."""

from __future__ import annotations

import uuid
from collections.abc import Iterable
from datetime import UTC, datetime
from decimal import Decimal
from typing import Any, cast

from geoalchemy2.elements import WKTElement
from sqlalchemy import delete, func, or_, select
from sqlalchemy.engine import CursorResult
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.constants import ImportRowStatus, ImportStatus, RelationshipStatus
from app.integrations.dealroom_csv import DealroomFounder, DealroomParsedRow
from app.models.company import Company
from app.models.company_contact import CompanyContact
from app.models.import_batch import ImportBatch
from app.models.import_row import ImportRow
from app.models.person import Person


async def create_batch(
    session: AsyncSession,
    *,
    filename: str | None,
    uploaded_by: uuid.UUID | None,
    column_mapping: dict[str, Any],
    total_rows: int,
) -> ImportBatch:
    batch = ImportBatch(
        source="dealroom",
        filename=filename,
        uploaded_by=uploaded_by,
        status=ImportStatus.PREVIEWING,
        column_mapping=column_mapping,
        total_rows=total_rows,
    )
    session.add(batch)
    await session.flush()
    return batch


async def get_batch(session: AsyncSession, batch_id: uuid.UUID) -> ImportBatch | None:
    return cast("ImportBatch | None", await session.get(ImportBatch, batch_id))


# Statuses with no committed companies — safe to discard. COMMITTED and
# PARTIALLY_COMMITTED are kept because they created/enriched real records.
UNCOMMITTED_STATUSES: tuple[ImportStatus, ...] = (
    ImportStatus.PREVIEWING,
    ImportStatus.UPLOADED,
    ImportStatus.FAILED,
)


async def delete_uncommitted_batches(session: AsyncSession) -> int:
    """Hard-delete staged batches that were never committed (rows cascade)."""
    result = cast(
        "CursorResult[Any]",
        await session.execute(
            delete(ImportBatch).where(ImportBatch.status.in_(UNCOMMITTED_STATUSES))
        ),
    )
    return result.rowcount or 0


async def list_rows(session: AsyncSession, batch_id: uuid.UUID) -> list[ImportRow]:
    stmt = select(ImportRow).where(ImportRow.batch_id == batch_id).order_by(ImportRow.row_number)
    return list(await session.scalars(stmt))


async def create_row(
    session: AsyncSession,
    *,
    batch_id: uuid.UUID,
    parsed: DealroomParsedRow,
    status: ImportRowStatus,
    field_provenance: dict[str, Any],
    conflicts: dict[str, Any] | None = None,
    skip_reason: str | None = None,
    matched_company_id: uuid.UUID | None = None,
) -> ImportRow:
    row = ImportRow(
        batch_id=batch_id,
        row_number=parsed.row_number,
        status=status,
        raw_data={
            "dealroom": parsed.raw,
            "normalized": parsed_to_payload(parsed),
        },
        field_provenance=field_provenance,
        conflicts=conflicts or {},
        skip_reason=skip_reason,
        matched_company_id=matched_company_id,
    )
    session.add(row)
    await session.flush()
    return row


async def find_company_matches(session: AsyncSession, parsed: DealroomParsedRow) -> list[Company]:
    clauses = []
    if parsed.dealroom_id:
        clauses.append(Company.dealroom_id == parsed.dealroom_id)
    if parsed.domain:
        clauses.append(func.lower(Company.domain) == parsed.domain.lower())
    if parsed.name:
        clauses.append(func.lower(Company.name) == parsed.name.lower())
    if not clauses:
        return []
    stmt = select(Company).where(or_(*clauses), Company.archived_at.is_(None)).limit(10)
    return list(await session.scalars(stmt))


async def create_company_from_row(
    session: AsyncSession,
    *,
    parsed: DealroomParsedRow,
    provenance: dict[str, Any],
) -> Company:
    company = Company(
        name=parsed.name or "Unnamed Dealroom company",
        website=parsed.website,
        description=parsed.description,
        sector=parsed.sector,
        stage=parsed.stage,
        city=parsed.city,
        state=parsed.state,
        country=parsed.country,
        location=_point(parsed),
        relationship_status=RelationshipStatus.IDENTIFIED,
        dealroom_id=parsed.dealroom_id,
        domain=parsed.domain,
        source_system="dealroom",
        field_provenance=provenance,
        imported_unreviewed=True,
    )
    session.add(company)
    await session.flush()
    await create_founder_contacts(session, company=company, founders=parsed.founders, row=parsed)
    return company


async def enrich_empty_company_fields(
    session: AsyncSession,
    *,
    company: Company,
    parsed: DealroomParsedRow,
    provenance: dict[str, Any],
) -> None:
    updated_provenance = dict(company.field_provenance)
    incoming: dict[str, Any] = {
        "website": parsed.website,
        "description": parsed.description,
        "sector": parsed.sector,
        "stage": parsed.stage,
        "city": parsed.city,
        "state": parsed.state,
        "country": parsed.country,
        "dealroom_id": parsed.dealroom_id,
        "domain": parsed.domain,
    }
    for field_name, value in incoming.items():
        if value is not None and not getattr(company, field_name):
            setattr(company, field_name, value)
            updated_provenance[field_name] = provenance[field_name]
    if company.location is None and parsed.latitude is not None and parsed.longitude is not None:
        company.location = _point(parsed)
        updated_provenance["location"] = provenance["location"]
    company.field_provenance = updated_provenance
    if not company.source_system:
        company.source_system = "dealroom"
    await create_founder_contacts(session, company=company, founders=parsed.founders, row=parsed)


async def create_founder_contacts(
    session: AsyncSession,
    *,
    company: Company,
    founders: Iterable[DealroomFounder],
    row: DealroomParsedRow,
) -> None:
    # Track person ids linked during this call: a company can list the same founder
    # twice (or two founders resolve to the same person), and the DB existence check
    # below can't see contacts added but not yet flushed. Without this, a duplicate
    # would violate the (company_id, person_id) unique constraint and roll back the
    # whole commit.
    linked_person_ids: set[uuid.UUID] = set()
    for index, founder in enumerate(founders):
        person = await _find_person(session, founder)
        if person is None:
            person = Person(
                full_name=founder.name,
                linkedin_url=founder.linkedin_url,
                title="Founder",
                notes=_founder_notes(founder),
                source_system="dealroom",
                field_provenance={
                    "full_name": _source(row),
                    "linkedin_url": _source(row),
                    "notes": _source(row),
                },
            )
            session.add(person)
            await session.flush()
        if person.id in linked_person_ids:
            continue
        linked = await _company_contact_exists(session, company.id, person.id)
        if not linked:
            session.add(
                CompanyContact(
                    company_id=company.id,
                    person_id=person.id,
                    is_primary=index == 0,
                    role="founder",
                )
            )
            linked_person_ids.add(person.id)


async def mark_batch_summary(
    session: AsyncSession,
    *,
    batch: ImportBatch,
    summary: dict[str, Any],
    status: ImportStatus,
) -> None:
    batch.summary = summary
    batch.status = status
    if status in {ImportStatus.COMMITTED, ImportStatus.PARTIALLY_COMMITTED}:
        batch.committed_at = datetime.now(UTC)
    await session.flush()


def parsed_from_payload(payload: dict[str, Any]) -> DealroomParsedRow:
    from app.integrations.dealroom_csv import DealroomFounder, DealroomFundingRound

    normalized = payload["normalized"]
    return DealroomParsedRow(
        row_number=int(normalized["row_number"]),
        raw=payload["dealroom"],
        dealroom_id=normalized.get("dealroom_id"),
        name=normalized.get("name"),
        dealroom_url=normalized.get("dealroom_url"),
        website=normalized.get("website"),
        domain=normalized.get("domain"),
        tagline=normalized.get("tagline"),
        description=normalized.get("description"),
        stage=normalized.get("stage"),
        sector=normalized.get("sector") or "Other",
        sector_warnings=list(normalized.get("sector_warnings") or []),
        industries=list(normalized.get("industries") or []),
        sub_industries=list(normalized.get("sub_industries") or []),
        tags=list(normalized.get("tags") or []),
        city=normalized.get("city"),
        state=normalized.get("state"),
        country=normalized.get("country"),
        latitude=_decimal_from_payload(normalized.get("latitude")),
        longitude=_decimal_from_payload(normalized.get("longitude")),
        founders=[DealroomFounder(**item) for item in normalized.get("founders", [])],
        funding_rounds=[
            DealroomFundingRound(
                round_type=item.get("round_type"),
                amount=_decimal_from_payload(item.get("amount")),
                currency=item.get("currency"),
                date=item.get("date"),
                investors=list(item.get("investors") or []),
            )
            for item in normalized.get("funding_rounds", [])
        ],
    )


def parsed_to_payload(parsed: DealroomParsedRow) -> dict[str, Any]:
    return {
        "row_number": parsed.row_number,
        "dealroom_id": parsed.dealroom_id,
        "name": parsed.name,
        "dealroom_url": parsed.dealroom_url,
        "website": parsed.website,
        "domain": parsed.domain,
        "tagline": parsed.tagline,
        "description": parsed.description,
        "stage": parsed.stage,
        "sector": parsed.sector,
        "sector_warnings": parsed.sector_warnings,
        "industries": parsed.industries,
        "sub_industries": parsed.sub_industries,
        "tags": parsed.tags,
        "city": parsed.city,
        "state": parsed.state,
        "country": parsed.country,
        "latitude": str(parsed.latitude) if parsed.latitude is not None else None,
        "longitude": str(parsed.longitude) if parsed.longitude is not None else None,
        "founders": [founder.__dict__ for founder in parsed.founders],
        "funding_rounds": [
            {
                **round_.__dict__,
                "amount": str(round_.amount) if round_.amount is not None else None,
            }
            for round_ in parsed.funding_rounds
        ],
    }


async def _find_person(session: AsyncSession, founder: DealroomFounder) -> Person | None:
    clauses = [func.lower(Person.full_name) == founder.name.lower()]
    if founder.linkedin_url:
        clauses.append(Person.linkedin_url == founder.linkedin_url)
    stmt = select(Person).where(or_(*clauses), Person.archived_at.is_(None)).limit(1)
    return cast("Person | None", await session.scalar(stmt))


async def _company_contact_exists(
    session: AsyncSession, company_id: uuid.UUID, person_id: uuid.UUID
) -> bool:
    stmt = select(CompanyContact.id).where(
        CompanyContact.company_id == company_id,
        CompanyContact.person_id == person_id,
    )
    return await session.scalar(stmt) is not None


def _point(parsed: DealroomParsedRow) -> WKTElement | None:
    if parsed.latitude is None or parsed.longitude is None:
        return None
    return WKTElement(f"POINT({parsed.longitude} {parsed.latitude})", srid=4326)


def _source(row: DealroomParsedRow) -> dict[str, Any]:
    return {
        "source": "dealroom",
        "source_row": row.row_number,
        "dealroom_id": row.dealroom_id,
        "confidence": 1.0,
    }


def _founder_notes(founder: DealroomFounder) -> str | None:
    parts = [
        f"Status: {founder.status}" if founder.status else None,
        f"University: {founder.university}" if founder.university else None,
        f"Background: {founder.background}" if founder.background else None,
    ]
    return "\n".join(part for part in parts if part) or None


def _decimal_from_payload(value: Any) -> Decimal | None:
    if value is None:
        return None
    return Decimal(str(value))
