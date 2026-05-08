from bot.i18n import detect_locale, translate


def test_detect_locale_from_language_code() -> None:
    assert detect_locale("en-US") == "en"
    assert detect_locale("uk-UA") == "uk"


def test_detect_locale_fallback_to_default() -> None:
    assert detect_locale("pl-PL", default_locale="uk") == "uk"


def test_translate_english_message() -> None:
    message = translate("support_text", locale="en")
    assert message == "Support: support@smartmenu.local"


def test_translate_with_format_args() -> None:
    message = translate("profile_text", locale="uk", user_id=7, username="demo")
    assert "id=7" in message
    assert "@demo" in message
