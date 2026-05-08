import asyncio

from bot.app import create_bot, create_dispatcher
from bot.config import BotSettings


async def main() -> None:
    settings = BotSettings()
    bot = create_bot(settings)
    dp = create_dispatcher(settings)

    if settings.bot_mode == "webhook":
        # Webhook mode is handled by FastAPI endpoint in api.app.
        await bot.session.close()
        return

    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
