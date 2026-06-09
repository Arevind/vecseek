from __future__ import annotations

from collections import deque
from threading import Lock, Thread
from time import sleep

from app.database import SessionLocal
from app.models import Folder
from app.services.indexing_service import index_folder
from app.services.runtime_metrics import metrics


class IndexQueueManager:
    def __init__(self) -> None:
        self._lock = Lock()
        self._pending: deque[str] = deque()
        self._queued: set[str] = set()
        self._active = 0
        self._started = False

    def start(self) -> None:
        with self._lock:
            if self._started:
                return
            self._started = True
        Thread(target=self._dispatch_loop, daemon=True, name="vecseek-index-dispatcher").start()

    def enqueue(self, folder_id: str) -> None:
        with self._lock:
            if folder_id in self._queued:
                return
            self._pending.append(folder_id)
            self._queued.add(folder_id)
            metrics.set_queue_depth(len(self._pending))

    def _dispatch_loop(self) -> None:
        while True:
            folder_id = None
            with self._lock:
                if self._pending:
                    db = SessionLocal()
                    try:
                        from app.models import Setting

                        setting = db.get(Setting, 1)
                        max_concurrency = int(setting.indexing_worker_concurrency if setting else 2)
                    finally:
                        db.close()
                    if self._active < max(1, max_concurrency):
                        folder_id = self._pending.popleft()
                        self._active += 1
                        metrics.set_queue_depth(len(self._pending))
            if folder_id:
                Thread(target=self._run_job, args=(folder_id,), daemon=True).start()
            else:
                sleep(0.15)

    def _run_job(self, folder_id: str) -> None:
        metrics.increment_index_jobs()
        db = SessionLocal()
        try:
            folder = db.query(Folder).filter(Folder.id == folder_id).first()
            if folder:
                index_folder(db, folder)
        finally:
            db.close()
            metrics.decrement_index_jobs()
            with self._lock:
                self._active = max(0, self._active - 1)
                self._queued.discard(folder_id)


index_queue = IndexQueueManager()
