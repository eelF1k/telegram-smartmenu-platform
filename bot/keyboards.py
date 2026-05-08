from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup


def paginate_items[T](items: list[T], page: int, page_size: int = 4) -> tuple[list[T], int]:
    safe_page = max(page, 0)
    start = safe_page * page_size
    end = start + page_size
    return items[start:end], safe_page


def _pager_row(prefix: str, page: int, has_next: bool) -> list[InlineKeyboardButton]:
    row: list[InlineKeyboardButton] = []
    if page > 0:
        row.append(InlineKeyboardButton(text="⬅️", callback_data=f"{prefix}:{page - 1}"))
    if has_next:
        row.append(InlineKeyboardButton(text="➡️", callback_data=f"{prefix}:{page + 1}"))
    return row


def venues_keyboard(venues: list[dict]) -> InlineKeyboardMarkup:
    rows = [
        [InlineKeyboardButton(text=venue["name"], callback_data=f"ord:venue:{venue['id']}")]
        for venue in venues
    ]
    return InlineKeyboardMarkup(inline_keyboard=rows)


def categories_keyboard(venue_id: str, categories: list[dict], page: int) -> InlineKeyboardMarkup:
    chunk, safe_page = paginate_items(categories, page=page, page_size=4)
    rows = [
        [
            InlineKeyboardButton(
                text=category["name"],
                callback_data=f"ord:cat:{venue_id}:{category['id']}",
            )
        ]
        for category in chunk
    ]
    pager = _pager_row(
        prefix=f"ord:catpg:{venue_id}",
        page=safe_page,
        has_next=((safe_page + 1) * 4) < len(categories),
    )
    if pager:
        rows.append(pager)
    return InlineKeyboardMarkup(inline_keyboard=rows)


def dishes_keyboard(
    venue_id: str, category_id: str, dishes: list[dict], page: int
) -> InlineKeyboardMarkup:
    chunk, safe_page = paginate_items(dishes, page=page, page_size=4)
    rows = [
        [
            InlineKeyboardButton(
                text=f"{dish['name']} - {dish['price']} грн",
                callback_data=f"ord:dish:{venue_id}:{category_id}:{dish['id']}",
            )
        ]
        for dish in chunk
    ]
    pager = _pager_row(
        prefix=f"ord:dishpg:{venue_id}:{category_id}",
        page=safe_page,
        has_next=((safe_page + 1) * 4) < len(dishes),
    )
    if pager:
        rows.append(pager)
    return InlineKeyboardMarkup(inline_keyboard=rows)


def modifiers_keyboard(modifiers: list[str]) -> InlineKeyboardMarkup:
    rows = [
        [InlineKeyboardButton(text=modifier, callback_data=f"ord:mod:{modifier}")]
        for modifier in modifiers
    ]
    rows.append([InlineKeyboardButton(text="✅ Далі", callback_data="ord:mod:done")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def payment_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="💳 Card", callback_data="ord:pay:card")],
            [InlineKeyboardButton(text="💵 Cash", callback_data="ord:pay:cash")],
        ]
    )
