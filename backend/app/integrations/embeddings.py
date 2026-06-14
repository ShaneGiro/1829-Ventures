"""Configurable local embedding model wrapper.

The sentence-transformer is loaded lazily so request handlers and tests can import
this module without downloading or initializing the model. Workers call
`embed_texts`; tests can pass a mock provider into the embedding job helpers.
"""

from __future__ import annotations

from collections.abc import Sequence
from functools import lru_cache
from typing import Any, Protocol

from app.core.config import settings
from app.core.constants import EMBEDDING_DIM


class EmbeddingProvider(Protocol):
    def embed_texts(self, texts: Sequence[str]) -> list[list[float]]:
        """Return one embedding vector per input text."""
        ...


class SentenceTransformerEmbeddingProvider:
    def __init__(self, model_name: str | None = None) -> None:
        self.model_name = model_name or settings.embedding_model_name
        self._model: Any | None = None

    @property
    def model(self) -> Any:
        if self._model is None:
            from sentence_transformers import SentenceTransformer

            self._model = SentenceTransformer(self.model_name)
        return self._model

    def embed_texts(self, texts: Sequence[str]) -> list[list[float]]:
        if not settings.embedding_enabled:
            raise RuntimeError("Embeddings are disabled by EMBEDDING_ENABLED=false")
        clean_texts = [text.strip() for text in texts]
        vectors = self.model.encode(
            clean_texts,
            batch_size=settings.embedding_batch_size,
            normalize_embeddings=True,
            show_progress_bar=False,
        )
        return [_coerce_vector(vector) for vector in vectors]


def _coerce_vector(vector: Any) -> list[float]:
    values = vector.tolist() if hasattr(vector, "tolist") else list(vector)
    floats = [float(value) for value in values]
    if len(floats) != EMBEDDING_DIM:
        raise ValueError(f"Expected embedding dimension {EMBEDDING_DIM}, got {len(floats)}")
    return floats


@lru_cache(maxsize=1)
def get_embedding_provider() -> EmbeddingProvider:
    return SentenceTransformerEmbeddingProvider()


def embed_texts(texts: Sequence[str]) -> list[list[float]]:
    return get_embedding_provider().embed_texts(texts)
