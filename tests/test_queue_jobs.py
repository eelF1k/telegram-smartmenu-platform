from httpx import ASGITransport, AsyncClient

from api.app import app


async def test_queue_enqueue_list_and_process() -> None:
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
