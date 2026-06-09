from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.config import Settings
from app.deps import get_app_settings, get_db
from app.models import Setting
from app.schemas import SettingsResponse, SettingsUpdateRequest
from app.utils.errors import bad_request

router = APIRouter(prefix="/settings", tags=["settings"])


@router.get("", response_model=SettingsResponse)
def get_settings_endpoint(
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_app_settings),
) -> SettingsResponse:
    setting = db.get(Setting, 1)
    if not setting:
        setting = Setting(
            default_top_k=settings.default_top_k,
            chunk_size=settings.chunk_size,
            chunk_overlap=settings.chunk_overlap,
            vector_candidate_limit=settings.vector_candidate_limit,
            retrieval_concurrency_limit=settings.retrieval_concurrency_limit,
            indexing_worker_concurrency=settings.indexing_worker_concurrency,
            hybrid_retrieval_enabled=1 if settings.hybrid_retrieval_enabled else 0,
            reranker_enabled=1 if settings.reranker_enabled else 0,
        )
        db.add(setting)
        db.commit()
        db.refresh(setting)
    return SettingsResponse(
        default_top_k=setting.default_top_k,
        max_top_k=settings.max_top_k,
        chunk_size=setting.chunk_size,
        chunk_overlap=setting.chunk_overlap,
        vector_candidate_limit=setting.vector_candidate_limit,
        retrieval_concurrency_limit=setting.retrieval_concurrency_limit,
        indexing_worker_concurrency=setting.indexing_worker_concurrency,
        hybrid_retrieval_enabled=bool(setting.hybrid_retrieval_enabled),
        reranker_enabled=bool(setting.reranker_enabled),
    )


@router.patch("", response_model=SettingsResponse)
def update_settings(
    payload: SettingsUpdateRequest,
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_app_settings),
) -> SettingsResponse:
    if payload.default_top_k > settings.max_top_k:
        raise bad_request(f"default_top_k must be between 1 and {settings.max_top_k}.")
    if payload.chunk_overlap >= payload.chunk_size:
        raise bad_request("chunk_overlap must be smaller than chunk_size.")
    if payload.vector_candidate_limit < payload.default_top_k:
        raise bad_request("vector_candidate_limit must be greater than or equal to default_top_k.")
    setting = db.get(Setting, 1)
    if not setting:
        setting = Setting(
            default_top_k=payload.default_top_k,
            chunk_size=payload.chunk_size,
            chunk_overlap=payload.chunk_overlap,
            vector_candidate_limit=payload.vector_candidate_limit,
            retrieval_concurrency_limit=payload.retrieval_concurrency_limit,
            indexing_worker_concurrency=payload.indexing_worker_concurrency,
            hybrid_retrieval_enabled=1 if payload.hybrid_retrieval_enabled else 0,
            reranker_enabled=1 if payload.reranker_enabled else 0,
        )
    else:
        setting.default_top_k = payload.default_top_k
        setting.chunk_size = payload.chunk_size
        setting.chunk_overlap = payload.chunk_overlap
        setting.vector_candidate_limit = payload.vector_candidate_limit
        setting.retrieval_concurrency_limit = payload.retrieval_concurrency_limit
        setting.indexing_worker_concurrency = payload.indexing_worker_concurrency
        setting.hybrid_retrieval_enabled = 1 if payload.hybrid_retrieval_enabled else 0
        setting.reranker_enabled = 1 if payload.reranker_enabled else 0
    db.add(setting)
    db.commit()
    db.refresh(setting)
    return SettingsResponse(
        default_top_k=setting.default_top_k,
        max_top_k=settings.max_top_k,
        chunk_size=setting.chunk_size,
        chunk_overlap=setting.chunk_overlap,
        vector_candidate_limit=setting.vector_candidate_limit,
        retrieval_concurrency_limit=setting.retrieval_concurrency_limit,
        indexing_worker_concurrency=setting.indexing_worker_concurrency,
        hybrid_retrieval_enabled=bool(setting.hybrid_retrieval_enabled),
        reranker_enabled=bool(setting.reranker_enabled),
    )
