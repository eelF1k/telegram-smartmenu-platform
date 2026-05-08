from dataclasses import dataclass
from datetime import UTC, datetime
from time import time


@dataclass
class QueueJob:
    job_id: int
    kind: str
    payload: dict
    status: str
    attempts: int
    max_attempts: int
    backoff_seconds: float
    available_at: float
    created_at: str
    updated_at: str


class InMemoryJobQueue:
    def __init__(self) -> None:
        self._jobs: list[QueueJob] = []
        self._next_job_id = 1

    def reset(self) -> None:
        self._jobs.clear()
        self._next_job_id = 1

    @staticmethod
    def _now() -> str:
        return datetime.now(tz=UTC).isoformat()

    def enqueue(
        self,
        kind: str,
        payload: dict,
        *,
        max_attempts: int = 3,
        backoff_seconds: float = 1.0,
    ) -> QueueJob:
        now = self._now()
        job = QueueJob(
            job_id=self._next_job_id,
            kind=kind,
            payload=payload,
            status="pending",
            attempts=0,
            max_attempts=max_attempts,
            backoff_seconds=backoff_seconds,
            available_at=time(),
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
        now_ts = time()
        for job in self._jobs:
            if job.status == "pending" and job.available_at <= now_ts:
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
                if job.attempts >= job.max_attempts:
                    job.status = "dead_letter"
                else:
                    job.status = "pending"
                    delay = job.backoff_seconds * (2 ** max(job.attempts - 1, 0))
                    job.available_at = time() + delay
                job.updated_at = self._now()
                return job
        return None


job_queue = InMemoryJobQueue()
