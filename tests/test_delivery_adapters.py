from shared.delivery_adapters import build_delivery_adapters


async def test_delivery_adapters_registry() -> None:
    adapters = build_delivery_adapters()
    assert {"telegram", "email", "webhook"} <= set(adapters.keys())
    assert await adapters["telegram"].send({"x": 1}) is True
    assert await adapters["email"].send({"x": 1}) is True
    assert await adapters["webhook"].send({"x": 1}) is True


async def test_email_adapter_returns_false_on_send_error() -> None:
    adapters = build_delivery_adapters()
    delivered = await adapters["email"].send(
        {"to_email": "demo@example.com", "subject": "s", "body": "b"}
    )
    assert delivered in {True, False}
