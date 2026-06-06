from __future__ import annotations

from sqlalchemy.orm import Session

from app.models import Folder, FolderStatus, Setting
from app.schemas import RetrievalResponse, RetrievalResult
from app.services.embeddings import embed_texts
from app.services.qdrant_service import search_collection
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


def retrieve(db: Session, folder_name: str, query: str, top_k: int, max_top_k: int) -> RetrievalResponse:
    effective_top_k = resolve_top_k(db, top_k, max_top_k)
    folder = (
        db.query(Folder)
        .filter(Folder.normalized_name == normalize_name(folder_name))
        .first()
    )
    if not folder:
        raise not_found("Folder not found.")
    if folder.status != FolderStatus.INDEXED:
        raise bad_request("Folder is not indexed yet.")

    query_vector = embed_texts([query])[0]
    candidate_count = min(max_top_k, max(effective_top_k * 4, effective_top_k))
    try:
        points = search_collection(folder.collection_name, query_vector, candidate_count)
    except Exception as exc:
        raise bad_request("Qdrant collection is missing for this folder.") from exc

    query_terms = {
        token
        for token in query.casefold().replace("?", " ").replace(":", " ").split()
        if len(token) > 2 and token not in STOPWORDS
    }
    scored_items: list[tuple[float, RetrievalResult]] = []
    for point in points:
        payload = dict(point.payload or {})
        content = str(payload.pop("content", ""))
        base_score = max(0.0, float(point.score))
        content_terms = set(content.casefold().replace("?", " ").replace(":", " ").split())
        overlap = len(query_terms & content_terms)
        richness_boost = min(len(content) / 1000.0, 0.2)
        adjusted_score = base_score + (overlap * 0.04) + richness_boost
        scored_items.append(
            (
                adjusted_score,
                RetrievalResult(content=content, score=adjusted_score, metadata=payload),
            )
        )
    scored_items.sort(key=lambda item: item[0], reverse=True)
    items = [item for _, item in scored_items[:effective_top_k]]
    return RetrievalResponse(folder_name=folder.display_name, query=query, top_k=effective_top_k, results=items)
