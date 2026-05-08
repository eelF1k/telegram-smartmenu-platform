from bot.keyboards import categories_keyboard, dishes_keyboard, paginate_items
from bot.menu_data import MENU_DATA


def test_paginate_items_returns_first_page() -> None:
    items = [1, 2, 3, 4, 5]
    chunk, page = paginate_items(items, page=0, page_size=2)
    assert chunk == [1, 2]
    assert page == 0


def test_categories_keyboard_has_rows() -> None:
    venue = MENU_DATA[0]
    keyboard = categories_keyboard(venue["id"], venue["categories"], page=0)
    assert keyboard.inline_keyboard
    assert len(keyboard.inline_keyboard) >= 1


def test_dishes_keyboard_renders_prices() -> None:
    venue = MENU_DATA[0]
    category = venue["categories"][0]
    keyboard = dishes_keyboard(venue["id"], category["id"], category["dishes"], page=0)
    first_button = keyboard.inline_keyboard[0][0]
    assert "грн" in first_button.text
