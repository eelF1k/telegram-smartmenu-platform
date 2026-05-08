from dataclasses import dataclass
from datetime import UTC, datetime


@dataclass
class QueueJob:
    job_id: int
    kind: str
    payload: dict
    status: str
    attempts: int
    created_at: str
    updated_at: str


class InMemoryJobQueue:
    def __init__(self) -> None:
        self._jobs: list[QueueJob] = []
        self._next_job_id = 1

    @staticmethod
    def _now() -> str:
        return datetime.now(tz=UTC).isoformat()

    def enqueue(self, kind: str, payload: dict) -> QueueJob:
        now = self._now()
        job = QueueJob(
            job_id=self._next_job_id,
            kind=kind,
            payload=payload,
            status="pending",
            attempts=0,
            created_at=now,
            updated_at=now,
        )
        self._next_job_id += 1
        self._jobs.append(job)
        return job

    def list_jobs(self, status: str | None = None) -> list[QueueJob]:
        if status is None:
            return self._jobs
        return [job for job in self._jobs if job.status == status]

    def claim_next(self) -> QueueJob | None:
        for job in self._jobs:
            if job.status == "pending":
                job.status = "processing"
                job.attempts += 1
                job.updated_at = self._now()
                return job
        return None

    def complete(self, job_id: int) -> QueueJob | None:
        for job in self._jobs:
            if job.job_id == job_id:
                job.status = "done"
                job.updated_at = self._now()
                return job
        return None

    def fail(self, job_id: int) -> QueueJob | None:
        for job in self._jobs:
            if job.job_id == job_id:
                job.status = "failed"
                job.updated_at = self._now()
                return job
        return None


job_queue = InMemoryJobQueue()
