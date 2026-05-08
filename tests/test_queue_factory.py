import pytest

from shared.queue_factory import build_queue_store
from shared.queue_jobs import InMemoryJobQueue


def test_build_memory_queue_store() -> None:
    store = build_queue_store(
        "memory",
        redis_url="redis://localhost:6379/0",
        redis_prefix="smartmenu:test",
    )
    assert isinstance(store, InMemoryJobQueue)


def test_build_unknown_queue_store_raises() -> None:
    with pytest.raises(ValueError):
        build_queue_store(
            "unknown",
            redis_url="redis://localhost:6379/0",
            redis_prefix="smartmenu:test",
        )
