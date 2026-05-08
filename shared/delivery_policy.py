from collections import defaultdict, deque
from dataclasses import dataclass
from time import time

from shared.queue_jobs import QueueJob


@dataclass
class DeliveryDecision:
    channel: str
    priority: str
    allowed: bool
    reason: str


class DeliveryPolicyEngine:
    def __init__(self, rate_limit_per_minute: int = 60) -> None:
        self._rate_limit_per_minute = rate_limit_per_minute
        self._events: dict[str, deque[float]] = defaultdict(deque)

    def _resolve_priority(self, job: QueueJob) -> str:
        value = str(job.payload.get("priority", "normal")).lower()
        if value in {"high", "normal", "low"}:
            return value
        return "normal"

    def _resolve_channel(self, job: QueueJob, priority: str) -> str:
        if priority == "high":
            return "telegram"
        if job.kind == "notify_order_created":
            return "telegram"
        if job.kind == "notify_order_status":
            return "webhook"
        if job.kind == "notify_reservation_status":
            return "email"
        return "telegram"

    def _allow(self, channel: str) -> bool:
        now = time()
        cutoff = now - 60
        bucket = self._events[channel]
        while bucket and bucket[0] < cutoff:
            bucket.popleft()
        if len(bucket) >= self._rate_limit_per_minute:
            return False
        bucket.append(now)
        return True

    def evaluate(self, job: QueueJob) -> DeliveryDecision:
        priority = self._resolve_priority(job)
        channel = self._resolve_channel(job, priority)
        allowed = self._allow(channel)
        reason = "ok" if allowed else "rate_limited"
        return DeliveryDecision(
            channel=channel,
            priority=priority,
            allowed=allowed,
            reason=reason,
        )
