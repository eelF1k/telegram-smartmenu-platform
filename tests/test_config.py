from bot.config import BotSettings


def test_bot_settings_defaults() -> None:
    settings = BotSettings()
    assert settings.bot_mode in {"polling", "webhook"}
    assert settings.webhook_secret
    assert settings.default_locale in {"uk", "en"}
