from __future__ import annotations

from collections import deque
from threading import Lock, Thread
from time import sleep

from app.database import SessionLocal
from app.models import EvalRun
from app.services.eval_service import run_eval_job_sync
from app.services.runtime_metrics import metrics


class EvalQueueManager:
    def __init__(self) -> None:
        self._lock = Lock()
        self._pending: deque[tuple[str, str | None]] = deque()
        self._queued: set[str] = set()
        self._active = 0
        self._started = False

    def start(self) -> None:
        with self._lock:
            if self._started:
                return
            self._started = True
        Thread(target=self._dispatch_loop, daemon=True, name="vecseek-eval-dispatcher").start()

    def enqueue(self, run_id: str, openai_api_key: str | None = None) -> None:
        with self._lock:
            if run_id in self._queued:
                return
            self._pending.append((run_id, openai_api_key))
            self._queued.add(run_id)
            metrics.set_queue_depth(len(self._pending))

    def _dispatch_loop(self) -> None:
        while True:
            payload = None
            with self._lock:
                if self._pending:
                    db = SessionLocal()
                    try:
                        from app.config import get_settings

                        max_concurrency = int(get_settings().eval_concurrency_limit)
                    finally:
                        db.close()
                    if self._active < max(1, max_concurrency):
                        payload = self._pending.popleft()
                        self._active += 1
                        metrics.set_queue_depth(len(self._pending))
            if payload:
                Thread(target=self._run_job, args=payload, daemon=True).start()
            else:
                sleep(0.15)

    def _run_job(self, run_id: str, openai_api_key: str | None) -> None:
        metrics.increment_eval_jobs()
        db = SessionLocal()
        try:
            run = db.query(EvalRun).filter(EvalRun.id == run_id).first()
            if run:
                run_eval_job_sync(db, run_id, openai_api_key=openai_api_key)
        finally:
            db.close()
            metrics.decrement_eval_jobs()
            with self._lock:
                self._active = max(0, self._active - 1)
                self._queued.discard(run_id)


eval_queue = EvalQueueManager()
