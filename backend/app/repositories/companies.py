"""Company repository helpers: filtering, exact/full-text/semantic search."""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, cast

from sqlalchemy import (
    ColumnElement,
    Date,
    Numeric,
    Select,
    case,
    exists,
    func,
    literal_column,
    or_,
    select,
)
from sqlalchemy import cast as sql_cast
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.company import Company
from app.models.company_contact import CompanyContact
from app.models.import_row import ImportRow
from app.models.tag import company_tags


@dataclass(frozen=True)
class DealroomColumnFilter:
    """Filter over a raw Dealroom CSV column stored on import rows."""

    column: str
    operator: str
    value: str | None = None
    value_to: str | None = None


@dataclass(frozen=True)
class CompanyFilters:
    """Structured filters over company datapoints. Empty/None means 'no constraint'."""

    include_archived: bool = False
    sectors: tuple[str, ...] = ()
    relationship_statuses: tuple[str, ...] = ()
    stages: tuple[str, ...] = ()
    countries: tuple[str, ...] = ()
    states: tuple[str, ...] = ()
    cities: tuple[str, ...] = ()
    source_systems: tuple[str, ...] = ()
    has_rit_nexus: bool | None = None
    imported_unreviewed: bool | None = None
    has_website: bool | None = None
    min_completeness: float | None = None
    max_completeness: float | None = None
    created_after: datetime | None = None
    created_before: datetime | None = None
    updated_after: datetime | None = None
    updated_before: datetime | None = None
    dealroom_column_filters: tuple[DealroomColumnFilter, ...] = ()
    # Extra ad-hoc conditions (e.g. a text predicate) appended by callers.
    extra: tuple[ColumnElement[bool], ...] = field(default_factory=tuple)


EMPTY_FILTERS = CompanyFilters()


def company_filter_conditions(filters: CompanyFilters) -> list[ColumnElement[bool]]:
    """Translate a ``CompanyFilters`` into SQLAlchemy WHERE conditions."""
    conditions: list[ColumnElement[bool]] = []
    if not filters.include_archived:
        conditions.append(Company.archived_at.is_(None))
    if filters.sectors:
        conditions.append(Company.sector.in_(filters.sectors))
    if filters.relationship_statuses:
        conditions.append(Company.relationship_status.in_(filters.relationship_statuses))
    if filters.stages:
        conditions.append(func.lower(Company.stage).in_([s.lower() for s in filters.stages]))
    if filters.countries:
        conditions.append(func.lower(Company.country).in_([c.lower() for c in filters.countries]))
    if filters.states:
        conditions.append(func.lower(Company.state).in_([s.lower() for s in filters.states]))
    if filters.cities:
        conditions.append(func.lower(Company.city).in_([c.lower() for c in filters.cities]))
    if filters.source_systems:
        conditions.append(Company.source_system.in_(filters.source_systems))
    if filters.has_rit_nexus is not None:
        conditions.append(Company.has_rit_nexus.is_(filters.has_rit_nexus))
    if filters.imported_unreviewed is not None:
        conditions.append(Company.imported_unreviewed.is_(filters.imported_unreviewed))
    if filters.has_website is not None:
        conditions.append(
            Company.website.isnot(None) if filters.has_website else Company.website.is_(None)
        )
    if filters.min_completeness is not None:
        conditions.append(Company.completeness_pct >= filters.min_completeness)
    if filters.max_completeness is not None:
        conditions.append(Company.completeness_pct <= filters.max_completeness)
    if filters.created_after is not None:
        conditions.append(Company.created_at >= filters.created_after)
    if filters.created_before is not None:
        conditions.append(Company.created_at <= filters.created_before)
    if filters.updated_after is not None:
        conditions.append(Company.updated_at >= filters.updated_after)
    if filters.updated_before is not None:
        conditions.append(Company.updated_at <= filters.updated_before)
    for dealroom_filter in filters.dealroom_column_filters:
        raw_value = ImportRow.raw_data["dealroom"][dealroom_filter.column].astext
        predicate = _dealroom_column_predicate(raw_value, dealroom_filter)
        if predicate is None:
            continue
        conditions.append(
            exists().where(ImportRow.matched_company_id == Company.id).where(predicate)
        )
    conditions.extend(filters.extra)
    return conditions


def _dealroom_column_predicate(
    raw_value: ColumnElement[str], dealroom_filter: DealroomColumnFilter
) -> ColumnElement[bool] | None:
    operator = dealroom_filter.operator
    value = (dealroom_filter.value or "").strip()
    value_to = (dealroom_filter.value_to or "").strip()

    if operator == "present":
        return raw_value.isnot(None) & (func.length(func.trim(raw_value)) > 0)
    if operator == "blank":
        return raw_value.is_(None) | (func.length(func.trim(raw_value)) == 0)
    if operator == "contains":
        return raw_value.ilike(f"%{value}%") if value else None
    if operator == "equals":
        return func.lower(raw_value) == value.lower() if value else None
    if operator == "yes_no":
        if value not in {"yes", "no"}:
            return None
        return func.lower(raw_value).in_((value, "true" if value == "yes" else "false"))
    if operator in {"number_gte", "number_lte", "number_between"}:
        return _numeric_dealroom_predicate(raw_value, operator, value, value_to)
    if operator in {"date_gte", "date_lte", "date_between"}:
        return _date_dealroom_predicate(raw_value, operator, value, value_to)
    return None


def _numeric_dealroom_predicate(
    raw_value: ColumnElement[str], operator: str, value: str, value_to: str
) -> ColumnElement[bool] | None:
    if not value:
        return None
    cleaned = func.replace(raw_value, ",", "")
    numeric_pattern = r"^\s*-?[0-9,]+(\.[0-9]+)?\s*$"
    valid_number = raw_value.op("~")(numeric_pattern)
    numeric_value = case((valid_number, sql_cast(cleaned, Numeric)), else_=None)
    if operator == "number_gte":
        return valid_number & (numeric_value >= float(value))
    if operator == "number_lte":
        return valid_number & (numeric_value <= float(value))
    if operator == "number_between":
        if not value_to:
            return None
        return valid_number & (numeric_value >= float(value)) & (numeric_value <= float(value_to))
    return None


def _date_dealroom_predicate(
    raw_value: ColumnElement[str], operator: str, value: str, value_to: str
) -> ColumnElement[bool] | None:
    if not value:
        return None
    valid_date = raw_value.op("~")(r"^\d{4}-\d{2}-\d{2}$")
    date_value = case((valid_date, sql_cast(raw_value, Date)), else_=None)
    if operator == "date_gte":
        return valid_date & (date_value >= value)
    if operator == "date_lte":
        return valid_date & (date_value <= value)
    if operator == "date_between":
        if not value_to:
            return None
        return valid_date & (date_value >= value) & (date_value <= value_to)
    return None


def _search_filter(search: str) -> ColumnElement[bool]:
    """Case-insensitive substring match across name, domain, and website."""
    like = f"%{search.strip()}%"
    return or_(
        Company.name.ilike(like),
        Company.domain.ilike(like),
        Company.website.ilike(like),
    )


def _company_tsvector() -> ColumnElement[str]:
    """Weighted full-text vector over name (A), description (B), thesis notes (C).

    The weight labels are emitted as SQL literals: setweight() expects Postgres
    `"char"`, and a bound string parameter would be VARCHAR (no matching overload).
    """

    def weighted(column: Any, label: str) -> ColumnElement[str]:
        return func.setweight(
            func.to_tsvector("english", func.coalesce(column, "")), literal_column(f"'{label}'")
        )

    return (
        weighted(Company.name, "A")
        .op("||")(weighted(Company.description, "B"))
        .op("||")(weighted(Company.thesis_notes, "C"))
    )


async def get_company(
    session: AsyncSession, company_id: uuid.UUID, *, include_archived: bool = False
) -> Company | None:
    stmt = select(Company).where(Company.id == company_id)
    if not include_archived:
        stmt = stmt.where(Company.archived_at.is_(None))
    return cast("Company | None", await session.scalar(stmt))


async def get_latest_dealroom_import_row(
    session: AsyncSession, company_id: uuid.UUID
) -> ImportRow | None:
    stmt = (
        select(ImportRow)
        .where(ImportRow.matched_company_id == company_id)
        .order_by(ImportRow.updated_at.desc(), ImportRow.row_number.desc())
        .limit(1)
    )
    return cast("ImportRow | None", await session.scalar(stmt))


async def list_companies(
    session: AsyncSession, *, limit: int, offset: int, filters: CompanyFilters = EMPTY_FILTERS
) -> list[Company]:
    stmt: Select[tuple[Company]] = (
        select(Company)
        .where(*company_filter_conditions(filters))
        .order_by(Company.name)
        .limit(limit)
        .offset(offset)
    )
    return list(await session.scalars(stmt))


async def count_companies(session: AsyncSession, *, filters: CompanyFilters = EMPTY_FILTERS) -> int:
    stmt = select(func.count()).select_from(Company).where(*company_filter_conditions(filters))
    return int(await session.scalar(stmt) or 0)


async def search_company_ids(
    session: AsyncSession, *, search: str, limit: int, filters: CompanyFilters = EMPTY_FILTERS
) -> list[uuid.UUID]:
    """Exact/substring matches (name, domain, website) honoring filters."""
    stmt = (
        select(Company.id)
        .where(_search_filter(search), *company_filter_conditions(filters))
        .order_by(Company.name)
        .limit(limit)
    )
    return list(await session.scalars(stmt))


async def fulltext_company_ids(
    session: AsyncSession, *, search: str, limit: int, filters: CompanyFilters = EMPTY_FILTERS
) -> list[uuid.UUID]:
    """Full-text matches over name/description/thesis notes, honoring filters."""
    tsv = _company_tsvector()
    tsquery = func.websearch_to_tsquery("english", search)
    stmt = (
        select(Company.id)
        .where(tsv.op("@@")(tsquery), *company_filter_conditions(filters))
        .order_by(func.ts_rank_cd(tsv, tsquery).desc())
        .limit(limit)
    )
    return list(await session.scalars(stmt))


async def semantic_company_ids(
    session: AsyncSession,
    *,
    embedding: list[float],
    limit: int,
    min_score: float = 0.0,
    filters: CompanyFilters = EMPTY_FILTERS,
) -> list[uuid.UUID]:
    """Vector nearest-neighbor company ids (cosine), honoring filters and a
    minimum cosine similarity (`min_score`). similarity = 1 - cosine_distance."""
    distance = Company.embedding.cosine_distance(embedding)
    stmt = (
        select(Company.id)
        .where(
            Company.embedding.isnot(None),
            distance <= (1.0 - min_score),
            *company_filter_conditions(filters),
        )
        .order_by(distance)
        .limit(limit)
    )
    return list(await session.scalars(stmt))


async def get_companies_by_ids(session: AsyncSession, ids: list[uuid.UUID]) -> list[Company]:
    """Fetch companies by id, preserving the order of ``ids``."""
    if not ids:
        return []
    rows = list(await session.scalars(select(Company).where(Company.id.in_(ids))))
    by_id = {company.id: company for company in rows}
    return [by_id[cid] for cid in ids if cid in by_id]


async def create_company(session: AsyncSession, company: Company) -> Company:
    session.add(company)
    await session.flush()
    return company


async def has_primary_contact(session: AsyncSession, company_id: uuid.UUID) -> bool:
    stmt = select(CompanyContact.id).where(
        CompanyContact.company_id == company_id,
        CompanyContact.is_primary.is_(True),
    )
    return await session.scalar(stmt) is not None


async def count_company_tags(session: AsyncSession, company_id: uuid.UUID) -> int:
    stmt = (
        select(func.count())
        .select_from(company_tags)
        .where(company_tags.c.company_id == company_id)
    )
    return int(await session.scalar(stmt) or 0)
