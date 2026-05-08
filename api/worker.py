import asyncio
import logging

from shared.queue_jobs import job_queue
from shared.queue_processor import process_next_job

logger = logging.getLogger(__name__)


async def run_worker(poll_interval_seconds: float = 1.0) -> None:
    while True:
        processed, job = process_next_job(job_queue)
        if not processed or not job:
            await asyncio.sleep(poll_interval_seconds)
            continue
        status = next(item.status for item in job_queue.list_jobs() if item.job_id == job.job_id)
        if status == "done":
            logger.info("queue_job_done", extra={"job_id": job.job_id, "kind": job.kind})
        elif status == "dead_letter":
            logger.warning("queue_job_dead_letter", extra={"job_id": job.job_id, "kind": job.kind})
        else:
            logger.warning(
                "queue_job_retry_scheduled",
                extra={"job_id": job.job_id, "kind": job.kind},
            )


if __name__ == "__main__":
    asyncio.run(run_worker())
