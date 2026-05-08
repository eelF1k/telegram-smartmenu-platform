from httpx import ASGITransport, AsyncClient

from api.app import app


async def test_webapp_menu_endpoint() -> None:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/webapp/menu")
    assert response.status_code == 200
    data = response.json()
    assert data["ok"] is True
    assert len(data["venues"]) >= 1


async def test_webapp_profile_endpoint() -> None:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/webapp/profile/42")
    assert response.status_code == 200
    assert response.json()["profile"]["user_id"] == 42
