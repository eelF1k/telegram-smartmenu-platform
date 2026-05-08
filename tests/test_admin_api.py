from httpx import ASGITransport, AsyncClient

from api.app import app
from shared.admin_store import admin_store


async def test_admin_reservations_status_update() -> None:
    created = admin_store.create_reservation(
        user_id=1,
        venue="Vinson Git",
        datetime_text="2026-06-01 19:00",
    )
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        list_response = await client.get("/admin/reservations")
        update_response = await client.post(
            f"/admin/reservations/{created.reservation_id}/status",
            json={"status": "accepted"},
        )
    assert list_response.status_code == 200
    assert update_response.status_code == 200
    assert update_response.json()["reservation"]["status"] == "accepted"


async def test_admin_orders_status_update() -> None:
    created = admin_store.create_order(user_id=2, total=25000)
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        list_response = await client.get("/admin/orders")
        update_response = await client.post(
            f"/admin/orders/{created.order_id}/status",
            json={"status": "completed"},
        )
    assert list_response.status_code == 200
    assert update_response.status_code == 200
    assert update_response.json()["order"]["status"] == "completed"
