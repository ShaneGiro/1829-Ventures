"""Document repository helpers."""

from __future__ import annotations

import uuid

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.document import Document
from app.repositories import base


async def get_document(
    session: AsyncSession, document_id: uuid.UUID, *, include_archived: bool = False
) -> Document | None:
    return await base.get_by_id(session, Document, document_id, include_archived=include_archived)


async def list_documents(
    session: AsyncSession,
    *,
    limit: int,
    offset: int,
    company_id: uuid.UUID | None = None,
    person_id: uuid.UUID | None = None,
    deal_id: uuid.UUID | None = None,
    include_archived: bool = False,
) -> list[Document]:
    stmt = select(Document)
    if not include_archived:
        stmt = stmt.where(Document.archived_at.is_(None))
    if company_id is not None:
        stmt = stmt.where(Document.company_id == company_id)
    if person_id is not None:
        stmt = stmt.where(Document.person_id == person_id)
    if deal_id is not None:
        stmt = stmt.where(Document.deal_id == deal_id)
    stmt = stmt.order_by(Document.created_at.desc()).limit(limit).offset(offset)
    return list(await session.scalars(stmt))


async def count_documents(
    session: AsyncSession,
    *,
    company_id: uuid.UUID | None = None,
    person_id: uuid.UUID | None = None,
    deal_id: uuid.UUID | None = None,
    include_archived: bool = False,
) -> int:
    stmt = select(func.count()).select_from(Document)
    if not include_archived:
        stmt = stmt.where(Document.archived_at.is_(None))
    if company_id is not None:
        stmt = stmt.where(Document.company_id == company_id)
    if person_id is not None:
        stmt = stmt.where(Document.person_id == person_id)
    if deal_id is not None:
        stmt = stmt.where(Document.deal_id == deal_id)
    return int(await session.scalar(stmt) or 0)


async def create_document(session: AsyncSession, document: Document) -> Document:
    session.add(document)
    await session.flush()
    return document
