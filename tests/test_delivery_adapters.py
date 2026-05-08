from shared.delivery_adapters import build_delivery_adapters


def test_delivery_adapters_registry() -> None:
    adapters = build_delivery_adapters()
    assert {"telegram", "email", "webhook"} <= set(adapters.keys())
    assert adapters["telegram"].send({"x": 1}) is True
    assert adapters["email"].send({"x": 1}) is True
    assert adapters["webhook"].send({"x": 1}) is True
