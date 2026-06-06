from __future__ import annotations

from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.models import DocumentStatus, FolderStatus, IndexJobStatus


class ApiMessage(BaseModel):
    status: str = "success"
    message: str


class FolderCreateRequest(BaseModel):
    folder_name: str

    @field_validator("folder_name")
    @classmethod
    def validate_folder_name(cls, value: str) -> str:
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("Folder name is required.")
        return cleaned


class FolderResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    display_name: str
    slug: str
    collection_name: str
    status: FolderStatus
    document_count: int = 0
    indexed_chunk_count: int = 0
    created_at: datetime
    updated_at: datetime


class DocumentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    file_name: str
    stored_file_name: str
    file_type: str
    file_hash: str
    status: DocumentStatus
    uploaded_at: datetime
    indexed_at: Optional[datetime] = None


class FolderDetailResponse(FolderResponse):
    documents: list[DocumentResponse]


class UploadItemResponse(BaseModel):
    status: str
    message: str
    file_name: str
    document_id: Optional[str] = None


class UploadResponse(BaseModel):
    folder_name: str
    results: list[UploadItemResponse]


class IndexResponse(BaseModel):
    message: str
    folder_name: str
    collection_name: str
    total_files: int = 0
    total_chunks: int = 0
    status: str
    job_id: Optional[str] = None


class IndexStatusResponse(BaseModel):
    folder_name: str
    status: FolderStatus
    latest_job: Optional["IndexJobResponse"] = None


class IndexJobResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    status: IndexJobStatus
    total_files: int
    processed_files: int
    total_chunks: int
    error_message: Optional[str] = None
    started_at: datetime
    completed_at: Optional[datetime] = None
    phase: Optional[str] = None
    progress_percent: Optional[int] = None
    status_message: Optional[str] = None


class RetrievalRequest(BaseModel):
    folder_name: str
    query: str
    top_k: Optional[int] = None

    @field_validator("folder_name")
    @classmethod
    def validate_folder_name(cls, value: str) -> str:
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("folder_name is required.")
        return cleaned

    @field_validator("query")
    @classmethod
    def validate_query(cls, value: str) -> str:
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("query is required.")
        return cleaned


class RetrievalResult(BaseModel):
    content: str
    score: float
    metadata: dict[str, Any]


class RetrievalResponse(BaseModel):
    folder_name: str
    query: str
    top_k: int
    results: list[RetrievalResult]


class SettingsResponse(BaseModel):
    default_top_k: int
    max_top_k: int
    chunk_size: int
    chunk_overlap: int


class SettingsUpdateRequest(BaseModel):
    default_top_k: int = Field(..., ge=1)
    chunk_size: int = Field(..., ge=200, le=5000)
    chunk_overlap: int = Field(..., ge=0, le=1000)


class HealthResponse(BaseModel):
    status: str
    service: str


IndexStatusResponse.model_rebuild()
