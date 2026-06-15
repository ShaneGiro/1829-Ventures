"""Keyword and semantic search for CRM context retrieval."""

from __future__ import annotations

import logging
import uuid
from dataclasses import dataclass
from typing import Literal

from sqlalchemy import text
from sqlalchemy.engine import RowMapping
from sqlalchemy.ext.asyncio import AsyncSession

from app.integrations.embeddings import EmbeddingProvider, get_embedding_provider

logger = logging.getLogger(__name__)

SearchEntityType = Literal["company", "interaction", "deal"]


@dataclass(frozen=True)
class SearchResult:
    entity_type: SearchEntityType
    entity_id: uuid.UUID
    title: str
    snippet: str | None
    rank: float


def company_embedding_text(name: str, description: str | None, thesis_notes: str | None) -> str:
    return "\n".join(part for part in (name, description, thesis_notes) if part)


def interaction_embedding_text(summary: str | None, body: str | None) -> str:
    return "\n".join(part for part in (summary, body) if part)


async def keyword_search(
    session: AsyncSession,
    query: str,
    *,
    limit: int = 10,
) -> list[SearchResult]:
    cleaned = query.strip()
    if not cleaned:
        return []
    stmt = text(
        """
        WITH q AS (SELECT websearch_to_tsquery('english', :query) AS query)
        SELECT 'company' AS entity_type,
               c.id AS entity_id,
               c.name AS title,
               c.description AS snippet,
               ts_rank_cd(
                   setweight(to_tsvector('english', coalesce(c.name, '')), 'A') ||
                   setweight(to_tsvector('english', coalesce(c.description, '')), 'B') ||
                   setweight(to_tsvector('english', coalesce(c.thesis_notes, '')), 'C'),
                   q.query
               ) AS rank
        FROM companies c, q
        WHERE c.archived_at IS NULL
          AND (
              setweight(to_tsvector('english', coalesce(c.name, '')), 'A') ||
              setweight(to_tsvector('english', coalesce(c.description, '')), 'B') ||
              setweight(to_tsvector('english', coalesce(c.thesis_notes, '')), 'C')
          ) @@ q.query
        UNION ALL
        SELECT 'interaction' AS entity_type,
               i.id AS entity_id,
               coalesce(i.summary, i.interaction_type) AS title,
               i.body AS snippet,
               ts_rank_cd(
                   setweight(to_tsvector('english', coalesce(i.summary, '')), 'A') ||
                   setweight(to_tsvector('english', coalesce(i.body, '')), 'B'),
                   q.query
               ) AS rank
        FROM interactions i, q
        WHERE i.archived_at IS NULL
          AND (
              setweight(to_tsvector('english', coalesce(i.summary, '')), 'A') ||
              setweight(to_tsvector('english', coalesce(i.body, '')), 'B')
          ) @@ q.query
        UNION ALL
        SELECT 'deal' AS entity_type,
               d.id AS entity_id,
               coalesce(d.name, c.name || ' deal') AS title,
               coalesce(d.thesis_fit_notes, d.decision_notes) AS snippet,
               ts_rank_cd(
                   setweight(to_tsvector('english', coalesce(d.name, '')), 'A') ||
                   setweight(to_tsvector('english', coalesce(c.name, '')), 'A') ||
                   setweight(to_tsvector('english', coalesce(d.thesis_fit_notes, '')), 'B') ||
                   setweight(to_tsvector('english', coalesce(d.decision_notes, '')), 'C'),
                   q.query
               ) AS rank
        FROM deals d
        JOIN companies c ON c.id = d.company_id,
             q
        WHERE d.archived_at IS NULL
          AND c.archived_at IS NULL
          AND (
              setweight(to_tsvector('english', coalesce(d.name, '')), 'A') ||
              setweight(to_tsvector('english', coalesce(c.name, '')), 'A') ||
              setweight(to_tsvector('english', coalesce(d.thesis_fit_notes, '')), 'B') ||
              setweight(to_tsvector('english', coalesce(d.decision_notes, '')), 'C')
          ) @@ q.query
        ORDER BY rank DESC
        LIMIT :limit
        """
    )
    rows = (await session.execute(stmt, {"query": cleaned, "limit": limit})).mappings()
    return [_result_from_row(row) for row in rows]


def embed_query(query: str, *, provider: EmbeddingProvider | None = None) -> list[float] | None:
    """Embed a search query for vector search. Returns None if embeddings are
    unavailable (disabled or model load failure) so callers degrade gracefully."""
    cleaned = query.strip()
    if not cleaned:
        return None
    try:
        return (provider or get_embedding_provider()).embed_texts([cleaned])[0]
    except Exception:  # noqa: BLE001 - embeddings are optional; fall back to keyword search
        logger.warning("Query embedding unavailable; skipping semantic search.")
        return None


async def semantic_search(
    session: AsyncSession,
    query: str,
    *,
    limit: int = 10,
    provider: EmbeddingProvider | None = None,
) -> list[SearchResult]:
    cleaned = query.strip()
    if not cleaned:
        return []
    embedding = (provider or get_embedding_provider()).embed_texts([cleaned])[0]
    return await semantic_search_by_embedding(session, embedding, limit=limit)


async def semantic_search_by_embedding(
    session: AsyncSession,
    embedding: list[float],
    *,
    limit: int = 10,
) -> list[SearchResult]:
    stmt = text(
        """
        SELECT 'company' AS entity_type,
               c.id AS entity_id,
               c.name AS title,
               c.description AS snippet,
               1 - (c.embedding <=> CAST(:embedding AS vector)) AS rank
        FROM companies c
        WHERE c.archived_at IS NULL
          AND c.embedding IS NOT NULL
        UNION ALL
        SELECT 'interaction' AS entity_type,
               i.id AS entity_id,
               coalesce(i.summary, i.interaction_type) AS title,
               i.body AS snippet,
               1 - (i.embedding <=> CAST(:embedding AS vector)) AS rank
        FROM interactions i
        WHERE i.archived_at IS NULL
          AND i.embedding IS NOT NULL
        ORDER BY rank DESC
        LIMIT :limit
        """
    )
    rows = (
        await session.execute(stmt, {"embedding": _pgvector_literal(embedding), "limit": limit})
    ).mappings()
    return [_result_from_row(row) for row in rows]


async def retrieve_context(
    session: AsyncSession,
    query: str,
    *,
    limit: int = 8,
    provider: EmbeddingProvider | None = None,
) -> list[SearchResult]:
    semantic = await semantic_search(session, query, limit=limit, provider=provider)
    if len(semantic) >= limit:
        return semantic
    seen = {(result.entity_type, result.entity_id) for result in semantic}
    keyword = await keyword_search(session, query, limit=limit)
    combined = [*semantic]
    for result in keyword:
        key = (result.entity_type, result.entity_id)
        if key not in seen:
            combined.append(result)
            seen.add(key)
        if len(combined) >= limit:
            break
    return combined


def _pgvector_literal(embedding: list[float]) -> str:
    return "[" + ",".join(f"{value:.8f}" for value in embedding) + "]"


def _result_from_row(row: RowMapping) -> SearchResult:
    mapping = dict(row)
    return SearchResult(
        entity_type=mapping["entity_type"],
        entity_id=mapping["entity_id"],
        title=mapping["title"],
        snippet=mapping["snippet"],
        rank=float(mapping["rank"] or 0),
    )
