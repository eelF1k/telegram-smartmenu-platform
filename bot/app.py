from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.fsm.storage.redis import RedisStorage
from redis.asyncio import Redis

from bot.config import BotSettings
from bot.middlewares import (
    BanCheckMiddleware,
    LocalizationMiddleware,
    LoggingMiddleware,
    ThrottlingMiddleware,
)
from bot.routers import router


def create_bot(settings: BotSettings) -> Bot:
    return Bot(token=settings.telegram_bot_token)


def create_dispatcher(settings: BotSettings) -> Dispatcher:
    storage = _create_storage(settings)
    dp = Dispatcher(storage=storage)
    dp.message.middleware(LocalizationMiddleware(default_locale=settings.default_locale))
    dp.message.middleware(LoggingMiddleware())
    dp.message.middleware(
        ThrottlingMiddleware(
            limit_per_minute=settings.throttle_per_minute,
            default_locale=settings.default_locale,
        )
    )
    dp.message.middleware(BanCheckMiddleware(default_locale=settings.default_locale))
    dp.callback_query.middleware(LocalizationMiddleware(default_locale=settings.default_locale))
    dp.include_router(router)
    return dp


def _create_storage(settings: BotSettings):
    try:
        redis = Redis.from_url(settings.redis_url)
        return RedisStorage(redis=redis)
    except Exception:
        return MemoryStorage()
