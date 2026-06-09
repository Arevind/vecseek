from __future__ import annotations

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api import documents, evaluations, folders, health, indexing, retrieval, settings as settings_router
from app.config import get_settings
from app.database import init_db
from app.models import Setting
from app.database import SessionLocal
from app.services.eval_queue import eval_queue
from app.services.index_queue import index_queue


def create_app() -> FastAPI:
    settings = get_settings()
    init_db()
    with SessionLocal() as db:
        if not db.get(Setting, 1):
            db.add(
                Setting(
                    default_top_k=settings.default_top_k,
                    chunk_size=settings.chunk_size,
                    chunk_overlap=settings.chunk_overlap,
                    vector_candidate_limit=settings.vector_candidate_limit,
                    retrieval_concurrency_limit=settings.retrieval_concurrency_limit,
                    indexing_worker_concurrency=settings.indexing_worker_concurrency,
                    hybrid_retrieval_enabled=1 if settings.hybrid_retrieval_enabled else 0,
                    reranker_enabled=1 if settings.reranker_enabled else 0,
                )
            )
            db.commit()
    index_queue.start()
    eval_queue.start()

    app = FastAPI(title=settings.app_name, version="1.0.0")
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.exception_handler(Exception)
    async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:  # noqa: ARG001
        if isinstance(exc, HTTPException):
            return JSONResponse(status_code=exc.status_code, content={"detail": exc.detail})
        return JSONResponse(status_code=500, content={"detail": str(exc)})

    app.include_router(health.router)
    app.include_router(settings_router.router)
    app.include_router(folders.router)
    app.include_router(documents.router)
    app.include_router(indexing.router)
    app.include_router(retrieval.router)
    app.include_router(evaluations.router)
    return app


app = create_app()
