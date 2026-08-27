"""In-process background crawl jobs.

One crawl == one asyncio Task running on the FastAPI event loop. State is
held in memory; terminal results are also persisted to SQLite via
``persist_crawl_result``. No external queue, broker, or worker process.

Job lifecycle:

    starting -> crawling -> completed
                         -> failed
                         -> cancelled
"""

from __future__ import annotations

import asyncio
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone

from app.crawler.orchestrator import crawl_company
from app.storage import persist_crawl_result

JobStatus = str  # "starting" | "crawling" | "completed" | "failed" | "cancelled"

_MAX_RETAINED_JOBS = 100


def _now() -> datetime:
    return datetime.now(timezone.utc)


@dataclass
class Job:
    id: str
    website: str
    max_pages: int
    status: JobStatus = "starting"
    phase: str = "queued"
    pages_done: int = 0
    pages_total: int = 0
    created_at: datetime = field(default_factory=_now)
    started_at: datetime | None = None
    finished_at: datetime | None = None
    error: str | None = None
    result: dict | None = None
    task: asyncio.Task | None = field(default=None, repr=False)

    def to_public(self, *, include_result: bool = False) -> dict:
        data = {
            "id": self.id,
            "website": self.website,
            "max_pages": self.max_pages,
            "status": self.status,
            "progress": {
                "phase": self.phase,
                "pages_done": self.pages_done,
                "pages_total": self.pages_total,
            },
            "created_at": self.created_at.isoformat(),
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "finished_at": (
                self.finished_at.isoformat() if self.finished_at else None
            ),
            "error": self.error,
        }
        if include_result:
            data["result"] = self.result
        return data


class JobManager:
    def __init__(self) -> None:
        self._jobs: dict[str, Job] = {}
        self._order: list[str] = []

    def create(self, website: str, max_pages: int) -> Job:
        job = Job(id=str(uuid.uuid4()), website=website, max_pages=max_pages)
        self._jobs[job.id] = job
        self._order.append(job.id)
        self._evict()
        job.task = asyncio.create_task(self._run(job))
        return job

    def get(self, job_id: str) -> Job | None:
        return self._jobs.get(job_id)

    def list(self) -> list[Job]:
        return [self._jobs[jid] for jid in reversed(self._order) if jid in self._jobs]

    def cancel(self, job_id: str) -> bool:
        job = self._jobs.get(job_id)
        if job is None or job.status in ("completed", "failed", "cancelled"):
            return False
        if job.task is not None:
            job.task.cancel()
        return True

    async def shutdown(self) -> None:
        tasks = [j.task for j in self._jobs.values() if j.task and not j.task.done()]
        for task in tasks:
            task.cancel()
        for task in tasks:
            try:
                await task
            except (asyncio.CancelledError, Exception):
                pass

    def _evict(self) -> None:
        while len(self._order) > _MAX_RETAINED_JOBS:
            oldest = self._order.pop(0)
            job = self._jobs.get(oldest)
            if job and job.status in ("starting", "crawling"):
                # Never drop a running job; keep it and trim the next oldest.
                self._order.append(oldest)
                continue
            self._jobs.pop(oldest, None)

    async def _run(self, job: Job) -> None:
        loop = asyncio.get_running_loop()
        job.status = "crawling"
        job.started_at = _now()

        def on_progress(phase: str, done: int, total: int) -> None:
            # Called from the crawl coroutine (same loop) - safe to mutate.
            job.phase = phase
            job.pages_done = done
            job.pages_total = total

        try:
            response = await crawl_company(
                job.website, job.max_pages, on_progress=on_progress
            )
            job.result = response.model_dump(mode="json")
            job.status = "completed"
            job.phase = "done"
            await loop.run_in_executor(None, persist_crawl_result, response)
        except asyncio.CancelledError:
            job.status = "cancelled"
            job.phase = "cancelled"
            raise
        except Exception as exc:  # noqa: BLE001 - surfaced to the client
            job.status = "failed"
            job.phase = "error"
            job.error = f"{type(exc).__name__}: {exc}"
        finally:
            job.finished_at = _now()


manager = JobManager()
