"""Celery jobs for asynchronous embedding generation."""

from __future__ import annotations

import asyncio
import uuid
from collections.abc import Sequence

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import AsyncSessionLocal
from app.integrations.embeddings import EmbeddingProvider, get_embedding_provider
from app.models.company import Company
from app.models.interaction import Interaction
from app.services.search_service import company_embedding_text, interaction_embedding_text
from app.workers.celery_app import celery_app

EmbeddableRecord = Company | Interaction


async def embed_company_records(
    session: AsyncSession,
    company_ids: Sequence[uuid.UUID],
    *,
    provider: EmbeddingProvider | None = None,
) -> int:
    stmt = select(Company).where(
        Company.id.in_(company_ids),
        Company.archived_at.is_(None),
    )
    companies = list(await session.scalars(stmt))
    texts = [
        company_embedding_text(company.name, company.description, company.thesis_notes)
        for company in companies
    ]
    return await _write_embeddings(session, companies, texts, provider=provider)


async def embed_interaction_records(
    session: AsyncSession,
    interaction_ids: Sequence[uuid.UUID],
    *,
    provider: EmbeddingProvider | None = None,
) -> int:
    stmt = select(Interaction).where(
        Interaction.id.in_(interaction_ids),
        Interaction.archived_at.is_(None),
    )
    interactions = list(await session.scalars(stmt))
    texts = [
        interaction_embedding_text(interaction.summary, interaction.body)
        for interaction in interactions
    ]
    return await _write_embeddings(session, interactions, texts, provider=provider)


async def embed_missing_records(
    session: AsyncSession,
    *,
    limit: int = 100,
    provider: EmbeddingProvider | None = None,
) -> dict[str, int]:
    company_ids = list(
        await session.scalars(
            select(Company.id)
            .where(Company.archived_at.is_(None), Company.embedding.is_(None))
            .order_by(Company.updated_at.desc())
            .limit(limit)
        )
    )
    remaining = max(limit - len(company_ids), 0)
    interaction_ids = list(
        await session.scalars(
            select(Interaction.id)
            .where(Interaction.archived_at.is_(None), Interaction.embedding.is_(None))
            .order_by(Interaction.updated_at.desc())
            .limit(remaining)
        )
    )
    return {
        "companies": await embed_company_records(session, company_ids, provider=provider),
        "interactions": await embed_interaction_records(
            session,
            interaction_ids,
            provider=provider,
        ),
    }


@celery_app.task(name="embeddings.embed_companies")
def embed_companies(company_ids: list[str]) -> int:
    async def _run() -> int:
        async with AsyncSessionLocal() as session:
            return await embed_company_records(
                session,
                [uuid.UUID(company_id) for company_id in company_ids],
                provider=get_embedding_provider(),
            )

    return asyncio.run(_run())


@celery_app.task(name="embeddings.embed_interactions")
def embed_interactions(interaction_ids: list[str]) -> int:
    async def _run() -> int:
        async with AsyncSessionLocal() as session:
            return await embed_interaction_records(
                session,
                [uuid.UUID(interaction_id) for interaction_id in interaction_ids],
                provider=get_embedding_provider(),
            )

    return asyncio.run(_run())


@celery_app.task(name="embeddings.embed_missing")
def embed_missing(limit: int = 100) -> dict[str, int]:
    async def _run() -> dict[str, int]:
        async with AsyncSessionLocal() as session:
            return await embed_missing_records(
                session,
                limit=limit,
                provider=get_embedding_provider(),
            )

    return asyncio.run(_run())


async def _write_embeddings(
    session: AsyncSession,
    records: Sequence[EmbeddableRecord],
    texts: Sequence[str],
    *,
    provider: EmbeddingProvider | None = None,
) -> int:
    text_by_record = [(record, text) for record, text in zip(records, texts, strict=True) if text]
    if not text_by_record:
        return 0
    vectors = (provider or get_embedding_provider()).embed_texts(
        [text for _, text in text_by_record]
    )
    for (record, _text), vector in zip(text_by_record, vectors, strict=True):
        record.embedding = vector
    await session.commit()
    return len(text_by_record)
