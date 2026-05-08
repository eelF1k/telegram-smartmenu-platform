from typing import Protocol

from shared.queue_jobs import QueueJob


class QueueStoreProtocol(Protocol):
    def enqueue(
        self,
        kind: str,
        payload: dict,
        *,
        max_attempts: int = 3,
        backoff_seconds: float = 1.0,
    ) -> QueueJob: ...

    def list_jobs(self, status: str | None = None) -> list[QueueJob]: ...

    def claim_next(self) -> QueueJob | None: ...

    def complete(self, job_id: int) -> QueueJob | None: ...

    def fail(self, job_id: int) -> QueueJob | None: ...
