import asyncio
import logging

from bot.config import BotSettings
from shared.delivery_adapters import build_delivery_adapters
from shared.notification_outbox import notification_outbox
from shared.queue_factory import build_queue_store
from shared.queue_processor import process_next_job

logger = logging.getLogger(__name__)
settings = BotSettings()
queue_store = build_queue_store(
    settings.queue_backend,
    redis_url=settings.redis_url,
    redis_prefix=settings.queue_redis_prefix,
)
delivery_adapters = build_delivery_adapters()


async def run_worker(poll_interval_seconds: float = 1.0) -> None:
    while True:
        processed, job = process_next_job(
            queue_store,
            outbox=notification_outbox,
            delivery_adapters=delivery_adapters,
        )
        if not processed or not job:
            await asyncio.sleep(poll_interval_seconds)
            continue
        status = next(item.status for item in queue_store.list_jobs() if item.job_id == job.job_id)
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
