from __future__ import annotations

from pathlib import Path
from uuid import uuid4

from fastapi import UploadFile


def build_folder_dir(upload_dir: Path, folder_slug: str) -> Path:
    return upload_dir / folder_slug


def save_upload(upload_dir: Path, folder_slug: str, upload: UploadFile, content: bytes) -> tuple[str, Path]:
    target_dir = build_folder_dir(upload_dir, folder_slug)
    target_dir.mkdir(parents=True, exist_ok=True)
    suffix = Path(upload.filename or "").suffix.lower()
    stored_name = f"{uuid4().hex}{suffix}"
    target_path = target_dir / stored_name
    target_path.write_bytes(content)
    return stored_name, target_path


def delete_file_if_exists(path: str | Path) -> None:
    candidate = Path(path)
    if candidate.exists() and candidate.is_file():
        candidate.unlink()
