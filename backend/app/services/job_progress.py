from __future__ import annotations

from threading import Lock


_progress_lock = Lock()
_job_progress: dict[str, dict[str, int | str]] = {}


def set_job_progress(job_id: str, *, phase: str, progress_percent: int, message: str) -> None:
    with _progress_lock:
        _job_progress[job_id] = {
            "phase": phase,
            "progress_percent": max(0, min(100, progress_percent)),
            "message": message,
        }


def get_job_progress(job_id: str) -> dict[str, int | str] | None:
    with _progress_lock:
        progress = _job_progress.get(job_id)
        return dict(progress) if progress else None


def clear_job_progress(job_id: str) -> None:
    with _progress_lock:
        _job_progress.pop(job_id, None)
