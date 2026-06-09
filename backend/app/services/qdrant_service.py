from __future__ import annotations

from functools import lru_cache

from qdrant_client import QdrantClient
from qdrant_client.http import models as qdrant_models

from app.config import get_settings
from app.services.embeddings import get_embedding_dimension
from app.services.runtime_metrics import metrics, timed_metric


@lru_cache
def get_client() -> QdrantClient:
    settings = get_settings()
    if settings.qdrant_mode == "server":
        return QdrantClient(
            url=settings.qdrant_url,
            api_key=settings.qdrant_api_key,
            prefer_grpc=settings.qdrant_prefer_grpc,
            timeout=settings.retrieval_timeout_seconds,
        )
    return QdrantClient(path=str(settings.qdrant_dir))


def ensure_collection(collection_name: str) -> None:
    client = get_client()
    vector_size = get_embedding_dimension()
    if client.collection_exists(collection_name):
        return
    client.create_collection(
        collection_name=collection_name,
        vectors_config=qdrant_models.VectorParams(
            size=vector_size,
            distance=qdrant_models.Distance.COSINE,
        ),
    )


def reset_collection(collection_name: str) -> None:
    client = get_client()
    try:
        client.delete_collection(collection_name=collection_name)
    except Exception:
        pass
    ensure_collection(collection_name)


def delete_collection(collection_name: str) -> None:
    client = get_client()
    try:
        client.delete_collection(collection_name=collection_name)
    except Exception:
        pass


def search_collection(
    collection_name: str,
    query_vector: list[float],
    limit: int,
) -> list[qdrant_models.ScoredPoint]:
    client = get_client()
    ensure_collection(collection_name)
    with timed_metric(metrics.record_qdrant_time):
        response = client.query_points(
            collection_name=collection_name,
            query=query_vector,
            limit=limit,
            with_payload=True,
        )
    return response.points
