from shared.delivery_policy import DeliveryPolicyEngine
from shared.queue_jobs import QueueJob


def make_job(kind: str, payload: dict) -> QueueJob:
    return QueueJob(
        job_id=1,
        kind=kind,
        payload=payload,
        status="pending",
        attempts=0,
        max_attempts=3,
        backoff_seconds=0,
        available_at=0,
        created_at="now",
        updated_at="now",
    )


def test_policy_high_priority_routes_to_telegram() -> None:
    engine = DeliveryPolicyEngine(rate_limit_per_minute=10)
    job = make_job("notify_order_status", {"priority": "high"})
    decision = engine.evaluate(job)
    assert decision.channel == "telegram"
    assert decision.priority == "high"
    assert decision.allowed is True


def test_policy_rate_limit_blocks_second_event() -> None:
    engine = DeliveryPolicyEngine(rate_limit_per_minute=1)
    job = make_job("notify_reservation_status", {"priority": "normal"})
    first = engine.evaluate(job)
    second = engine.evaluate(job)
    assert first.allowed is True
    assert second.allowed is False
    assert second.reason == "rate_limited"
