from __future__ import annotations

from pathlib import Path

import pdfplumber
from pypdf import PdfReader

from app.services.preprocessing.cleaner import normalize_whitespace
from app.services.preprocessing.table_converter import table_to_records


def extract_pdf_blocks(path: Path, file_name: str) -> list[dict]:
    blocks: list[dict] = []
    try:
        reader = PdfReader(str(path))
        for page_index, page in enumerate(reader.pages, start=1):
            text = normalize_whitespace(page.extract_text() or "")
            if text:
                blocks.append(
                    {
                        "text": text,
                        "content_type": "text",
                        "page_number": page_index,
                        "table_index": -1,
                        "row_index": -1,
                    }
                )
    except Exception as exc:  # pragma: no cover - library error surface
        raise ValueError(f"Failed to extract PDF text: {file_name}") from exc

    try:
        with pdfplumber.open(str(path)) as pdf:
            for page_index, page in enumerate(pdf.pages, start=1):
                tables = page.extract_tables() or []
                for table_index, table in enumerate(tables, start=1):
                    for row_index, record in enumerate(
                        table_to_records(f"Table {table_index} on page {page_index}", file_name, table),
                        start=1,
                    ):
                        blocks.append(
                            {
                                "text": normalize_whitespace(record),
                                "content_type": "table",
                                "page_number": page_index,
                                "table_index": table_index,
                                "row_index": row_index,
                            }
                        )
    except Exception:
        # Table extraction quality varies; text blocks remain available even if table extraction fails.
        pass
    return blocks
