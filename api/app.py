from aiogram.types import Update
from fastapi import FastAPI, Header, HTTPException

from api.uow import uow_context
from bot.app import create_bot, create_dispatcher
from bot.config import BotSettings
from bot.menu_data import MENU_DATA

app = FastAPI(title="SmartMenu API", version="0.1.0")
settings = BotSettings()
bot = create_bot(settings)
dispatcher = create_dispatcher(settings)


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/webapp/menu")
async def webapp_menu() -> dict:
    return {"ok": True, "venues": MENU_DATA}


@app.get("/webapp/profile/{user_id}")
async def webapp_profile(user_id: int) -> dict:
    user_payload = {
        "user_id": user_id,
        "username": f"user{user_id}",
        "locale": settings.default_locale,
    }
    try:
        async with uow_context() as uow:
            user = await uow.users.get_by_telegram_id(user_id)
            if not user:
                user = await uow.users.create_user(
                    telegram_id=user_id,
                    username=f"user{user_id}",
                    locale=settings.default_locale,
                )
            user_payload = {
                "user_id": user.telegram_id,
                "username": user.username,
                "locale": user.locale,
            }
    except Exception:
        # If DB is not available, keep endpoint usable in local demo mode.
        pass

    return {
        "ok": True,
        "profile": {
            "user_id": user_payload["user_id"],
            "username": user_payload["username"],
            "locale": user_payload["locale"],
            "loyalty_points": 120,
            "orders_count": 7,
            "preferred_venue": "vinson-git",
        },
    }


@app.post("/webapp/confirm")
async def webapp_confirm(payload: dict) -> dict:
    return {"ok": True, "received": payload}


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
