from shared.queue_jobs import InMemoryJobQueue
from shared.queue_protocol import QueueStoreProtocol
from shared.redis_queue import RedisJobQueue


def build_queue_store(
    backend: str,
    *,
    redis_url: str,
    redis_prefix: str,
) -> QueueStoreProtocol:
    if backend == "memory":
        return InMemoryJobQueue()
    if backend == "redis":
        try:
            queue = RedisJobQueue(redis_url=redis_url, prefix=redis_prefix)
            queue.ping()
            return queue
        except Exception:
            return InMemoryJobQueue()
    raise ValueError(f"Unsupported queue backend: {backend}")
