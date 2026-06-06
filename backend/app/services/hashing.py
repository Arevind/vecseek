from __future__ import annotations

import hashlib
from pathlib import Path


def sha256_for_bytes(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()


def sha256_for_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as file:
        for chunk in iter(lambda: file.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()
