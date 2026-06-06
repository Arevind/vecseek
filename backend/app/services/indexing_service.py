from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

from sqlalchemy.orm import Session

from app.config import get_settings
from app.models import Document, DocumentStatus, Folder, FolderStatus, IndexJob, IndexJobStatus, Setting
from app.services.chunking import build_chunk_id, merge_blocks, split_text
from app.services.embeddings import embed_texts
from app.services.job_progress import clear_job_progress, set_job_progress
from app.services.preprocessing.docx_parser import extract_docx_blocks
from app.services.preprocessing.pdf_parser import extract_pdf_blocks
from app.services.qdrant_service import get_client, reset_collection
from app.services.preprocessing.txt_parser import extract_txt_blocks
from app.utils.errors import bad_request
from qdrant_client.http import models as qdrant_models


def _extract_blocks(document: Document) -> list[dict]:
    path = Path(document.file_path)
    if document.file_type == "pdf":
        return extract_pdf_blocks(path, document.file_name)
    if document.file_type == "docx":
        return extract_docx_blocks(path, document.file_name)
    if document.file_type == "txt":
        return extract_txt_blocks(path, document.file_name)
    raise bad_request(f"Unsupported file type: {document.file_type}")


def _build_embedding_text(folder: Folder, document: Document, block: dict, chunk: str) -> str:
    content_label = "table record" if block.get("content_type") == "table" else "document text"
    page_number = int(block.get("page_number", -1))
    page_label = f"Page {page_number}" if page_number >= 0 else "Page unavailable"
    return (
        f"Folder: {folder.display_name}\n"
        f"Source file: {document.file_name}\n"
        f"File type: {document.file_type}\n"
        f"Content type: {content_label}\n"
        f"{page_label}\n\n"
        f"{chunk}"
    )


def index_folder(db: Session, folder: Folder) -> tuple[IndexJob, int]:
    settings = get_settings()
    stored_settings = db.get(Setting, 1)
    chunk_size = stored_settings.chunk_size if stored_settings else settings.chunk_size
    chunk_overlap = stored_settings.chunk_overlap if stored_settings else settings.chunk_overlap
    documents = [
        document
        for document in folder.documents
        if document.status != DocumentStatus.DELETED
    ]
    if not documents:
        raise bad_request("Cannot index a folder with no documents.")

    job = IndexJob(
        folder_id=folder.id,
        status=IndexJobStatus.RUNNING,
        total_files=len(documents),
        processed_files=0,
        total_chunks=0,
    )
    folder.status = FolderStatus.INDEXING
    db.add(job)
    db.commit()
    db.refresh(job)
    set_job_progress(job.id, phase="preparing", progress_percent=2, message="Preparing indexing job")

    now = datetime.now(timezone.utc)
    reset_collection(folder.collection_name)
    client = get_client()
    all_ids: list[str] = []
    all_documents: list[str] = []
    all_embedding_inputs: list[str] = []
    all_payloads: list[dict] = []

    try:
        for document in documents:
            blocks = merge_blocks(_extract_blocks(document), chunk_size * 2)
            if not blocks:
                raise ValueError(f"Empty extracted document: {document.file_name}")
            for block_index, block in enumerate(blocks):
                chunks = split_text(block["text"], chunk_size, chunk_overlap)
                for chunk_index, chunk in enumerate(chunks):
                    payload = {
                        "folder_id": folder.id,
                        "folder_name": folder.display_name,
                        "collection_name": folder.collection_name,
                        "source_file": document.file_name,
                        "file_id": document.id,
                        "file_type": document.file_type,
                        "content_type": block["content_type"],
                        "page_number": int(block.get("page_number", -1)),
                        "table_index": int(block.get("table_index", -1)),
                        "row_index": int(block.get("row_index", -1)),
                        "chunk_index": chunk_index,
                        "file_hash": document.file_hash,
                        "created_at": now.isoformat(),
                        "updated_at": now.isoformat(),
                        "content": chunk,
                    }
                    chunk_id = build_chunk_id(folder.id, document.id, block_index, chunk_index, chunk)
                    all_ids.append(chunk_id)
                    all_documents.append(chunk)
                    all_embedding_inputs.append(_build_embedding_text(folder, document, block, chunk))
                    all_payloads.append(payload)
            document.status = DocumentStatus.INDEXED
            document.indexed_at = now
            job.processed_files += 1
            file_progress = int((job.processed_files / max(job.total_files, 1)) * 70)
            set_job_progress(
                job.id,
                phase="preparing",
                progress_percent=max(5, file_progress),
                message=f"Processed {job.processed_files} of {job.total_files} files",
            )
            db.add(document)
            db.add(job)
            db.commit()

        set_job_progress(
            job.id,
            phase="embedding",
            progress_percent=78,
            message=f"Generating embeddings for {len(all_documents)} chunks",
        )
        embeddings = embed_texts(all_embedding_inputs)

        set_job_progress(
            job.id,
            phase="storing",
            progress_percent=92,
            message="Writing chunks to the vector index",
        )
        points = [
            qdrant_models.PointStruct(id=point_id, vector=vector, payload=payload)
            for point_id, vector, payload in zip(all_ids, embeddings, all_payloads)
        ]
        client.upsert(collection_name=folder.collection_name, points=points, wait=True)

        set_job_progress(
            job.id,
            phase="finalizing",
            progress_percent=97,
            message="Finalizing folder index",
        )
        job.status = IndexJobStatus.COMPLETED
        job.total_chunks = len(all_ids)
        job.completed_at = datetime.now(timezone.utc)
        folder.status = FolderStatus.INDEXED
        db.add(job)
        db.add(folder)
        db.commit()
        db.refresh(job)
        set_job_progress(job.id, phase="completed", progress_percent=100, message="Indexing complete")
        return job, len(all_ids)
    except Exception as exc:
        set_job_progress(job.id, phase="failed", progress_percent=100, message=str(exc))
        job.status = IndexJobStatus.FAILED
        job.error_message = str(exc)
        job.completed_at = datetime.now(timezone.utc)
        folder.status = FolderStatus.FAILED
        for document in documents:
            if document.status != DocumentStatus.DELETED:
                document.status = DocumentStatus.FAILED
                db.add(document)
        db.add(job)
        db.add(folder)
        db.commit()
        raise
