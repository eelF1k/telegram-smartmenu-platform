from httpx import ASGITransport, AsyncClient

from api.app import app, policy_engine, queue_store
from shared.outbox_store import outbox_store


async def test_queue_enqueue_list_and_process() -> None:
    if hasattr(queue_store, "reset"):
        queue_store.reset()
    if hasattr(outbox_store, "reset"):
        outbox_store.reset()
    policy_engine._events.clear()
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        enqueue_response = await client.post(
            "/queue/enqueue",
            json={"kind": "notify_order_status", "payload": {"user_id": 1, "order_id": 10}},
        )
        list_response = await client.get("/queue/jobs")
        process_response = await client.post("/queue/process-next")
        list_done_response = await client.get("/queue/jobs", params={"status": "done"})

    assert enqueue_response.status_code == 200
    assert list_response.status_code == 200
    assert process_response.status_code == 200
    assert process_response.json()["processed"] is True
    assert list_done_response.status_code == 200
    assert len(list_done_response.json()["jobs"]) >= 1


async def test_order_status_update_enqueues_notification_job() -> None:
    if hasattr(queue_store, "reset"):
        queue_store.reset()
    if hasattr(outbox_store, "reset"):
        outbox_store.reset()
    policy_engine._events.clear()
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        await client.post("/webapp/confirm", json={"user_id": 7, "total": 15000})
        # create a real order id from admin endpoint list
        orders = await client.get("/admin/orders")
        last_order_id = orders.json()["orders"][-1]["order_id"]
        update_response = await client.post(
            f"/admin/orders/{last_order_id}/status",
            json={"status": "preparing"},
        )
        pending_jobs = await client.get("/queue/jobs", params={"status": "pending"})

    assert update_response.status_code == 200
    assert pending_jobs.status_code == 200
    assert any(job["kind"] == "notify_order_status" for job in pending_jobs.json()["jobs"])


async def test_queue_retry_and_dead_letter_flow() -> None:
    if hasattr(queue_store, "reset"):
        queue_store.reset()
    if hasattr(outbox_store, "reset"):
        outbox_store.reset()
    policy_engine._events.clear()
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        enqueue_response = await client.post(
            "/queue/enqueue",
            json={
                "kind": "unknown_kind",
                "payload": {"x": 1},
                "max_attempts": 2,
                "backoff_seconds": 0,
            },
        )
        first_process = await client.post("/queue/process-next")
        pending_after_first = await client.get("/queue/jobs", params={"status": "pending"})
        second_process = await client.post("/queue/process-next")
        dead_letter = await client.get("/queue/jobs", params={"status": "dead_letter"})

    assert enqueue_response.status_code == 200
    assert first_process.status_code == 200
    assert first_process.json()["status"] == "pending"
    assert pending_after_first.status_code == 200
    assert len(pending_after_first.json()["jobs"]) >= 1
    assert second_process.status_code == 200
    assert second_process.json()["status"] == "dead_letter"
    assert dead_letter.status_code == 200
    assert any(job["kind"] == "unknown_kind" for job in dead_letter.json()["jobs"])


async def test_notification_outbox_is_idempotent_on_duplicate_processing() -> None:
    if hasattr(queue_store, "reset"):
        queue_store.reset()
    if hasattr(outbox_store, "reset"):
        outbox_store.reset()
    policy_engine._events.clear()
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        await client.post(
            "/queue/enqueue",
            json={"kind": "notify_order_status", "payload": {"order_id": 555, "user_id": 1}},
        )
        await client.post(
            "/queue/enqueue",
            json={"kind": "notify_order_status", "payload": {"order_id": 555, "user_id": 1}},
        )
        first = await client.post("/queue/process-next")
        second = await client.post("/queue/process-next")
        outbox = await client.get("/queue/outbox")

    assert first.status_code == 200
    assert second.status_code == 200
    assert first.json()["status"] == "done"
    assert second.json()["status"] == "done"
    assert outbox.status_code == 200
    assert len(outbox.json()["records"]) == 1


async def test_metrics_endpoint_exposes_queue_metrics() -> None:
    if hasattr(queue_store, "reset"):
        queue_store.reset()
    if hasattr(outbox_store, "reset"):
        outbox_store.reset()
    policy_engine._events.clear()
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        await client.post(
            "/queue/enqueue",
            json={"kind": "notify_order_status", "payload": {"order_id": 900, "user_id": 10}},
        )
        await client.post("/queue/process-next")
        metrics = await client.get("/metrics")

    assert metrics.status_code == 200
    assert "smartmenu_queue_process_total" in metrics.text


async def test_queue_rate_limit_creates_throttled_status() -> None:
    if hasattr(queue_store, "reset"):
        queue_store.reset()
    if hasattr(outbox_store, "reset"):
        outbox_store.reset()
    policy_engine._events.clear()
    policy_engine._rate_limit_per_minute = 1
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        await client.post(
            "/queue/enqueue",
            json={"kind": "notify_order_created", "payload": {"user_id": 10}},
        )
        await client.post(
            "/queue/enqueue",
            json={"kind": "notify_order_created", "payload": {"user_id": 11}},
        )
        first = await client.post("/queue/process-next")
        second = await client.post("/queue/process-next")
    policy_engine._rate_limit_per_minute = 60
    assert first.status_code == 200
    assert second.status_code == 200
    assert first.json()["status"] in {"done", "pending"}
    assert second.json()["status"] in {"pending", "dead_letter"}


async def test_queue_venue_override_changes_channel() -> None:
    if hasattr(queue_store, "reset"):
        queue_store.reset()
    if hasattr(outbox_store, "reset"):
        outbox_store.reset()
    policy_engine._events.clear()
    policy_engine.set_venue_override("venue-test", channel="email", priority="low")
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        await client.post(
            "/queue/enqueue",
            json={
                "kind": "notify_order_created",
                "payload": {"user_id": 33, "venue_id": "venue-test"},
            },
        )
        await client.post("/queue/process-next")
        outbox = await client.get("/queue/outbox")

    assert outbox.status_code == 200
    assert any(record["channel"] == "email" for record in outbox.json()["records"])
