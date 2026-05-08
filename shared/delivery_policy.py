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
        self._tenant_rates: dict[str, int] = {}
        self._venue_overrides: dict[str, dict[str, str]] = {}

    def set_tenant_rate_limit(self, tenant_id: str, limit_per_minute: int) -> None:
        self._tenant_rates[tenant_id] = max(1, limit_per_minute)

    def clear_rules(self) -> None:
        self._tenant_rates = {}
        self._venue_overrides = {}

    def set_venue_override(
        self,
        venue_id: str,
        *,
        channel: str | None = None,
        priority: str | None = None,
    ) -> None:
        overrides: dict[str, str] = {}
        if channel:
            overrides["channel"] = channel
        if priority:
            overrides["priority"] = priority
        self._venue_overrides[venue_id] = overrides

    def _resolve_priority(self, job: QueueJob) -> str:
        value = str(job.payload.get("priority", "normal")).lower()
        venue_id = str(job.payload.get("venue_id", ""))
        venue_override = self._venue_overrides.get(venue_id, {})
        if "priority" in venue_override:
            value = venue_override["priority"]
        if value in {"high", "normal", "low"}:
            return value
        return "normal"

    def _resolve_channel(self, job: QueueJob, priority: str) -> str:
        venue_id = str(job.payload.get("venue_id", ""))
        venue_override = self._venue_overrides.get(venue_id, {})
        if "channel" in venue_override:
            return venue_override["channel"]
        if priority == "high":
            return "telegram"
        if job.kind == "notify_order_created":
            return "telegram"
        if job.kind == "notify_order_status":
            return "webhook"
        if job.kind == "notify_reservation_status":
            return "email"
        return "telegram"

    def _allow(self, channel: str, tenant_id: str) -> bool:
        now = time()
        cutoff = now - 60
        bucket_key = f"{tenant_id}:{channel}"
        bucket = self._events[bucket_key]
        while bucket and bucket[0] < cutoff:
            bucket.popleft()
        limit = self._tenant_rates.get(tenant_id, self._rate_limit_per_minute)
        if len(bucket) >= limit:
            return False
        bucket.append(now)
        return True

    def evaluate(self, job: QueueJob) -> DeliveryDecision:
        tenant_id = str(job.payload.get("tenant_id", "default"))
        priority = self._resolve_priority(job)
        channel = self._resolve_channel(job, priority)
        allowed = self._allow(channel, tenant_id=tenant_id)
        reason = "ok" if allowed else "rate_limited"
        return DeliveryDecision(
            channel=channel,
            priority=priority,
            allowed=allowed,
            reason=reason,
        )
