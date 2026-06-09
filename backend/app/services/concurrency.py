from __future__ import annotations

from contextlib import contextmanager
from threading import Condition
from time import monotonic

from app.services.runtime_metrics import metrics
from app.utils.errors import bad_request


class DynamicLimiter:
    def __init__(self) -> None:
        self._condition = Condition()
        self._active = 0

    @contextmanager
    def acquire(self, limit: int, timeout_seconds: float):
        acquired = self._wait_for_slot(limit=max(1, limit), timeout_seconds=max(0.1, timeout_seconds))
        if not acquired:
            metrics.increment_rejected_retrievals()
            raise bad_request("VecSeek is currently handling too many retrieval requests. Please retry shortly.")
        metrics.increment_retrievals()
        try:
            yield
        finally:
            metrics.decrement_retrievals()
            with self._condition:
                self._active = max(0, self._active - 1)
                self._condition.notify()

    def _wait_for_slot(self, limit: int, timeout_seconds: float) -> bool:
        deadline = monotonic() + timeout_seconds
        with self._condition:
            while self._active >= limit:
                remaining = deadline - monotonic()
                if remaining <= 0:
                    return False
                self._condition.wait(timeout=remaining)
            self._active += 1
            return True


retrieval_limiter = DynamicLimiter()
