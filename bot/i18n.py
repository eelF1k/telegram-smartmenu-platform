from collections.abc import Callable

DEFAULT_LOCALE = "uk"
SUPPORTED_LOCALES = {"uk", "en"}

MESSAGES: dict[str, dict[str, str]] = {
    "uk": {
        "too_many_requests": "Забагато запитів. Спробуйте трохи пізніше.",
        "account_banned": "Ваш акаунт тимчасово заблокований у SmartMenu.",
        "welcome": (
            "Вітаю у SmartMenu.\n"
            "Команди: /menu /profile /reserve /support /referral /help /pricing /buy"
        ),
        "referral_applied": "\nРеферальний код застосовано. Ви отримали welcome бонус.",
        "help": (
            "Доступно:\n"
            "/menu - відкрити меню\n"
            "/profile - профіль\n"
            "/reserve - бронювання столу\n"
            "/support - підтримка\n"
            "/referral - реферальне посилання"
        ),
        "choose_venue": "Оберіть заклад:",
        "profile_unavailable": "Профіль недоступний.",
        "profile_text": "Профіль: id={user_id}, username=@{username}",
        "reserve_prompt": "Бронювання: оберіть заклад (введіть назву).",
        "support_text": "Підтримка: support@smartmenu.local",
        "referral_unavailable": "Не вдалося згенерувати реферальне посилання.",
        "referral_text": (
            "Ваше реферальне посилання: https://t.me/SmartMenuBot?start=ref{user_id}\n"
            "Запрошено друзів: {invitee_count}"
        ),
        "cancelled": "Поточну дію скасовано.",
    },
    "en": {
        "too_many_requests": "Too many requests. Please try again later.",
        "account_banned": "Your account is temporarily blocked in SmartMenu.",
        "welcome": (
            "Welcome to SmartMenu.\n"
            "Commands: /menu /profile /reserve /support /referral /help /pricing /buy"
        ),
        "referral_applied": "\nReferral code applied. You received a welcome bonus.",
        "help": (
            "Available:\n"
            "/menu - open menu\n"
            "/profile - profile\n"
            "/reserve - table reservation\n"
            "/support - support\n"
            "/referral - referral link"
        ),
        "choose_venue": "Choose a venue:",
        "profile_unavailable": "Profile is unavailable.",
        "profile_text": "Profile: id={user_id}, username=@{username}",
        "reserve_prompt": "Reservation: choose venue (enter name).",
        "support_text": "Support: support@smartmenu.local",
        "referral_unavailable": "Failed to generate referral link.",
        "referral_text": (
            "Your referral link: https://t.me/SmartMenuBot?start=ref{user_id}\n"
            "Invited friends: {invitee_count}"
        ),
        "cancelled": "Current action cancelled.",
    },
}


def detect_locale(language_code: str | None, default_locale: str = DEFAULT_LOCALE) -> str:
    if language_code:
        candidate = language_code.lower().split("-", maxsplit=1)[0]
        if candidate in SUPPORTED_LOCALES:
            return candidate
    return default_locale if default_locale in SUPPORTED_LOCALES else DEFAULT_LOCALE


def translate(key: str, locale: str, **kwargs: object) -> str:
    source = MESSAGES.get(locale) or MESSAGES[DEFAULT_LOCALE]
    template = source.get(key) or MESSAGES[DEFAULT_LOCALE].get(key) or key
    return template.format(**kwargs)


def translator(locale: str) -> Callable[..., str]:
    def _translate(key: str, **kwargs: object) -> str:
        return translate(key=key, locale=locale, **kwargs)

    return _translate
