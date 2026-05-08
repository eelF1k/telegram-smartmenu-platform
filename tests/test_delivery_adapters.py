from shared.delivery_adapters import build_delivery_adapters


async def test_delivery_adapters_registry() -> None:
    adapters = build_delivery_adapters()
    assert {"telegram", "email", "webhook"} <= set(adapters.keys())
    assert await adapters["telegram"].send({"x": 1}) is True
    assert await adapters["email"].send({"x": 1}) is True
    assert await adapters["webhook"].send({"x": 1}) is True
