from httpx import ASGITransport, AsyncClient

from api.app import app


def _payload(text: str = "/start") -> dict:
    return {
        "update_id": 1,
        "message": {
            "message_id": 1,
            "text": text,
            "from": {"id": 1, "is_bot": False, "first_name": "Test"},
            "chat": {"id": 1, "type": "private"},
            "date": 1,
        },
    }


async def test_webhook_rejects_invalid_secret_path() -> None:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post("/telegram/webhook/wrong-secret", json=_payload())
    assert response.status_code == 401


async def test_webhook_rejects_invalid_secret_header() -> None:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            "/telegram/webhook/dev-webhook-secret",
            json=_payload(),
            headers={"X-Telegram-Bot-Api-Secret-Token": "invalid"},
        )
    assert response.status_code == 401
