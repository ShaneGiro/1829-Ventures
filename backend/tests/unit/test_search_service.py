"""Search service tests."""

from __future__ import annotations

import uuid
from collections.abc import Sequence
from unittest.mock import AsyncMock

import pytest

from app.core.constants import EMBEDDING_DIM
from app.services import search_service


class FakeProvider:
    def embed_texts(self, texts: Sequence[str]) -> list[list[float]]:
        assert texts == ["photonics seed company"]
        return [[0.1] * EMBEDDING_DIM]


@pytest.mark.asyncio
async def test_retrieve_context_uses_semantic_then_keyword_fallback(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    semantic_result = search_service.SearchResult(
        entity_type="company",
        entity_id=uuid.uuid4(),
        title="Semantic Co",
        snippet=None,
        rank=0.9,
    )
    keyword_result = search_service.SearchResult(
        entity_type="deal",
        entity_id=uuid.uuid4(),
        title="Keyword Deal",
        snippet="memo",
        rank=0.7,
    )
    monkeypatch.setattr(
        search_service,
        "semantic_search",
        AsyncMock(return_value=[semantic_result]),
    )
    monkeypatch.setattr(
        search_service,
        "keyword_search",
        AsyncMock(return_value=[semantic_result, keyword_result]),
    )

    results = await search_service.retrieve_context(
        AsyncMock(),
        "photonics seed company",
        limit=2,
        provider=FakeProvider(),
    )

    assert results == [semantic_result, keyword_result]


def test_embedding_text_helpers_skip_empty_parts() -> None:
    assert search_service.company_embedding_text("Company", None, "Thesis") == "Company\nThesis"
    assert search_service.interaction_embedding_text(None, "Body") == "Body"


def test_pgvector_literal_is_stable() -> None:
    assert search_service._pgvector_literal([0.1, -0.25]) == "[0.10000000,-0.25000000]"
