from aiogram import Bot, F, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message, PreCheckoutQuery

from bot.config import BotSettings
from bot.keyboards import (
    categories_keyboard,
    dishes_keyboard,
    modifiers_keyboard,
    payment_keyboard,
    venues_keyboard,
)
from bot.menu_data import MENU_DATA, get_category, get_dish, get_venue
from bot.payments import get_product, list_products_text, product_prices
from bot.referrals import ReferralService, parse_start_referral
from bot.states import OrderFlow, ReserveFlow

router = Router(name="client_router")
referrals = ReferralService()
settings = BotSettings()


@router.message(Command("start"))
async def start_handler(message: Message, state: FSMContext) -> None:
    await state.clear()
    referral_payload = parse_start_referral(message.text)
    referral_text = ""
    if referral_payload and message.from_user:
        registered = referrals.register_referral(message.from_user.id, referral_payload)
        if registered:
            referral_text = "\nРеферальний код застосовано. Ви отримали welcome бонус."
    await message.answer(
        "Вітаю у SmartMenu.\n"
        "Команди: /menu /profile /reserve /support /referral /help /pricing /buy" + referral_text
    )


@router.message(Command("help"))
async def help_handler(message: Message) -> None:
    await message.answer(
        "Доступно:\n"
        "/menu - відкрити меню\n"
        "/profile - профіль\n"
        "/reserve - бронювання столу\n"
        "/support - підтримка\n"
        "/referral - реферальне посилання"
    )


@router.message(Command("menu"))
async def menu_handler(message: Message, state: FSMContext) -> None:
    await state.clear()
    await state.set_state(OrderFlow.venue)
    await message.answer("Оберіть заклад:", reply_markup=venues_keyboard(MENU_DATA))


@router.message(Command("profile"))
async def profile_handler(message: Message) -> None:
    user = message.from_user
    if not user:
        await message.answer("Профіль недоступний.")
        return
    await message.answer(f"Профіль: id={user.id}, username=@{user.username or 'unknown'}")


@router.message(Command("reserve"))
async def reserve_handler(message: Message, state: FSMContext) -> None:
    await state.set_state(ReserveFlow.venue)
    await message.answer("Бронювання: оберіть заклад (введіть назву).")


@router.message(Command("support"))
async def support_handler(message: Message) -> None:
    await message.answer("Підтримка: support@smartmenu.local")


@router.message(Command("referral"))
async def referral_handler(message: Message) -> None:
    user = message.from_user
    if not user:
        await message.answer("Не вдалося згенерувати реферальне посилання.")
        return
    stats = referrals.stats(user.id)
    await message.answer(
        f"Ваше реферальне посилання: https://t.me/SmartMenuBot?start=ref{user.id}\n"
        f"Запрошено друзів: {stats.invitee_count}"
    )


@router.message(Command("pricing"))
async def pricing_handler(message: Message) -> None:
    await message.answer(list_products_text())


@router.message(Command("buy"))
async def buy_handler(message: Message, bot: Bot) -> None:
    text = message.text or ""
    parts = text.split(maxsplit=1)
    if len(parts) < 2:
        await message.answer("Формат: /buy <product_id>, приклад: /buy hoodie")
        return
    product = get_product(parts[1].strip())
    if not product:
        await message.answer("Товар не знайдено. Використай /pricing")
        return
    if not message.from_user:
        await message.answer("Не вдалося визначити користувача для оплати.")
        return
    await bot.send_invoice(
        chat_id=message.chat.id,
        title=product.title,
        description=product.description,
        payload=f"order:{product.product_id}:{message.from_user.id}",
        provider_token=settings.telegram_provider_token,
        currency=product.currency,
        prices=product_prices(product),
        start_parameter=f"buy-{product.product_id}",
    )


@router.message(Command("cancel"))
async def cancel_handler(message: Message, state: FSMContext) -> None:
    await state.clear()
    await message.answer("Поточну дію скасовано.")


@router.message(ReserveFlow.venue, F.text)
async def reserve_venue_step(message: Message, state: FSMContext) -> None:
    await state.update_data(venue=message.text)
    await state.set_state(ReserveFlow.datetime)
    await message.answer("Вкажіть дату і час бронювання, наприклад: 2026-05-10 19:00")


@router.message(ReserveFlow.datetime, F.text)
async def reserve_destination_step(message: Message, state: FSMContext) -> None:
    data = await state.get_data()
    venue = data.get("venue", "заклад")
    await state.clear()
    await message.answer(
        f"Бронювання створено: {venue}, час: {message.text}. Підтвердження надіслано."
    )


@router.callback_query(F.data.startswith("ord:venue:"))
async def order_venue_callback(callback: CallbackQuery, state: FSMContext) -> None:
    _, _, venue_id = callback.data.split(":")
    venue = get_venue(venue_id)
    if not venue:
        await callback.answer("Заклад не знайдено", show_alert=True)
        return
    await state.set_state(OrderFlow.category)
    await state.update_data(venue_id=venue_id, page=0)
    await callback.message.edit_text(
        f"Заклад: {venue['name']}\nОберіть категорію:",
        reply_markup=categories_keyboard(venue_id, venue["categories"], page=0),
    )
    await callback.answer()


@router.callback_query(F.data.startswith("ord:catpg:"))
async def order_category_page_callback(callback: CallbackQuery, state: FSMContext) -> None:
    _, _, venue_id, page_str = callback.data.split(":")
    venue = get_venue(venue_id)
    if not venue:
        await callback.answer("Заклад не знайдено", show_alert=True)
        return
    page = int(page_str)
    await state.update_data(page=page)
    await callback.message.edit_reply_markup(
        reply_markup=categories_keyboard(venue_id, venue["categories"], page=page)
    )
    await callback.answer()


@router.callback_query(F.data.startswith("ord:cat:"))
async def order_category_callback(callback: CallbackQuery, state: FSMContext) -> None:
    _, _, venue_id, category_id = callback.data.split(":")
    category = get_category(venue_id, category_id)
    if not category:
        await callback.answer("Категорію не знайдено", show_alert=True)
        return
    await state.set_state(OrderFlow.dish)
    await state.update_data(venue_id=venue_id, category_id=category_id, dish_page=0)
    await callback.message.edit_text(
        f"Категорія: {category['name']}\nОберіть страву:",
        reply_markup=dishes_keyboard(venue_id, category_id, category["dishes"], page=0),
    )
    await callback.answer()


@router.callback_query(F.data.startswith("ord:dishpg:"))
async def order_dish_page_callback(callback: CallbackQuery, state: FSMContext) -> None:
    _, _, venue_id, category_id, page_str = callback.data.split(":")
    category = get_category(venue_id, category_id)
    if not category:
        await callback.answer("Категорію не знайдено", show_alert=True)
        return
    page = int(page_str)
    await state.update_data(dish_page=page)
    await callback.message.edit_reply_markup(
        reply_markup=dishes_keyboard(venue_id, category_id, category["dishes"], page=page)
    )
    await callback.answer()


@router.callback_query(F.data.startswith("ord:dish:"))
async def order_dish_callback(callback: CallbackQuery, state: FSMContext) -> None:
    _, _, venue_id, category_id, dish_id = callback.data.split(":")
    dish = get_dish(venue_id, category_id, dish_id)
    if not dish:
        await callback.answer("Страву не знайдено", show_alert=True)
        return
    await state.set_state(OrderFlow.modifiers)
    await state.update_data(dish_id=dish_id, dish_name=dish["name"], modifiers=[])
    await callback.message.edit_text(
        f"Страва: {dish['name']} ({dish['price']} грн)\nОберіть модифікатори:",
        reply_markup=modifiers_keyboard(dish["modifiers"]),
    )
    await callback.answer()


@router.callback_query(F.data.startswith("ord:mod:"))
async def order_modifier_callback(callback: CallbackQuery, state: FSMContext) -> None:
    _, _, modifier = callback.data.split(":")
    data = await state.get_data()
    selected: list[str] = data.get("modifiers", [])

    if modifier == "done":
        await state.set_state(OrderFlow.destination)
        await callback.message.edit_text(
            "Вкажіть адресу доставки або номер столика (наприклад: table-7)."
        )
        await callback.answer()
        return

    if modifier not in selected:
        selected.append(modifier)
    await state.update_data(modifiers=selected)
    await callback.answer(f"Додано: {modifier}")


@router.message(OrderFlow.destination, F.text)
async def order_destination_step(message: Message, state: FSMContext) -> None:
    await state.update_data(destination=message.text)
    await state.set_state(OrderFlow.payment)
    await message.answer("Оберіть метод оплати:", reply_markup=payment_keyboard())


@router.callback_query(F.data.startswith("ord:pay:"))
async def order_payment_callback(callback: CallbackQuery, state: FSMContext) -> None:
    _, _, method = callback.data.split(":")
    data = await state.get_data()
    await state.clear()
    modifiers = ", ".join(data.get("modifiers", [])) or "без модифікаторів"
    await callback.message.edit_text(
        "Замовлення сформовано:\n"
        f"- Страва: {data.get('dish_name', 'N/A')}\n"
        f"- Модифікатори: {modifiers}\n"
        f"- Локація: {data.get('destination', 'N/A')}\n"
        f"- Оплата: {method}"
    )
    await callback.answer("Замовлення підтверджено")


@router.pre_checkout_query()
async def pre_checkout_handler(query: PreCheckoutQuery, bot: Bot) -> None:
    await bot.answer_pre_checkout_query(pre_checkout_query_id=query.id, ok=True)


@router.message(F.successful_payment)
async def successful_payment_handler(message: Message) -> None:
    payment = message.successful_payment
    await message.answer(
        "Оплату отримано ✅\n"
        f"Сума: {payment.total_amount / 100:.2f} {payment.currency}\n"
        f"Payload: {payment.invoice_payload}"
    )
