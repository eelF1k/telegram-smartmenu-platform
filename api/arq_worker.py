from bot.config import BotSettings

try:
    from arq.connections import RedisSettings
    from arq.worker import Worker
except Exception:  # pragma: no cover - optional runtime dependency
    RedisSettings = None
    Worker = None


async def process_notification_job(ctx: dict, job: dict) -> None:
    # ARQ worker entrypoint: actual delivery adapters are injected in later phases.
    _ = ctx
    _ = job


def build_arq_worker():
    if Worker is None or RedisSettings is None:
        raise RuntimeError("ARQ is not installed. Add dependency `arq` to run this worker.")
    settings = BotSettings()
    redis_settings = RedisSettings.from_dsn(settings.redis_url)
    return Worker(
        functions=[process_notification_job],
        redis_settings=redis_settings,
    )
