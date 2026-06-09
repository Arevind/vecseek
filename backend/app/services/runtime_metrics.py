from __future__ import annotations

from collections import deque
from statistics import mean
from threading import Lock
from time import perf_counter


class RuntimeMetrics:
    def __init__(self) -> None:
        self._lock = Lock()
        self._queue_depth = 0
        self._active_index_jobs = 0
        self._active_eval_jobs = 0
        self._active_retrievals = 0
        self._rejected_retrievals = 0
        self._embedding_timings: deque[float] = deque(maxlen=100)
        self._qdrant_timings: deque[float] = deque(maxlen=100)
        self._retrieval_timings: deque[float] = deque(maxlen=100)
        self._folder_index_timings: deque[float] = deque(maxlen=100)
        self._eval_timings: deque[float] = deque(maxlen=100)

    def set_queue_depth(self, depth: int) -> None:
        with self._lock:
            self._queue_depth = max(0, depth)

    def increment_index_jobs(self) -> None:
        with self._lock:
            self._active_index_jobs += 1

    def decrement_index_jobs(self) -> None:
        with self._lock:
            self._active_index_jobs = max(0, self._active_index_jobs - 1)

    def increment_retrievals(self) -> None:
        with self._lock:
            self._active_retrievals += 1

    def decrement_retrievals(self) -> None:
        with self._lock:
            self._active_retrievals = max(0, self._active_retrievals - 1)

    def increment_rejected_retrievals(self) -> None:
        with self._lock:
            self._rejected_retrievals += 1

    def increment_eval_jobs(self) -> None:
        with self._lock:
            self._active_eval_jobs += 1

    def decrement_eval_jobs(self) -> None:
        with self._lock:
            self._active_eval_jobs = max(0, self._active_eval_jobs - 1)

    def record_embedding_time(self, seconds: float) -> None:
        with self._lock:
            self._embedding_timings.append(seconds)

    def record_qdrant_time(self, seconds: float) -> None:
        with self._lock:
            self._qdrant_timings.append(seconds)

    def record_retrieval_time(self, seconds: float) -> None:
        with self._lock:
            self._retrieval_timings.append(seconds)

    def record_folder_index_time(self, seconds: float) -> None:
        with self._lock:
            self._folder_index_timings.append(seconds)

    def record_eval_time(self, seconds: float) -> None:
        with self._lock:
            self._eval_timings.append(seconds)

    def snapshot(self) -> dict[str, float | int]:
        with self._lock:
            return {
                "queue_depth": self._queue_depth,
                "active_index_jobs": self._active_index_jobs,
                "active_eval_jobs": self._active_eval_jobs,
                "active_retrievals": self._active_retrievals,
                "rejected_retrievals": self._rejected_retrievals,
                "avg_embedding_seconds": round(mean(self._embedding_timings), 4) if self._embedding_timings else 0.0,
                "avg_qdrant_seconds": round(mean(self._qdrant_timings), 4) if self._qdrant_timings else 0.0,
                "avg_retrieval_seconds": round(mean(self._retrieval_timings), 4) if self._retrieval_timings else 0.0,
                "avg_folder_index_seconds": round(mean(self._folder_index_timings), 4) if self._folder_index_timings else 0.0,
                "avg_eval_seconds": round(mean(self._eval_timings), 4) if self._eval_timings else 0.0,
            }


metrics = RuntimeMetrics()


class timed_metric:
    def __init__(self, recorder):
        self._recorder = recorder
        self._started = 0.0

    def __enter__(self):
        self._started = perf_counter()
        return self

    def __exit__(self, exc_type, exc, tb):
        self._recorder(perf_counter() - self._started)
