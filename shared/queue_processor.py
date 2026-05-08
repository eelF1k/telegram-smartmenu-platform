from shared.queue_jobs import InMemoryJobQueue, QueueJob

SUPPORTED_JOB_KINDS = {
    "notify_order_created",
    "notify_order_status",
    "notify_reservation_status",
}


def process_next_job(queue: InMemoryJobQueue) -> tuple[bool, QueueJob | None]:
    job = queue.claim_next()
    if not job:
        return False, None
    if job.kind in SUPPORTED_JOB_KINDS:
        queue.complete(job.job_id)
        return True, job
    queue.fail(job.job_id)
    return True, job
