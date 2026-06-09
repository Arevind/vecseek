from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.config import Settings
from app.deps import get_app_settings, get_db
from app.schemas import RetrievalRequest, RetrievalResponse
from app.services.retrieval_service import retrieve

router = APIRouter(tags=["retrieval"])


@router.post("/retrieve", response_model=RetrievalResponse)
def retrieve_endpoint(
    payload: RetrievalRequest,
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_app_settings),
) -> RetrievalResponse:
    return retrieve(
        db,
        payload.folder_name,
        payload.query,
        payload.top_k,
        settings.max_top_k,
        settings.retrieval_timeout_seconds,
    )
