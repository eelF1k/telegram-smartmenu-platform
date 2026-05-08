import logging
import time
from collections import defaultdict, deque
from collections.abc import Awaitable, Callable
from typing import Any

from aiogram import BaseMiddleware
from aiogram.types import Message, TelegramObject

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
    def __init__(self, limit_per_minute: int) -> None:
        self._limit = limit_per_minute
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
                await event.answer("Забагато запитів. Спробуйте трохи пізніше.")
                return None
            bucket.append(now)
        return await handler(event, data)


class BanCheckMiddleware(BaseMiddleware):
    def __init__(self, banned_ids: set[int] | None = None) -> None:
        self._banned_ids = banned_ids or set()

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
            await event.answer("Ваш акаунт тимчасово заблокований у SmartMenu.")
            return None
        return await handler(event, data)
