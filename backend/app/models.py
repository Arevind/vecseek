from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Optional
from uuid import uuid4

from sqlalchemy import DateTime, Enum as SqlEnum, ForeignKey, Integer, String, Text, UniqueConstraint
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
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow, nullable=False)
