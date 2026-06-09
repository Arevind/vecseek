from __future__ import annotations

from sqlalchemy import create_engine
from sqlalchemy import text
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from app.config import get_settings


class Base(DeclarativeBase):
    pass


settings = get_settings()
engine = create_engine(settings.sqlite_url, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def init_db() -> None:
    from app.models import Document, EvalCase, EvalProfile, EvalRun, EvalRunArtifact, EvalRunItem, Folder, IndexJob, IndexedChunk, Setting  # noqa: F401

    Base.metadata.create_all(bind=engine)
    with engine.begin() as connection:
        columns = {
            row[1]
            for row in connection.execute(text("PRAGMA table_info(settings)")).fetchall()
        }
        if "chunk_size" not in columns:
            connection.execute(text("ALTER TABLE settings ADD COLUMN chunk_size INTEGER NOT NULL DEFAULT 1400"))
        if "chunk_overlap" not in columns:
            connection.execute(text("ALTER TABLE settings ADD COLUMN chunk_overlap INTEGER NOT NULL DEFAULT 250"))
        if "vector_candidate_limit" not in columns:
            connection.execute(text("ALTER TABLE settings ADD COLUMN vector_candidate_limit INTEGER NOT NULL DEFAULT 32"))
        if "retrieval_concurrency_limit" not in columns:
            connection.execute(text("ALTER TABLE settings ADD COLUMN retrieval_concurrency_limit INTEGER NOT NULL DEFAULT 12"))
        if "indexing_worker_concurrency" not in columns:
            connection.execute(text("ALTER TABLE settings ADD COLUMN indexing_worker_concurrency INTEGER NOT NULL DEFAULT 2"))
        if "hybrid_retrieval_enabled" not in columns:
            connection.execute(text("ALTER TABLE settings ADD COLUMN hybrid_retrieval_enabled INTEGER NOT NULL DEFAULT 1"))
        if "reranker_enabled" not in columns:
            connection.execute(text("ALTER TABLE settings ADD COLUMN reranker_enabled INTEGER NOT NULL DEFAULT 1"))

        connection.execute(
            text(
                """
                CREATE VIRTUAL TABLE IF NOT EXISTS indexed_chunks_fts
                USING fts5(
                    content,
                    source_file,
                    content='indexed_chunks',
                    content_rowid='rowid',
                    tokenize='porter unicode61'
                )
                """
            )
        )
        connection.execute(
            text(
                """
                CREATE TRIGGER IF NOT EXISTS indexed_chunks_ai AFTER INSERT ON indexed_chunks BEGIN
                    INSERT INTO indexed_chunks_fts(rowid, content, source_file)
                    VALUES (new.rowid, new.content, new.source_file);
                END
                """
            )
        )
        connection.execute(
            text(
                """
                CREATE TRIGGER IF NOT EXISTS indexed_chunks_ad AFTER DELETE ON indexed_chunks BEGIN
                    INSERT INTO indexed_chunks_fts(indexed_chunks_fts, rowid, content, source_file)
                    VALUES ('delete', old.rowid, old.content, old.source_file);
                END
                """
            )
        )
        connection.execute(
            text(
                """
                CREATE TRIGGER IF NOT EXISTS indexed_chunks_au AFTER UPDATE ON indexed_chunks BEGIN
                    INSERT INTO indexed_chunks_fts(indexed_chunks_fts, rowid, content, source_file)
                    VALUES ('delete', old.rowid, old.content, old.source_file);
                    INSERT INTO indexed_chunks_fts(rowid, content, source_file)
                    VALUES (new.rowid, new.content, new.source_file);
                END
                """
            )
        )
        connection.execute(text("INSERT INTO indexed_chunks_fts(indexed_chunks_fts) VALUES ('rebuild')"))
