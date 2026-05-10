"""
Simple in-memory job store for long-running background tasks (e.g. book ingestion).
Jobs are ephemeral — they don't survive a server restart, which is fine for CLI-free UX.
"""

import threading
import uuid
from dataclasses import dataclass, field
from typing import Literal


@dataclass
class Job:
    id: str
    status: Literal["running", "done", "error"] = "running"
    messages: list[str] = field(default_factory=list)
    result: str | None = None  # vault-relative path to the book index note
    error: str | None = None


_jobs: dict[str, Job] = {}
_lock = threading.Lock()


def create() -> Job:
    job = Job(id=str(uuid.uuid4()))
    with _lock:
        _jobs[job.id] = job
    return job


def get(job_id: str) -> Job | None:
    with _lock:
        return _jobs.get(job_id)
