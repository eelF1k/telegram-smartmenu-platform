from dataclasses import dataclass
from typing import Protocol


class DeliveryAdapter(Protocol):
    channel: str

    def send(self, payload: dict) -> bool: ...


@dataclass
class TelegramDeliveryAdapter:
    channel: str = "telegram"

    def send(self, payload: dict) -> bool:
        # Stub adapter for portfolio/demo mode.
        _ = payload
        return True


@dataclass
class EmailDeliveryAdapter:
    channel: str = "email"

    def send(self, payload: dict) -> bool:
        _ = payload
        return True


@dataclass
class WebhookDeliveryAdapter:
    channel: str = "webhook"

    def send(self, payload: dict) -> bool:
        _ = payload
        return True


def build_delivery_adapters() -> dict[str, DeliveryAdapter]:
    return {
        "telegram": TelegramDeliveryAdapter(),
        "email": EmailDeliveryAdapter(),
        "webhook": WebhookDeliveryAdapter(),
    }
