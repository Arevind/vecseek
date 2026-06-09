from __future__ import annotations

from fastapi import APIRouter

from app.config import get_settings
from app.schemas import DiagnosticsResponse, HealthResponse
from app.services.runtime_metrics import metrics

router = APIRouter(tags=["health"])


@router.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    settings = get_settings()
    return HealthResponse(status="ok", service=settings.app_name)


@router.get("/health/diagnostics", response_model=DiagnosticsResponse)
def diagnostics() -> DiagnosticsResponse:
    settings = get_settings()
    return DiagnosticsResponse(
        status="ok",
        service=settings.app_name,
        qdrant_mode=settings.qdrant_mode,
        embedding_model=settings.embedding_model,
        runtime_metrics=metrics.snapshot(),
    )
