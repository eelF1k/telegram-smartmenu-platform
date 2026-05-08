from httpx import ASGITransport, AsyncClient

from api.app import app
from shared.queue_jobs import job_queue


async def test_queue_enqueue_list_and_process() -> None:
    job_queue.reset()
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
    job_queue.reset()
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
    job_queue.reset()
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
