from time import perf_counter
from uuid import uuid4

from prometheus_client import CONTENT_TYPE_LATEST, Counter, Histogram, generate_latest

QUEUE_PROCESS_TOTAL = Counter(
    "smartmenu_queue_process_total",
    "Total processed queue jobs by result",
    labelnames=("kind", "status"),
)
QUEUE_PROCESS_DURATION_SECONDS = Histogram(
    "smartmenu_queue_process_duration_seconds",
    "Queue job processing duration in seconds",
    labelnames=("kind", "status"),
)
DELIVERY_TOTAL = Counter(
    "smartmenu_delivery_total",
    "Total delivery attempts by channel and result",
    labelnames=("channel", "result"),
)
DELIVERY_DURATION_SECONDS = Histogram(
    "smartmenu_delivery_duration_seconds",
    "Delivery adapter call duration in seconds",
    labelnames=("channel", "result"),
)


def new_trace_id() -> str:
    return uuid4().hex


def now_perf() -> float:
    return perf_counter()


def observe_queue(kind: str, status: str, duration_seconds: float) -> None:
    QUEUE_PROCESS_TOTAL.labels(kind=kind, status=status).inc()
    QUEUE_PROCESS_DURATION_SECONDS.labels(kind=kind, status=status).observe(duration_seconds)


def observe_delivery(channel: str, success: bool, duration_seconds: float) -> None:
    result = "success" if success else "failed"
    DELIVERY_TOTAL.labels(channel=channel, result=result).inc()
    DELIVERY_DURATION_SECONDS.labels(channel=channel, result=result).observe(duration_seconds)


def export_metrics() -> tuple[bytes, str]:
    return generate_latest(), CONTENT_TYPE_LATEST
