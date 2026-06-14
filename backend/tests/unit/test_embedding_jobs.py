"""Embedding job tests with mocked model providers."""

from __future__ import annotations

import uuid
from collections.abc import Sequence

import pytest

from app.core.constants import EMBEDDING_DIM
from app.models.company import Company
from app.workers.jobs import embedding_jobs


class FakeProvider:
    def embed_texts(self, texts: Sequence[str]) -> list[list[float]]:
        assert texts == ["Vector Co\nThesis"]
        return [[0.2] * EMBEDDING_DIM]


class FakeSession:
    def __init__(self) -> None:
        self.committed = False

    async def commit(self) -> None:
        self.committed = True


@pytest.mark.asyncio
async def test_write_embeddings_uses_mock_provider_without_loading_model() -> None:
    session = FakeSession()
    company = Company(id=uuid.uuid4(), name="Vector Co")

    count = await embedding_jobs._write_embeddings(
        session,  # type: ignore[arg-type]
        [company],
        ["Vector Co\nThesis"],
        provider=FakeProvider(),
    )

    assert count == 1
    assert company.embedding == [0.2] * EMBEDDING_DIM
    assert session.committed is True


@pytest.mark.asyncio
async def test_write_embeddings_skips_empty_text() -> None:
    session = FakeSession()
    company = Company(id=uuid.uuid4(), name="Empty Co")

    count = await embedding_jobs._write_embeddings(
        session,  # type: ignore[arg-type]
        [company],
        [""],
        provider=FakeProvider(),
    )

    assert count == 0
    assert company.embedding is None
    assert session.committed is False
