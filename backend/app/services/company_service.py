"""Company service: CRUD, completeness, soft archive, and audit."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.audit import actor_from_user
from app.core.config import settings
from app.core.constants import COMPANY_COMPLETENESS_FIELDS
from app.core.exceptions import NotFoundError, ValidationError
from app.models.company import Company
from app.models.user import User
from app.repositories import companies as company_repo
from app.repositories.companies import EMPTY_FILTERS, CompanyFilters
from app.schemas.company import CompanyCompleteness, CompanyCreate, CompanyUpdate
from app.services import audit_service, search_service


def _enqueue_embedding(company_id: uuid.UUID) -> None:
    """Queue a background embedding refresh so semantic search stays current.

    Imported lazily to avoid a hard dependency on Celery/Redis at import time;
    failures are non-fatal (embeddings are additive to exact search).
    """
    try:
        from app.workers.jobs.embedding_jobs import embed_companies

        embed_companies.delay([str(company_id)])
    except Exception:  # noqa: BLE001 - embedding is best-effort, never blocks the write
        pass


async def list_companies(
    session: AsyncSession,
    *,
    query: str | None,
    filters: CompanyFilters,
    limit: int,
    offset: int,
) -> tuple[list[Company], int]:
    """Company listing with structured filters and optional hybrid text search.

    With no ``query``, returns the filtered list ordered by name (paginated +
    counted). With a ``query``, returns a hybrid ranked result that still honors
    every filter: (1) exact/substring on name/domain/website, (2) full-text on
    name/description/thesis notes, (3) semantic (pgvector) above a threshold.
    """
    if not (query and query.strip()):
        companies = await company_repo.list_companies(
            session, limit=limit, offset=offset, filters=filters
        )
        total = await company_repo.count_companies(session, filters=filters)
        return companies, total

    ordered: list[uuid.UUID] = []
    seen: set[uuid.UUID] = set()

    def _add(ids: list[uuid.UUID]) -> None:
        for company_id in ids:
            if company_id not in seen:
                ordered.append(company_id)
                seen.add(company_id)

    _add(await company_repo.search_company_ids(session, search=query, limit=500, filters=filters))
    _add(await company_repo.fulltext_company_ids(session, search=query, limit=100, filters=filters))
    embedding = search_service.embed_query(query)
    if embedding is not None:
        _add(
            await company_repo.semantic_company_ids(
                session,
                embedding=embedding,
                limit=settings.search_semantic_limit,
                min_score=settings.search_semantic_threshold,
                filters=filters,
            )
        )

    total = len(ordered)
    page_ids = ordered[offset : offset + limit]
    return await company_repo.get_companies_by_ids(session, page_ids), total


async def search_companies(
    session: AsyncSession,
    query: str,
    *,
    limit: int,
    offset: int,
    filters: CompanyFilters = EMPTY_FILTERS,
) -> tuple[list[Company], int]:
    """Backward-compatible hybrid search entry point (delegates to list_companies)."""
    return await list_companies(session, query=query, filters=filters, limit=limit, offset=offset)


async def _calculate_completeness(
    session: AsyncSession,
    company: Company,
) -> tuple[float, list[str]]:
    missing: list[str] = []
    for field in COMPANY_COMPLETENESS_FIELDS:
        match field:
            case "location":
                has_value = bool(company.city or company.state or company.country)
            case "primary_contact":
                has_value = await company_repo.has_primary_contact(session, company.id)
            case "tags":
                has_value = await company_repo.count_company_tags(session, company.id) > 0
            case _:
                has_value = bool(getattr(company, field, None))
        if not has_value:
            missing.append(field)
    completed = len(COMPANY_COMPLETENESS_FIELDS) - len(missing)
    pct = round((completed / len(COMPANY_COMPLETENESS_FIELDS)) * 100, 2)
    return pct, missing


async def refresh_completeness(session: AsyncSession, company: Company) -> CompanyCompleteness:
    pct, missing = await _calculate_completeness(session, company)
    company.completeness_pct = pct
    await session.flush()
    return CompanyCompleteness(
        company_id=str(company.id),
        completeness_pct=pct,
        missing_fields=missing,
    )


async def get_company(
    session: AsyncSession,
    company_id: uuid.UUID,
    *,
    include_archived: bool = False,
) -> Company:
    company = await company_repo.get_company(session, company_id, include_archived=include_archived)
    if company is None:
        raise NotFoundError("Company not found")
    return company


async def create_company(session: AsyncSession, payload: CompanyCreate, actor: User) -> Company:
    data = payload.model_dump(exclude_none=True)
    company = Company(**data)
    await company_repo.create_company(session, company)
    await refresh_completeness(session, company)
    await audit_service.record_create(
        session,
        actor=actor_from_user(actor),
        entity=company,
    )
    await session.commit()
    await session.refresh(company)
    _enqueue_embedding(company.id)
    return company


async def update_company(
    session: AsyncSession,
    company_id: uuid.UUID,
    payload: CompanyUpdate,
    actor: User,
) -> Company:
    company = await get_company(session, company_id)
    updates = payload.model_dump(exclude_unset=True)
    required_fields = {"name", "sector", "relationship_status", "has_rit_nexus"}
    null_required = sorted(field for field in required_fields if updates.get(field) is None)
    if null_required:
        raise ValidationError(f"Required company fields cannot be null: {', '.join(null_required)}")
    changes: dict[str, tuple[Any, Any]] = {}
    for field, value in updates.items():
        old_value = getattr(company, field)
        if old_value != value:
            changes[field] = (old_value, value)
            setattr(company, field, value)
    await refresh_completeness(session, company)
    if changes:
        await audit_service.record_update(
            session,
            actor=actor_from_user(actor),
            entity=company,
            changes=changes,
        )
    await session.commit()
    await session.refresh(company)
    # Re-embed only when the text that feeds the embedding changed.
    if changes.keys() & {"name", "description", "thesis_notes"}:
        _enqueue_embedding(company.id)
    return company


async def archive_company(
    session: AsyncSession,
    company_id: uuid.UUID,
    actor: User,
) -> Company:
    company = await get_company(session, company_id)
    old_snapshot = audit_service.snapshot_model(company)
    company.archived_at = datetime.now(UTC)
    await audit_service.record_archive(
        session,
        actor=actor_from_user(actor),
        entity=company,
        old_snapshot=old_snapshot,
    )
    await session.commit()
    await session.refresh(company)
    return company


async def get_company_completeness(
    session: AsyncSession,
    company_id: uuid.UUID,
) -> CompanyCompleteness:
    company = await get_company(session, company_id)
    completeness = await refresh_completeness(session, company)
    await session.commit()
    return completeness
