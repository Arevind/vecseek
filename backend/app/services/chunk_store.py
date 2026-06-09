from __future__ import annotations

from sqlalchemy import text
from sqlalchemy.orm import Session

from app.models import IndexedChunk


def replace_folder_chunks(db: Session, folder_id: str, chunks: list[IndexedChunk]) -> None:
    db.query(IndexedChunk).filter(IndexedChunk.folder_id == folder_id).delete(synchronize_session=False)
    if chunks:
        db.bulk_save_objects(chunks)
    db.commit()


def delete_folder_chunks(db: Session, folder_id: str) -> None:
    db.query(IndexedChunk).filter(IndexedChunk.folder_id == folder_id).delete(synchronize_session=False)
    db.commit()


def search_keyword_chunks(db: Session, folder_id: str, query: str, limit: int) -> list[dict]:
    sql = text(
        """
        SELECT
            c.id,
            c.source_file,
            c.file_type,
            c.content_type,
            c.page_number,
            c.table_index,
            c.row_index,
            c.chunk_index,
            c.file_hash,
            c.content,
            bm25(indexed_chunks_fts) AS bm25_score
        FROM indexed_chunks_fts
        JOIN indexed_chunks c ON c.rowid = indexed_chunks_fts.rowid
        WHERE indexed_chunks_fts MATCH :query
          AND c.folder_id = :folder_id
        ORDER BY bm25(indexed_chunks_fts)
        LIMIT :limit
        """
    )
    rows = db.execute(sql, {"query": query, "folder_id": folder_id, "limit": limit}).mappings().all()
    return [dict(row) for row in rows]


def build_fts_query(query: str) -> str:
    tokens = []
    for raw in query.casefold().replace("?", " ").replace(":", " ").replace("/", " ").split():
        token = "".join(ch for ch in raw if ch.isalnum() or ch in {"_", "-"})
        if len(token) > 1:
            tokens.append(token)
    if not tokens:
        return ""
    return " OR ".join(f'"{token}"' for token in tokens[:12])
