import logging
import time
from collections import defaultdict, deque
from collections.abc import Awaitable, Callable
from typing import Any

from aiogram import BaseMiddleware
from aiogram.types import Message, TelegramObject

from bot.i18n import detect_locale, translator

logger = logging.getLogger(__name__)


class LoggingMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        if isinstance(event, Message) and event.from_user:
            logger.info(
                "bot_message_received",
                extra={"user_id": event.from_user.id, "text": event.text or ""},
            )
        return await handler(event, data)


class ThrottlingMiddleware(BaseMiddleware):
    def __init__(self, limit_per_minute: int, default_locale: str = "uk") -> None:
        self._limit = limit_per_minute
        self._default_locale = default_locale
        self._events: dict[int, deque[float]] = defaultdict(deque)

    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        if isinstance(event, Message) and event.from_user:
            now = time.time()
            cutoff = now - 60
            bucket = self._events[event.from_user.id]
            while bucket and bucket[0] < cutoff:
                bucket.popleft()
            if len(bucket) >= self._limit:
                locale = data.get("locale", self._default_locale)
                t = data.get("t", translator(locale))
                await event.answer(t("too_many_requests"))
                return None
            bucket.append(now)
        return await handler(event, data)


class BanCheckMiddleware(BaseMiddleware):
    def __init__(self, banned_ids: set[int] | None = None, default_locale: str = "uk") -> None:
        self._banned_ids = banned_ids or set()
        self._default_locale = default_locale

    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        if (
            isinstance(event, Message)
            and event.from_user
            and event.from_user.id in self._banned_ids
        ):
            locale = data.get("locale", self._default_locale)
            t = data.get("t", translator(locale))
            await event.answer(t("account_banned"))
            return None
        return await handler(event, data)


class LocalizationMiddleware(BaseMiddleware):
    def __init__(self, default_locale: str = "uk") -> None:
        self._default_locale = default_locale

    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        if isinstance(event, Message):
            locale = detect_locale(
                event.from_user.language_code if event.from_user else None,
                default_locale=self._default_locale,
            )
        else:
            locale = self._default_locale
        data["locale"] = locale
        data["t"] = translator(locale)
        return await handler(event, data)
