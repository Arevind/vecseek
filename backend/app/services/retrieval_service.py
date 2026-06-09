from __future__ import annotations

from math import fabs
from time import perf_counter

from sqlalchemy.orm import Session

from app.config import get_settings
from app.models import Folder, FolderStatus, Setting
from app.schemas import RetrievalResponse, RetrievalResult
from app.services.chunk_store import build_fts_query, search_keyword_chunks
from app.services.concurrency import retrieval_limiter
from app.services.embeddings import embed_texts
from app.services.qdrant_service import search_collection
from app.services.runtime_metrics import metrics
from app.utils.errors import bad_request, not_found
from app.utils.slugs import normalize_name


STOPWORDS = {
    "what", "which", "when", "where", "who", "why", "how", "about", "tell", "into", "from",
    "that", "this", "with", "have", "your", "their", "there", "would", "could", "should",
    "please", "does", "is", "are", "the", "and", "for", "can",
}


def resolve_top_k(db: Session, requested_top_k: int | None, max_top_k: int) -> int:
    if requested_top_k is not None:
        if requested_top_k < 1 or requested_top_k > max_top_k:
            raise bad_request(f"top_k must be between 1 and {max_top_k}.")
        return requested_top_k
    settings_row = db.get(Setting, 1)
    return settings_row.default_top_k if settings_row else min(5, max_top_k)


def _settings_or_defaults(db: Session, max_top_k: int) -> dict[str, int | bool]:
    setting = db.get(Setting, 1)
    if not setting:
        return {
            "vector_candidate_limit": max(max_top_k * 4, 32),
            "retrieval_concurrency_limit": 12,
            "hybrid_retrieval_enabled": True,
            "reranker_enabled": True,
        }
    return {
        "vector_candidate_limit": max(setting.vector_candidate_limit, max_top_k),
        "retrieval_concurrency_limit": max(1, setting.retrieval_concurrency_limit),
        "hybrid_retrieval_enabled": bool(setting.hybrid_retrieval_enabled),
        "reranker_enabled": bool(setting.reranker_enabled),
    }


def _tokenize(text: str) -> set[str]:
    return {
        token
        for token in text.casefold().replace("?", " ").replace(":", " ").replace("/", " ").split()
        if len(token) > 2 and token not in STOPWORDS
    }


def _explanation(payload: dict, dense_score: float, lexical_score: float, query_terms: set[str], content: str) -> str:
    matched_terms = sorted(query_terms & _tokenize(content))
    reasons = []
    if dense_score > 0:
        reasons.append("strong semantic match")
    if lexical_score > 0:
        reasons.append("keyword overlap")
    if payload.get("content_type") == "table":
        reasons.append("table-derived record")
    if matched_terms:
        reasons.append(f"matched terms: {', '.join(matched_terms[:4])}")
    return "; ".join(reasons) if reasons else "Retrieved from vector similarity."


def _merge_candidates(
    dense_points,
    lexical_rows: list[dict],
    query_terms: set[str],
    reranker_enabled: bool,
) -> list[RetrievalResult]:
    merged: dict[str, dict] = {}

    for point in dense_points:
        payload = dict(point.payload or {})
        chunk_id = str(payload.get("chunk_id") or point.id)
        content = str(payload.get("content", ""))
        merged[chunk_id] = {
            "content": content,
            "metadata": payload,
            "dense_score": max(0.0, float(point.score)),
            "lexical_score": 0.0,
        }

    for row in lexical_rows:
        chunk_id = str(row["id"])
        lexical_score = 1.0 / (1.0 + fabs(float(row["bm25_score"])))
        metadata = {
            "chunk_id": chunk_id,
            "source_file": row["source_file"],
            "file_type": row["file_type"],
            "content_type": row["content_type"],
            "page_number": int(row["page_number"]),
            "table_index": int(row["table_index"]),
            "row_index": int(row["row_index"]),
            "chunk_index": int(row["chunk_index"]),
            "file_hash": row["file_hash"],
            "citation": f"{row['source_file']} · page {int(row['page_number'])}",
        }
        item = merged.setdefault(
            chunk_id,
            {
                "content": str(row["content"]),
                "metadata": metadata,
                "dense_score": 0.0,
                "lexical_score": 0.0,
            },
        )
        item["lexical_score"] = max(float(item["lexical_score"]), lexical_score)
        item["metadata"].update(metadata)

    results: list[tuple[float, RetrievalResult]] = []
    for item in merged.values():
        content = str(item["content"])
        metadata = dict(item["metadata"])
        dense_score = float(item["dense_score"])
        lexical_score = float(item["lexical_score"])
        overlap = len(query_terms & _tokenize(content))
        richness_boost = min(len(content) / 1000.0, 0.18)
        rerank_boost = (overlap * 0.03) + richness_boost if reranker_enabled else 0.0
        final_score = (dense_score * 0.62) + (lexical_score * 0.28) + rerank_boost
        metadata["dense_score"] = round(dense_score, 4)
        metadata["keyword_score"] = round(lexical_score, 4)
        metadata["embedding_model"] = get_settings().embedding_model
        metadata["explanation"] = _explanation(metadata, dense_score, lexical_score, query_terms, content)
        results.append((final_score, RetrievalResult(content=content, score=final_score, metadata=metadata)))

    results.sort(key=lambda item: item[0], reverse=True)
    return [item for _, item in results]


def retrieve(db: Session, folder_name: str, query: str, top_k: int, max_top_k: int, timeout_seconds: float) -> RetrievalResponse:
    started = perf_counter()
    effective_top_k = resolve_top_k(db, top_k, max_top_k)
    resolved_settings = _settings_or_defaults(db, max_top_k)
    folder = db.query(Folder).filter(Folder.normalized_name == normalize_name(folder_name)).first()
    if not folder:
        raise not_found("Folder not found.")
    if folder.status != FolderStatus.INDEXED:
        raise bad_request("Folder is not indexed yet.")

    with retrieval_limiter.acquire(
        int(resolved_settings["retrieval_concurrency_limit"]),
        timeout_seconds=timeout_seconds,
    ):
        query_vector = embed_texts([query])[0]
        candidate_limit = min(
            int(resolved_settings["vector_candidate_limit"]),
            max(max_top_k, effective_top_k * 4),
        )
        try:
            dense_points = search_collection(folder.collection_name, query_vector, candidate_limit)
        except Exception as exc:
            raise bad_request("Qdrant collection is missing for this folder.") from exc

        lexical_rows: list[dict] = []
        if bool(resolved_settings["hybrid_retrieval_enabled"]):
            fts_query = build_fts_query(query)
            if fts_query:
                lexical_rows = search_keyword_chunks(db, folder.id, fts_query, candidate_limit)

        query_terms = _tokenize(query)
        merged = _merge_candidates(
            dense_points=dense_points,
            lexical_rows=lexical_rows,
            query_terms=query_terms,
            reranker_enabled=bool(resolved_settings["reranker_enabled"]),
        )
        metrics.record_retrieval_time(perf_counter() - started)
        return RetrievalResponse(
            folder_name=folder.display_name,
            query=query,
            top_k=effective_top_k,
            results=merged[:effective_top_k],
        )
