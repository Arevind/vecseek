from __future__ import annotations

import re
import unicodedata


def normalize_name(value: str) -> str:
    return " ".join(value.strip().split()).casefold()


def slugify(value: str) -> str:
    normalized = unicodedata.normalize("NFKD", value)
    ascii_value = normalized.encode("ascii", "ignore").decode("ascii")
    slug = re.sub(r"[^a-zA-Z0-9]+", "-", ascii_value).strip("-").lower()
    return slug or "workspace"


def make_collection_name(slug: str) -> str:
    return f"kb-{slug}"
