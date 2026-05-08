from shared.observability import now_perf, observe_delivery, observe_queue
from shared.outbox_store import AsyncOutboxStoreProtocol
from shared.queue_jobs import QueueJob
from shared.queue_protocol import QueueStoreProtocol

SUPPORTED_JOB_KINDS = {
    "notify_order_created",
    "notify_order_status",
    "notify_reservation_status",
}


def _dedupe_key(job: QueueJob) -> str:
    external_id = (
        job.payload.get("order_id")
        or job.payload.get("reservation_id")
        or job.payload.get("user_id")
        or "unknown"
    )
    return f"{job.kind}:{external_id}"


def _pick_channel(job: QueueJob) -> str:
    if job.kind == "notify_order_created":
        return "telegram"
    if job.kind == "notify_order_status":
        return "webhook"
    if job.kind == "notify_reservation_status":
        return "email"
    return "telegram"


async def process_next_job(
    queue: QueueStoreProtocol,
    *,
    outbox: AsyncOutboxStoreProtocol | None = None,
    delivery_adapters: dict | None = None,
) -> tuple[bool, QueueJob | None]:
    started = now_perf()
    job = queue.claim_next()
    if not job:
        return False, None

    if job.kind not in SUPPORTED_JOB_KINDS:
        queue.fail(job.job_id)
        observe_queue(job.kind, "failed", now_perf() - started)
        return True, job

    if outbox and delivery_adapters:
        dedupe_key = _dedupe_key(job)
        if await outbox.exists(dedupe_key):
            queue.complete(job.job_id)
            observe_queue(job.kind, "done", now_perf() - started)
            return True, job
        channel = _pick_channel(job)
        adapter = delivery_adapters.get(channel)
        delivery_started = now_perf()
        delivered = bool(adapter and await adapter.send(job.payload))
        observe_delivery(channel, delivered, now_perf() - delivery_started)
        await outbox.save(
            dedupe_key=dedupe_key,
            channel=channel,
            payload=job.payload,
            delivered=delivered,
        )
        if delivered:
            queue.complete(job.job_id)
            observe_queue(job.kind, "done", now_perf() - started)
        else:
            queue.fail(job.job_id)
            observe_queue(job.kind, "failed", now_perf() - started)
        return True, job

    queue.fail(job.job_id)
    observe_queue(job.kind, "failed", now_perf() - started)
    return True, job
