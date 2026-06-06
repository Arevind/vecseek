from __future__ import annotations

from threading import Thread

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.deps import get_db
from app.database import SessionLocal
from app.models import Folder, FolderStatus, IndexJob, IndexJobStatus
from app.schemas import IndexResponse, IndexStatusResponse, IndexJobResponse
from app.services.indexing_service import index_folder
from app.services.job_progress import get_job_progress
from app.utils.errors import bad_request, not_found
from app.utils.slugs import normalize_name

router = APIRouter(prefix="/folders/{folder_name}/index", tags=["indexing"])


def _resolve_folder(db: Session, folder_name: str) -> Folder:
    folder = db.query(Folder).filter(Folder.normalized_name == normalize_name(folder_name)).first()
    if not folder:
        raise not_found("Folder not found.")
    return folder


def _run_index_job(folder_id: str) -> None:
    db = SessionLocal()
    try:
        folder = db.query(Folder).filter(Folder.id == folder_id).first()
        if not folder:
            return
        index_folder(db, folder)
    finally:
        db.close()


@router.post("", response_model=IndexResponse)
def index_folder_endpoint(folder_name: str, db: Session = Depends(get_db)) -> IndexResponse:
    folder = _resolve_folder(db, folder_name)
    latest_job = max(folder.index_jobs, key=lambda item: item.started_at, default=None)
    if folder.status == FolderStatus.INDEXING or (
        latest_job and latest_job.status == IndexJobStatus.RUNNING
    ):
        raise bad_request("Indexing is already running for this folder.")

    total_files = len([document for document in folder.documents if document.status.value != "deleted"])
    if total_files == 0:
        raise bad_request("Cannot index a folder with no documents.")

    thread = Thread(target=_run_index_job, args=(folder.id,), daemon=True)
    thread.start()

    db.expire_all()
    refreshed_folder = _resolve_folder(db, folder_name)
    latest_job = max(refreshed_folder.index_jobs, key=lambda item: item.started_at, default=None)
    return IndexResponse(
        message="Folder indexing started",
        folder_name=refreshed_folder.display_name,
        collection_name=refreshed_folder.collection_name,
        total_files=latest_job.total_files if latest_job else total_files,
        total_chunks=latest_job.total_chunks if latest_job else 0,
        status=refreshed_folder.status.value,
        job_id=latest_job.id if latest_job else None,
    )


@router.get("/status", response_model=IndexStatusResponse)
def get_index_status(folder_name: str, db: Session = Depends(get_db)) -> IndexStatusResponse:
    folder = _resolve_folder(db, folder_name)
    latest_job = max(folder.index_jobs, key=lambda item: item.started_at, default=None)
    if latest_job:
        progress = get_job_progress(latest_job.id)
        latest_job_response = IndexJobResponse.model_validate(latest_job)
        if progress:
          latest_job_response.phase = str(progress.get("phase"))
          latest_job_response.progress_percent = int(progress.get("progress_percent", 0))
          latest_job_response.status_message = str(progress.get("message"))
        elif latest_job.status == IndexJobStatus.COMPLETED:
          latest_job_response.phase = "completed"
          latest_job_response.progress_percent = 100
          latest_job_response.status_message = "Indexing complete"
        elif latest_job.status == IndexJobStatus.FAILED:
          latest_job_response.phase = "failed"
          latest_job_response.progress_percent = 100
          latest_job_response.status_message = latest_job.error_message
    else:
        latest_job_response = None
    return IndexStatusResponse(
        folder_name=folder.display_name,
        status=folder.status,
        latest_job=latest_job_response,
    )
