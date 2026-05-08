from aiogram.types import Update
from fastapi import FastAPI, Header, HTTPException

from bot.app import create_bot, create_dispatcher
from bot.config import BotSettings

app = FastAPI(title="SmartMenu API", version="0.1.0")
settings = BotSettings()
bot = create_bot(settings)
dispatcher = create_dispatcher(settings)


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/telegram/webhook/{secret}")
async def telegram_webhook(
    secret: str,
    payload: dict,
    x_telegram_bot_api_secret_token: str | None = Header(
        default=None,
        alias="X-Telegram-Bot-Api-Secret-Token",
    ),
) -> dict[str, bool]:
    if secret != settings.webhook_secret:
        raise HTTPException(status_code=401, detail="invalid_webhook_secret")
    if (
        x_telegram_bot_api_secret_token
        and x_telegram_bot_api_secret_token != settings.webhook_secret
    ):
        raise HTTPException(status_code=401, detail="invalid_telegram_header_secret")

    update = Update.model_validate(payload)
    await dispatcher.feed_update(bot=bot, update=update)
    return {"ok": True}
