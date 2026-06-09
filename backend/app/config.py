from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path

from pydantic import AliasChoices, Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_name: str = "VecSeek"
    backend_host: str = "0.0.0.0"
    backend_port: int = 8000
    frontend_port: int = 3000
    kb_api_key: str = "change-this-secret"
    cors_origins: list[str] = Field(default_factory=lambda: ["http://localhost:3000"])
    upload_dir: Path = Path("./data/uploads")
    qdrant_mode: str = "local"
    qdrant_dir: Path = Field(
        default=Path("./data/qdrant"),
        validation_alias=AliasChoices("QDRANT_DIR", "CHROMA_DIR"),
    )
    qdrant_url: str | None = None
    qdrant_api_key: str | None = None
    qdrant_prefer_grpc: bool = False
    sqlite_path: Path = Path("./data/sqlite/knowledgebase.db")
    embedding_model: str = "BAAI/bge-base-en-v1.5"
    default_top_k: int = 5
    max_top_k: int = 20
    chunk_size: int = 1400
    chunk_overlap: int = 250
    vector_candidate_limit: int = 32
    hybrid_retrieval_enabled: bool = True
    reranker_enabled: bool = True
    retrieval_concurrency_limit: int = 12
    indexing_worker_concurrency: int = 2
    retrieval_timeout_seconds: float = 8.0
    eval_concurrency_limit: int = 1
    eval_timeout_seconds: float = 45.0
    ollama_base_url: str = "http://localhost:11434"
    openai_base_url: str = "https://api.openai.com/v1"
    promptfoo_command: str = "npx promptfoo"

    @field_validator("cors_origins", mode="before")
    @classmethod
    def parse_cors_origins(cls, value: str | list[str]) -> list[str]:
        if isinstance(value, list):
            return value
        text = value.strip()
        if text.startswith("[") and text.endswith("]"):
            try:
                loaded = json.loads(text)
                if isinstance(loaded, list):
                    return [str(item).strip() for item in loaded if str(item).strip()]
            except json.JSONDecodeError:
                inner = text[1:-1]
                return [item.strip() for item in inner.split(",") if item.strip()]
        return [item.strip() for item in text.split(",") if item.strip()]

    @property
    def sqlite_url(self) -> str:
        return f"sqlite:///{self.sqlite_path.as_posix()}"

    def ensure_directories(self) -> None:
        self.upload_dir.mkdir(parents=True, exist_ok=True)
        if self.qdrant_mode != "server":
            self.qdrant_dir.mkdir(parents=True, exist_ok=True)
        self.sqlite_path.parent.mkdir(parents=True, exist_ok=True)


@lru_cache
def get_settings() -> Settings:
    settings = Settings()
    settings.ensure_directories()
    return settings
