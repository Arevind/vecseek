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
    from app.models import Document, Folder, IndexJob, Setting  # noqa: F401

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
