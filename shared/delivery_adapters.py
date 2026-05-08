from dataclasses import dataclass
from email.message import EmailMessage
from typing import Protocol

import aiosmtplib
import httpx

from bot.config import BotSettings


class DeliveryAdapter(Protocol):
    channel: str

    async def send(self, payload: dict) -> bool: ...


@dataclass
class TelegramDeliveryAdapter:
    channel: str = "telegram"

    async def send(self, payload: dict) -> bool:
        settings = BotSettings()
        chat_id = payload.get("user_id")
        if not chat_id or not settings.telegram_bot_token:
            return True
        text = payload.get("text") or f"[SmartMenu] {payload.get('status', 'notification')}"
        url = f"https://api.telegram.org/bot{settings.telegram_bot_token}/sendMessage"
        async with httpx.AsyncClient(timeout=5) as client:
            response = await client.post(url, json={"chat_id": chat_id, "text": text})
        return response.status_code == 200


@dataclass
class EmailDeliveryAdapter:
    channel: str = "email"

    async def send(self, payload: dict) -> bool:
        settings = BotSettings()
        to_email = payload.get("to_email")
        if not to_email:
            return True
        subject = payload.get("subject", "SmartMenu notification")
        body = payload.get("body", str(payload))
        message = EmailMessage()
        message["From"] = settings.smtp_from_email
        message["To"] = str(to_email)
        message["Subject"] = str(subject)
        message.set_content(str(body))
        try:
            await aiosmtplib.send(
                message,
                hostname=settings.smtp_host,
                port=settings.smtp_port,
                username=settings.smtp_username or None,
                password=settings.smtp_password or None,
                start_tls=False,
                timeout=5,
            )
            return True
        except Exception:
            return False


@dataclass
class WebhookDeliveryAdapter:
    channel: str = "webhook"

    async def send(self, payload: dict) -> bool:
        settings = BotSettings()
        url = payload.get("webhook_url") or settings.delivery_webhook_url
        if not url:
            return True
        async with httpx.AsyncClient(timeout=5) as client:
            response = await client.post(url, json=payload)
        return response.status_code < 400


def build_delivery_adapters() -> dict[str, DeliveryAdapter]:
    return {
        "telegram": TelegramDeliveryAdapter(),
        "email": EmailDeliveryAdapter(),
        "webhook": WebhookDeliveryAdapter(),
    }
