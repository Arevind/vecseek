from __future__ import annotations

import shutil
from hashlib import sha1

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session, selectinload

from app.config import Settings
from app.deps import get_app_settings, get_db
from app.models import Document, DocumentStatus, Folder, FolderStatus, IndexJob
from app.schemas import ApiMessage, FolderCreateRequest, FolderDetailResponse, FolderResponse
from app.services.chunk_store import delete_folder_chunks
from app.services.qdrant_service import delete_collection
from app.utils.errors import conflict, not_found
from app.utils.slugs import make_collection_name, normalize_name, slugify

router = APIRouter(prefix="/folders", tags=["folders"])


def _folder_to_response(folder: Folder) -> FolderResponse:
    active_documents = [doc for doc in folder.documents if doc.status != DocumentStatus.DELETED]
    latest_job = max(folder.index_jobs, key=lambda item: item.started_at, default=None)
    return FolderResponse(
        id=folder.id,
        display_name=folder.display_name,
        slug=folder.slug,
        collection_name=folder.collection_name,
        status=folder.status,
        document_count=len(active_documents),
        indexed_chunk_count=latest_job.total_chunks if latest_job and latest_job.status.value == "completed" else 0,
        created_at=folder.created_at,
        updated_at=folder.updated_at,
    )


@router.post("", response_model=FolderResponse)
def create_folder(payload: FolderCreateRequest, db: Session = Depends(get_db)) -> FolderResponse:
    normalized_name = normalize_name(payload.folder_name)
    existing = db.query(Folder).filter(Folder.normalized_name == normalized_name).first()
    if existing:
        raise conflict("A folder with this name already exists.")
    slug = slugify(payload.folder_name)
    if db.query(Folder).filter(Folder.slug == slug).first():
        slug = f"{slug}-{sha1(normalized_name.encode('utf-8')).hexdigest()[:8]}"
    folder = Folder(
        display_name=payload.folder_name.strip(),
        normalized_name=normalized_name,
        slug=slug,
        collection_name=make_collection_name(slug),
        status=FolderStatus.EMPTY,
    )
    db.add(folder)
    db.commit()
    db.refresh(folder)
    folder.documents = []
    folder.index_jobs = []
    return _folder_to_response(folder)


@router.get("", response_model=list[FolderResponse])
def list_folders(db: Session = Depends(get_db)) -> list[FolderResponse]:
    folders = (
        db.query(Folder)
        .options(selectinload(Folder.documents), selectinload(Folder.index_jobs))
        .order_by(Folder.created_at.desc())
        .all()
    )
    return [_folder_to_response(folder) for folder in folders]


@router.get("/{folder_name}", response_model=FolderDetailResponse)
def get_folder(folder_name: str, db: Session = Depends(get_db)) -> FolderDetailResponse:
    folder = (
        db.query(Folder)
        .options(selectinload(Folder.documents), selectinload(Folder.index_jobs))
        .filter(Folder.normalized_name == normalize_name(folder_name))
        .first()
    )
    if not folder:
        raise not_found("Folder not found.")
    active_documents = [doc for doc in folder.documents if doc.status != DocumentStatus.DELETED]
    base = _folder_to_response(folder)
    return FolderDetailResponse(**base.model_dump(), documents=active_documents)


@router.delete("/{folder_name}", response_model=ApiMessage)
def delete_folder(
    folder_name: str,
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_app_settings),
) -> ApiMessage:
    folder = db.query(Folder).filter(Folder.normalized_name == normalize_name(folder_name)).first()
    if not folder:
        raise not_found("Folder not found.")
    delete_collection(folder.collection_name)
    delete_folder_chunks(db, folder.id)
    target_dir = settings.upload_dir / folder.slug
    if target_dir.exists():
        shutil.rmtree(target_dir, ignore_errors=True)
    db.delete(folder)
    db.commit()
    return ApiMessage(message="Folder deleted successfully.")
