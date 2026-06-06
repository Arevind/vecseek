from __future__ import annotations

from collections import Counter


def _normalize_headers(headers: list[str]) -> list[str]:
    cleaned = [header.strip() if header and header.strip() else "" for header in headers]
    duplicates = Counter(cleaned)
    normalized: list[str] = []
    for index, header in enumerate(cleaned, start=1):
        if not header or duplicates[header] > 1:
            normalized.append(f"Column {index}")
        else:
            normalized.append(header)
    return normalized


def table_to_records(table_name: str, file_name: str, rows: list[list[str | None]]) -> list[str]:
    if not rows:
        return []
    header_row = rows[0]
    headers = _normalize_headers([str(cell or "").strip() for cell in header_row])
    records: list[str] = []
    for row_index, row in enumerate(rows[1:], start=1):
        pairs = []
        for column_index, header in enumerate(headers):
            value = "N/A"
            if column_index < len(row) and row[column_index] not in (None, ""):
                value = str(row[column_index]).strip() or "N/A"
            pairs.append(f"{header}: {value}")
        record_text = "\n".join(
            [
                f"{table_name} from file: {file_name}",
                "",
                f"Record {row_index}:",
                *pairs,
            ]
        ).strip()
        records.append(record_text)
    return records
