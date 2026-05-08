import asyncio
import logging

from shared.queue_jobs import job_queue

logger = logging.getLogger(__name__)


async def run_worker(poll_interval_seconds: float = 1.0) -> None:
    while True:
        job = job_queue.claim_next()
        if not job:
            await asyncio.sleep(poll_interval_seconds)
            continue
        if job.kind in {"notify_order_created", "notify_order_status", "notify_reservation_status"}:
            job_queue.complete(job.job_id)
            logger.info("queue_job_done", extra={"job_id": job.job_id, "kind": job.kind})
        else:
            job_queue.fail(job.job_id)
            logger.warning("queue_job_failed", extra={"job_id": job.job_id, "kind": job.kind})


if __name__ == "__main__":
    asyncio.run(run_worker())
