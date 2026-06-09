from __future__ import annotations

from functools import lru_cache
from typing import Protocol

from sentence_transformers import SentenceTransformer

from app.config import get_settings
from app.services.runtime_metrics import metrics, timed_metric


class EmbeddingBackend(Protocol):
    model_name: str

    def dimension(self) -> int: ...

    def embed(self, texts: list[str]) -> list[list[float]]: ...


class SentenceTransformerBackend:
    def __init__(self, model_name: str) -> None:
        self.model_name = model_name
        self._model = SentenceTransformer(model_name)

    def dimension(self) -> int:
        return int(self._model.get_sentence_embedding_dimension())

    def embed(self, texts: list[str]) -> list[list[float]]:
        with timed_metric(metrics.record_embedding_time):
            embeddings = self._model.encode(texts, normalize_embeddings=True, batch_size=32, show_progress_bar=False)
        return embeddings.tolist()


@lru_cache
def get_embedding_backend() -> EmbeddingBackend:
    settings = get_settings()
    return SentenceTransformerBackend(settings.embedding_model)


def get_embedding_dimension() -> int:
    return get_embedding_backend().dimension()


def get_embedding_model_name() -> str:
    return get_embedding_backend().model_name


def embed_texts(texts: list[str]) -> list[list[float]]:
    return get_embedding_backend().embed(texts)
