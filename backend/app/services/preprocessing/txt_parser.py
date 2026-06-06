from __future__ import annotations

from pathlib import Path

from app.services.preprocessing.cleaner import normalize_whitespace


def extract_txt_blocks(path: Path, file_name: str) -> list[dict]:
    encodings = ["utf-8", "utf-8-sig", "latin-1"]
    content = None
    for encoding in encodings:
        try:
            content = path.read_text(encoding=encoding)
            break
        except UnicodeDecodeError:
            continue
    if content is None:
        raise ValueError(f"Failed to decode TXT file: {file_name}")
    cleaned = normalize_whitespace(content)
    if not cleaned:
        return []
    return [
        {
            "text": cleaned,
            "content_type": "text",
            "page_number": -1,
            "table_index": -1,
            "row_index": -1,
        }
    ]
