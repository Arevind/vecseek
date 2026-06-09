from __future__ import annotations

from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.models import (
    DocumentStatus,
    EvalCaseType,
    EvalProvider,
    EvalRunStatus,
    EvalRunType,
    EvalTriggerType,
    FolderStatus,
    IndexJobStatus,
)


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
    vector_candidate_limit: int
    retrieval_concurrency_limit: int
    indexing_worker_concurrency: int
    hybrid_retrieval_enabled: bool
    reranker_enabled: bool


class SettingsUpdateRequest(BaseModel):
    default_top_k: int = Field(..., ge=1)
    chunk_size: int = Field(..., ge=200, le=5000)
    chunk_overlap: int = Field(..., ge=0, le=1000)
    vector_candidate_limit: int = Field(..., ge=5, le=200)
    retrieval_concurrency_limit: int = Field(..., ge=1, le=128)
    indexing_worker_concurrency: int = Field(..., ge=1, le=16)
    hybrid_retrieval_enabled: bool
    reranker_enabled: bool


class HealthResponse(BaseModel):
    status: str
    service: str


class DiagnosticsResponse(BaseModel):
    status: str
    service: str
    qdrant_mode: str
    embedding_model: str
    runtime_metrics: dict[str, float | int]


class EvalProfileResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    folder_id: str
    provider: EvalProvider
    model_name: str
    auto_run_enabled: bool
    created_at: datetime
    updated_at: datetime


class EvalProfileUpdateRequest(BaseModel):
    provider: EvalProvider
    model_name: str
    auto_run_enabled: bool = False

    @field_validator("model_name")
    @classmethod
    def validate_model_name(cls, value: str) -> str:
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("model_name is required.")
        return cleaned


class EvalCaseRequest(BaseModel):
    name: str
    question: str
    reference_answer: Optional[str] = None
    expected_answer_points: list[str] = Field(default_factory=list)
    expected_source_files: list[str] = Field(default_factory=list)
    tags: list[str] = Field(default_factory=list)
    case_type: EvalCaseType = EvalCaseType.ALL
    enabled: bool = True

    @field_validator("name", "question")
    @classmethod
    def validate_text(cls, value: str) -> str:
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("This field is required.")
        return cleaned


class EvalCaseResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    folder_id: str
    name: str
    question: str
    reference_answer: Optional[str] = None
    expected_answer_points: list[str]
    expected_source_files: list[str]
    tags: list[str]
    case_type: EvalCaseType
    enabled: bool
    created_at: datetime
    updated_at: datetime


class EvalRunStartRequest(BaseModel):
    run_type: EvalRunType = EvalRunType.FULL
    provider: Optional[EvalProvider] = None
    model_name: Optional[str] = None
    openai_api_key: Optional[str] = None


class EvalRunItemResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    run_id: str
    case_id: Optional[str] = None
    eval_type: EvalRunType
    score: Optional[float] = None
    passed: bool
    details: dict[str, Any]
    created_at: datetime


class EvalRunArtifactResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    run_id: str
    artifact_type: str
    name: str
    content: str
    created_at: datetime


class EvalRunSummaryResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    folder_id: str
    profile_id: Optional[str] = None
    previous_run_id: Optional[str] = None
    run_type: EvalRunType
    trigger_type: EvalTriggerType
    status: EvalRunStatus
    provider: EvalProvider
    model_name: str
    summary_metrics: dict[str, Any]
    error_message: Optional[str] = None
    started_at: datetime
    completed_at: Optional[datetime] = None


class EvalRunDetailResponse(EvalRunSummaryResponse):
    items: list[EvalRunItemResponse]
    artifacts: list[EvalRunArtifactResponse]


class OllamaModelResponse(BaseModel):
    name: str
    size: Optional[int] = None
    modified_at: Optional[str] = None


class OllamaModelsListResponse(BaseModel):
    models: list[OllamaModelResponse]


IndexStatusResponse.model_rebuild()
