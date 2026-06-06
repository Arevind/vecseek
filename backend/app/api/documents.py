from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter, Depends, File, UploadFile
from sqlalchemy.orm import Session

from app.config import Settings
from app.deps import get_app_settings, get_db
from app.models import Document, DocumentStatus, Folder, FolderStatus
from app.schemas import ApiMessage, DocumentResponse, UploadItemResponse, UploadResponse
from app.services.file_storage import delete_file_if_exists, save_upload
from app.services.hashing import sha256_for_bytes
from app.utils.errors import bad_request, not_found
from app.utils.slugs import normalize_name

router = APIRouter(prefix="/folders/{folder_name}", tags=["documents"])

SUPPORTED_EXTENSIONS = {".pdf": "pdf", ".docx": "docx", ".txt": "txt"}


def _resolve_folder(db: Session, folder_name: str) -> Folder:
    folder = db.query(Folder).filter(Folder.normalized_name == normalize_name(folder_name)).first()
    if not folder:
        raise not_found("Folder not found.")
    return folder


@router.post("/upload", response_model=UploadResponse)
async def upload_documents(
    folder_name: str,
    files: list[UploadFile] = File(...),
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_app_settings),
) -> UploadResponse:
    folder = _resolve_folder(db, folder_name)
    if not files:
        raise bad_request("At least one file is required.")

    results: list[UploadItemResponse] = []
    uploaded_any = False
    for upload in files:
        file_name = upload.filename or "unnamed"
        extension = Path(file_name).suffix.lower()
        file_type = SUPPORTED_EXTENSIONS.get(extension)
        if not file_type:
            results.append(
                UploadItemResponse(
                    status="error",
                    message=f"Unsupported file type for {file_name}.",
                    file_name=file_name,
                )
            )
            continue
        content = await upload.read()
        if not content:
            results.append(UploadItemResponse(status="error", message="Uploaded file is empty.", file_name=file_name))
            continue
        file_hash = sha256_for_bytes(content)
        existing = (
            db.query(Document)
            .filter(
                Document.folder_id == folder.id,
                Document.file_hash == file_hash,
                Document.status != DocumentStatus.DELETED,
            )
            .first()
        )
        if existing:
            results.append(
                UploadItemResponse(
                    status="duplicate",
                    message="This file already exists in the selected folder.",
                    file_name=file_name,
                    document_id=existing.id,
                )
            )
            continue
        stored_name, path = save_upload(settings.upload_dir, folder.slug, upload, content)
        document = Document(
            folder_id=folder.id,
            file_name=file_name,
            stored_file_name=stored_name,
            file_type=file_type,
            file_path=str(path),
            file_hash=file_hash,
            status=DocumentStatus.UPLOADED,
        )
        db.add(document)
        uploaded_any = True
        db.commit()
        db.refresh(document)
        results.append(
            UploadItemResponse(
                status="uploaded",
                message="File uploaded successfully.",
                file_name=file_name,
                document_id=document.id,
            )
        )

    if uploaded_any:
        folder.status = FolderStatus.NEEDS_REINDEX if folder.status == FolderStatus.INDEXED else FolderStatus.HAS_FILES
        db.add(folder)
        db.commit()
    return UploadResponse(folder_name=folder.display_name, results=results)


@router.get("/documents", response_model=list[DocumentResponse])
def list_documents(folder_name: str, db: Session = Depends(get_db)) -> list[DocumentResponse]:
    folder = _resolve_folder(db, folder_name)
    return (
        db.query(Document)
        .filter(Document.folder_id == folder.id, Document.status != DocumentStatus.DELETED)
        .order_by(Document.uploaded_at.desc())
        .all()
    )


@router.delete("/documents/{document_id}", response_model=ApiMessage)
def delete_document(folder_name: str, document_id: str, db: Session = Depends(get_db)) -> ApiMessage:
    folder = _resolve_folder(db, folder_name)
    document = (
        db.query(Document)
        .filter(Document.folder_id == folder.id, Document.id == document_id, Document.status != DocumentStatus.DELETED)
        .first()
    )
    if not document:
        raise not_found("Document not found.")
    delete_file_if_exists(document.file_path)
    document.status = DocumentStatus.DELETED
    folder.status = FolderStatus.NEEDS_REINDEX
    db.add(document)
    db.add(folder)
    db.commit()
    return ApiMessage(message="Document deleted successfully.")
