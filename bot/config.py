from pydantic_settings import BaseSettings, SettingsConfigDict


class BotSettings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    telegram_bot_token: str = "123456:TEST_TOKEN"
    telegram_provider_token: str = "381764678:TEST:12345"
    bot_mode: str = "polling"
    webhook_secret: str = "dev-webhook-secret"
    redis_url: str = "redis://localhost:6379/0"
    database_url: str = "postgresql+asyncpg://smartmenu:smartmenu@localhost:5432/smartmenu"
    throttle_per_minute: int = 30
    default_locale: str = "uk"
    queue_backend: str = "memory"
    queue_redis_prefix: str = "smartmenu:queue"
