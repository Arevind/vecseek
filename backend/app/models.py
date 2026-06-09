from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Optional
from uuid import uuid4

from sqlalchemy import JSON, Boolean, DateTime, Enum as SqlEnum, Float, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class FolderStatus(str, Enum):
    EMPTY = "empty"
    HAS_FILES = "has_files"
    INDEXING = "indexing"
    INDEXED = "indexed"
    NEEDS_REINDEX = "needs_reindex"
    FAILED = "failed"


class DocumentStatus(str, Enum):
    UPLOADED = "uploaded"
    INDEXED = "indexed"
    FAILED = "failed"
    DELETED = "deleted"


class IndexJobStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class EvalProvider(str, Enum):
    OLLAMA = "ollama"
    OPENAI = "openai"


class EvalCaseType(str, Enum):
    RETRIEVAL = "retrieval"
    ANSWER = "answer"
    REDTEAM = "redteam"
    ALL = "all"


class EvalRunType(str, Enum):
    FULL = "full"
    RETRIEVAL = "retrieval"
    ANSWER = "answer"
    REDTEAM = "redteam"


class EvalTriggerType(str, Enum):
    MANUAL = "manual"
    AUTO = "auto"


class EvalRunStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class Folder(Base):
    __tablename__ = "folders"
    __table_args__ = (UniqueConstraint("slug", name="uq_folder_slug"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    display_name: Mapped[str] = mapped_column(String(255), nullable=False)
    normalized_name: Mapped[str] = mapped_column(String(255), nullable=False, unique=True, index=True)
    slug: Mapped[str] = mapped_column(String(255), nullable=False)
    collection_name: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    status: Mapped[FolderStatus] = mapped_column(SqlEnum(FolderStatus), default=FolderStatus.EMPTY, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow, nullable=False)

    documents: Mapped[list["Document"]] = relationship(back_populates="folder", cascade="all, delete-orphan")
    index_jobs: Mapped[list["IndexJob"]] = relationship(back_populates="folder", cascade="all, delete-orphan")
    eval_profile: Mapped[Optional["EvalProfile"]] = relationship(back_populates="folder", cascade="all, delete-orphan", uselist=False)
    eval_cases: Mapped[list["EvalCase"]] = relationship(back_populates="folder", cascade="all, delete-orphan")
    eval_runs: Mapped[list["EvalRun"]] = relationship(back_populates="folder", cascade="all, delete-orphan")


class Document(Base):
    __tablename__ = "documents"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    folder_id: Mapped[str] = mapped_column(String(36), ForeignKey("folders.id"), nullable=False, index=True)
    file_name: Mapped[str] = mapped_column(String(255), nullable=False)
    stored_file_name: Mapped[str] = mapped_column(String(255), nullable=False)
    file_type: Mapped[str] = mapped_column(String(16), nullable=False)
    file_path: Mapped[str] = mapped_column(Text, nullable=False)
    file_hash: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    status: Mapped[DocumentStatus] = mapped_column(SqlEnum(DocumentStatus), default=DocumentStatus.UPLOADED, nullable=False)
    uploaded_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)
    indexed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    folder: Mapped["Folder"] = relationship(back_populates="documents")


class IndexJob(Base):
    __tablename__ = "index_jobs"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    folder_id: Mapped[str] = mapped_column(String(36), ForeignKey("folders.id"), nullable=False, index=True)
    status: Mapped[IndexJobStatus] = mapped_column(SqlEnum(IndexJobStatus), default=IndexJobStatus.PENDING, nullable=False)
    total_files: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    processed_files: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    total_chunks: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    folder: Mapped["Folder"] = relationship(back_populates="index_jobs")


class Setting(Base):
    __tablename__ = "settings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, default=1)
    default_top_k: Mapped[int] = mapped_column(Integer, default=5, nullable=False)
    chunk_size: Mapped[int] = mapped_column(Integer, default=1400, nullable=False)
    chunk_overlap: Mapped[int] = mapped_column(Integer, default=250, nullable=False)
    vector_candidate_limit: Mapped[int] = mapped_column(Integer, default=32, nullable=False)
    retrieval_concurrency_limit: Mapped[int] = mapped_column(Integer, default=12, nullable=False)
    indexing_worker_concurrency: Mapped[int] = mapped_column(Integer, default=2, nullable=False)
    hybrid_retrieval_enabled: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    reranker_enabled: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow, nullable=False)


class IndexedChunk(Base):
    __tablename__ = "indexed_chunks"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    folder_id: Mapped[str] = mapped_column(String(36), ForeignKey("folders.id"), nullable=False, index=True)
    document_id: Mapped[str] = mapped_column(String(36), ForeignKey("documents.id"), nullable=False, index=True)
    collection_name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    source_file: Mapped[str] = mapped_column(String(255), nullable=False)
    file_type: Mapped[str] = mapped_column(String(16), nullable=False)
    content_type: Mapped[str] = mapped_column(String(32), nullable=False)
    page_number: Mapped[int] = mapped_column(Integer, default=-1, nullable=False)
    table_index: Mapped[int] = mapped_column(Integer, default=-1, nullable=False)
    row_index: Mapped[int] = mapped_column(Integer, default=-1, nullable=False)
    chunk_index: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    file_hash: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow, nullable=False)


class EvalProfile(Base):
    __tablename__ = "eval_profiles"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    folder_id: Mapped[str] = mapped_column(String(36), ForeignKey("folders.id"), nullable=False, unique=True, index=True)
    provider: Mapped[EvalProvider] = mapped_column(SqlEnum(EvalProvider), default=EvalProvider.OLLAMA, nullable=False)
    model_name: Mapped[str] = mapped_column(String(255), default="", nullable=False)
    auto_run_enabled: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow, nullable=False)

    folder: Mapped["Folder"] = relationship(back_populates="eval_profile")


class EvalCase(Base):
    __tablename__ = "eval_cases"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    folder_id: Mapped[str] = mapped_column(String(36), ForeignKey("folders.id"), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    question: Mapped[str] = mapped_column(Text, nullable=False)
    reference_answer: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    expected_answer_points: Mapped[list[str]] = mapped_column(JSON, default=list, nullable=False)
    expected_source_files: Mapped[list[str]] = mapped_column(JSON, default=list, nullable=False)
    tags: Mapped[list[str]] = mapped_column(JSON, default=list, nullable=False)
    case_type: Mapped[EvalCaseType] = mapped_column(SqlEnum(EvalCaseType), default=EvalCaseType.ALL, nullable=False)
    enabled: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow, nullable=False)

    folder: Mapped["Folder"] = relationship(back_populates="eval_cases")
    run_items: Mapped[list["EvalRunItem"]] = relationship(back_populates="eval_case")


class EvalRun(Base):
    __tablename__ = "eval_runs"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    folder_id: Mapped[str] = mapped_column(String(36), ForeignKey("folders.id"), nullable=False, index=True)
    profile_id: Mapped[Optional[str]] = mapped_column(String(36), ForeignKey("eval_profiles.id"), nullable=True, index=True)
    previous_run_id: Mapped[Optional[str]] = mapped_column(String(36), ForeignKey("eval_runs.id"), nullable=True)
    run_type: Mapped[EvalRunType] = mapped_column(SqlEnum(EvalRunType), default=EvalRunType.FULL, nullable=False)
    trigger_type: Mapped[EvalTriggerType] = mapped_column(SqlEnum(EvalTriggerType), default=EvalTriggerType.MANUAL, nullable=False)
    status: Mapped[EvalRunStatus] = mapped_column(SqlEnum(EvalRunStatus), default=EvalRunStatus.PENDING, nullable=False)
    provider: Mapped[EvalProvider] = mapped_column(SqlEnum(EvalProvider), default=EvalProvider.OLLAMA, nullable=False)
    model_name: Mapped[str] = mapped_column(String(255), default="", nullable=False)
    summary_metrics: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    folder: Mapped["Folder"] = relationship(back_populates="eval_runs")
    profile: Mapped[Optional["EvalProfile"]] = relationship()
    previous_run: Mapped[Optional["EvalRun"]] = relationship(remote_side="EvalRun.id")
    run_items: Mapped[list["EvalRunItem"]] = relationship(back_populates="eval_run", cascade="all, delete-orphan")
    artifacts: Mapped[list["EvalRunArtifact"]] = relationship(back_populates="eval_run", cascade="all, delete-orphan")


class EvalRunItem(Base):
    __tablename__ = "eval_run_items"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    run_id: Mapped[str] = mapped_column(String(36), ForeignKey("eval_runs.id"), nullable=False, index=True)
    case_id: Mapped[Optional[str]] = mapped_column(String(36), ForeignKey("eval_cases.id"), nullable=True, index=True)
    eval_type: Mapped[EvalRunType] = mapped_column(SqlEnum(EvalRunType), default=EvalRunType.RETRIEVAL, nullable=False)
    score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    passed: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    details: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)

    eval_run: Mapped["EvalRun"] = relationship(back_populates="run_items")
    eval_case: Mapped[Optional["EvalCase"]] = relationship(back_populates="run_items")


class EvalRunArtifact(Base):
    __tablename__ = "eval_run_artifacts"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    run_id: Mapped[str] = mapped_column(String(36), ForeignKey("eval_runs.id"), nullable=False, index=True)
    artifact_type: Mapped[str] = mapped_column(String(64), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)

    eval_run: Mapped["EvalRun"] = relationship(back_populates="artifacts")
