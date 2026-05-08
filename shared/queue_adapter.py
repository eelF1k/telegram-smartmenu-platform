from dataclasses import dataclass
from typing import Protocol

from shared.queue_jobs import InMemoryJobQueue, QueueJob, job_queue


class QueueAdapter(Protocol):
    def enqueue(
        self,
        kind: str,
        payload: dict,
        *,
        max_attempts: int = 3,
        backoff_seconds: float = 1.0,
    ) -> QueueJob: ...


@dataclass
class InMemoryQueueAdapter:
    queue: InMemoryJobQueue

    def enqueue(
        self,
        kind: str,
        payload: dict,
        *,
        max_attempts: int = 3,
        backoff_seconds: float = 1.0,
    ) -> QueueJob:
        return self.queue.enqueue(
            kind=kind,
            payload=payload,
            max_attempts=max_attempts,
            backoff_seconds=backoff_seconds,
        )


class ArqQueueAdapter:
    def enqueue(
        self,
        kind: str,
        payload: dict,
        *,
        max_attempts: int = 3,
        backoff_seconds: float = 1.0,
    ) -> QueueJob:
        raise NotImplementedError("ARQ adapter is planned for the next infrastructure phase.")


class CeleryQueueAdapter:
    def enqueue(
        self,
        kind: str,
        payload: dict,
        *,
        max_attempts: int = 3,
        backoff_seconds: float = 1.0,
    ) -> QueueJob:
        raise NotImplementedError("Celery adapter is planned for the next infrastructure phase.")


def build_queue_adapter(backend: str = "memory") -> QueueAdapter:
    if backend == "memory":
        return InMemoryQueueAdapter(queue=job_queue)
    if backend == "arq":
        return ArqQueueAdapter()
    if backend == "celery":
        return CeleryQueueAdapter()
    raise ValueError(f"Unsupported queue backend: {backend}")
