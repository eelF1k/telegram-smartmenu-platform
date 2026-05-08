import json
from time import time

from redis import Redis

from shared.queue_jobs import QueueJob


class RedisJobQueue:
    def __init__(self, redis_url: str, prefix: str = "smartmenu:queue") -> None:
        self._redis = Redis.from_url(redis_url, decode_responses=True)
        self._prefix = prefix

    def ping(self) -> bool:
        return bool(self._redis.ping())

    def _next_id_key(self) -> str:
        return f"{self._prefix}:next_id"

    def _pending_key(self) -> str:
        return f"{self._prefix}:pending"

    def _all_jobs_key(self) -> str:
        return f"{self._prefix}:all"

    def _job_key(self, job_id: int) -> str:
        return f"{self._prefix}:job:{job_id}"

    @staticmethod
    def _from_hash(raw: dict[str, str]) -> QueueJob:
        return QueueJob(
            job_id=int(raw["job_id"]),
            kind=raw["kind"],
            payload=json.loads(raw["payload"]),
            status=raw["status"],
            attempts=int(raw["attempts"]),
            max_attempts=int(raw["max_attempts"]),
            backoff_seconds=float(raw["backoff_seconds"]),
            available_at=float(raw["available_at"]),
            created_at=raw["created_at"],
            updated_at=raw["updated_at"],
        )

    def _save_job(self, job: QueueJob) -> None:
        self._redis.hset(
            self._job_key(job.job_id),
            mapping={
                "job_id": str(job.job_id),
                "kind": job.kind,
                "payload": json.dumps(job.payload),
                "status": job.status,
                "attempts": str(job.attempts),
                "max_attempts": str(job.max_attempts),
                "backoff_seconds": str(job.backoff_seconds),
                "available_at": str(job.available_at),
                "created_at": job.created_at,
                "updated_at": job.updated_at,
            },
        )
        self._redis.sadd(self._all_jobs_key(), str(job.job_id))

    def _load_job(self, job_id: int) -> QueueJob | None:
        raw = self._redis.hgetall(self._job_key(job_id))
        if not raw:
            return None
        return self._from_hash(raw)

    def enqueue(
        self,
        kind: str,
        payload: dict,
        *,
        max_attempts: int = 3,
        backoff_seconds: float = 1.0,
    ) -> QueueJob:
        from datetime import UTC, datetime

        now = datetime.now(tz=UTC).isoformat()
        job_id = int(self._redis.incr(self._next_id_key()))
        job = QueueJob(
            job_id=job_id,
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
        self._save_job(job)
        self._redis.zadd(self._pending_key(), {str(job_id): job.available_at})
        return job

    def list_jobs(self, status: str | None = None) -> list[QueueJob]:
        raw_ids = self._redis.smembers(self._all_jobs_key())
        ids = sorted(int(item) for item in raw_ids)
        jobs: list[QueueJob] = []
        for job_id in ids:
            job = self._load_job(job_id)
            if not job:
                continue
            if status is None or job.status == status:
                jobs.append(job)
        return jobs

    def claim_next(self) -> QueueJob | None:
        now_ts = time()
        ids = self._redis.zrangebyscore(self._pending_key(), min="-inf", max=now_ts, start=0, num=1)
        if not ids:
            return None
        job_id = int(ids[0])
        self._redis.zrem(self._pending_key(), str(job_id))
        job = self._load_job(job_id)
        if not job:
            return None
        job.status = "processing"
        job.attempts += 1
        from datetime import UTC, datetime

        job.updated_at = datetime.now(tz=UTC).isoformat()
        self._save_job(job)
        return job

    def complete(self, job_id: int) -> QueueJob | None:
        job = self._load_job(job_id)
        if not job:
            return None
        from datetime import UTC, datetime

        job.status = "done"
        job.updated_at = datetime.now(tz=UTC).isoformat()
        self._save_job(job)
        return job

    def fail(self, job_id: int) -> QueueJob | None:
        job = self._load_job(job_id)
        if not job:
            return None
        from datetime import UTC, datetime

        if job.attempts >= job.max_attempts:
            job.status = "dead_letter"
        else:
            job.status = "pending"
            delay = job.backoff_seconds * (2 ** max(job.attempts - 1, 0))
            job.available_at = time() + delay
            self._redis.zadd(self._pending_key(), {str(job_id): job.available_at})
        job.updated_at = datetime.now(tz=UTC).isoformat()
        self._save_job(job)
        return job
