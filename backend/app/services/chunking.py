from __future__ import annotations

import re
from uuid import NAMESPACE_URL, uuid5


def _split_long_text(text: str, chunk_size: int, chunk_overlap: int) -> list[str]:
    if len(text) <= chunk_size:
        return [text.strip()]

    sentences = re.split(r"(?<=[.!?])\s+", text)
    chunks: list[str] = []
    current = ""
    for sentence in sentences:
        candidate = f"{current} {sentence}".strip() if current else sentence.strip()
        if current and len(candidate) > chunk_size:
            chunks.append(current.strip())
            overlap_text = current[-chunk_overlap:].strip() if chunk_overlap > 0 else ""
            current = f"{overlap_text} {sentence}".strip() if overlap_text else sentence.strip()
            continue
        if not current and len(sentence) > chunk_size:
            start = 0
            while start < len(sentence):
                end = min(len(sentence), start + chunk_size)
                chunks.append(sentence[start:end].strip())
                if end >= len(sentence):
                    current = ""
                    break
                start = max(end - chunk_overlap, start + 1)
            continue
        current = candidate

    if current.strip():
        chunks.append(current.strip())
    return [chunk for chunk in chunks if chunk]


def split_text(text: str, chunk_size: int, chunk_overlap: int) -> list[str]:
    if len(text) <= chunk_size:
        return [text]
    paragraphs = [paragraph.strip() for paragraph in re.split(r"\n{2,}", text) if paragraph.strip()]
    if len(paragraphs) <= 1:
        return _split_long_text(text, chunk_size, chunk_overlap)

    chunks: list[str] = []
    current = ""
    for paragraph in paragraphs:
        candidate = f"{current}\n\n{paragraph}".strip() if current else paragraph
        if current and len(candidate) > chunk_size:
            chunks.append(current.strip())
            overlap_text = current[-chunk_overlap:].strip() if chunk_overlap > 0 else ""
            current = f"{overlap_text}\n\n{paragraph}".strip() if overlap_text else paragraph
            continue
        if not current and len(paragraph) > chunk_size:
            chunks.extend(_split_long_text(paragraph, chunk_size, chunk_overlap))
            current = ""
            continue
        current = candidate

    if current.strip():
        chunks.append(current.strip())
    return [chunk for chunk in chunks if chunk]


def merge_blocks(blocks: list[dict], target_size: int) -> list[dict]:
    merged: list[dict] = []
    buffer: dict | None = None

    def flush_buffer() -> None:
        nonlocal buffer
        if buffer and buffer.get("text", "").strip():
            merged.append(buffer)
        buffer = None

    for block in blocks:
        block_copy = dict(block)
        block_text = str(block_copy.get("text", "")).strip()
        if not block_text:
            continue
        block_copy["text"] = block_text

        is_mergeable_text = block_copy.get("content_type") == "text"
        same_group = (
            buffer
            and buffer.get("content_type") == block_copy.get("content_type")
            and buffer.get("page_number", -1) == block_copy.get("page_number", -1)
            and buffer.get("table_index", -1) == block_copy.get("table_index", -1)
            and buffer.get("row_index", -1) == block_copy.get("row_index", -1)
        )

        if not is_mergeable_text:
            flush_buffer()
            merged.append(block_copy)
            continue

        if buffer is None:
            buffer = block_copy
            continue

        candidate = f"{buffer['text']}\n\n{block_text}".strip() if same_group else block_text
        if same_group and len(candidate) <= target_size:
            buffer["text"] = candidate
            continue

        flush_buffer()
        buffer = block_copy

    flush_buffer()
    return merged


def build_chunk_id(folder_id: str, file_id: str, block_index: int, chunk_index: int, text: str) -> str:
    seed = f"{folder_id}:{file_id}:{block_index}:{chunk_index}:{text}"
    return str(uuid5(NAMESPACE_URL, seed))
