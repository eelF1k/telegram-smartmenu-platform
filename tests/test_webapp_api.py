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


async def test_webapp_recommendations_endpoint() -> None:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/webapp/recommendations/42", params={"q": "гостре"})
    assert response.status_code == 200
    data = response.json()
    assert data["ok"] is True
    assert len(data["items"]) >= 1
    assert "dish_name" in data["items"][0]


async def test_webapp_recommendations_stream_endpoint() -> None:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get(
            "/webapp/recommendations-stream",
            params={"user_id": 42, "q": "сир"},
        )
    assert response.status_code == 200
    assert "text/event-stream" in response.headers["content-type"]
    assert "data:" in response.text
