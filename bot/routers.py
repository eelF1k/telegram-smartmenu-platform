from aiogram import F, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from bot.states import OrderFlow

router = Router(name="client_router")


@router.message(Command("start"))
async def start_handler(message: Message, state: FSMContext) -> None:
    await state.clear()
    await message.answer(
        "Вітаю у SmartMenu.\nКоманди: /menu /profile /reserve /support /referral /help"
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
async def menu_handler(message: Message) -> None:
    await message.answer("Меню буде відкрите через WebApp на наступному кроці.")


@router.message(Command("profile"))
async def profile_handler(message: Message) -> None:
    user = message.from_user
    if not user:
        await message.answer("Профіль недоступний.")
        return
    await message.answer(f"Профіль: id={user.id}, username=@{user.username or 'unknown'}")


@router.message(Command("reserve"))
async def reserve_handler(message: Message, state: FSMContext) -> None:
    await state.set_state(OrderFlow.venue)
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
    await message.answer(f"Ваше реферальне посилання: https://t.me/SmartMenuBot?start=ref{user.id}")


@router.message(Command("cancel"))
async def cancel_handler(message: Message, state: FSMContext) -> None:
    await state.clear()
    await message.answer("Поточну дію скасовано.")


@router.message(OrderFlow.venue, F.text)
async def reserve_venue_step(message: Message, state: FSMContext) -> None:
    await state.update_data(venue=message.text)
    await state.set_state(OrderFlow.destination)
    await message.answer("Вкажіть дату і час бронювання, наприклад: 2026-05-10 19:00")


@router.message(OrderFlow.destination, F.text)
async def reserve_destination_step(message: Message, state: FSMContext) -> None:
    data = await state.get_data()
    venue = data.get("venue", "заклад")
    await state.clear()
    await message.answer(
        f"Бронювання створено: {venue}, час: {message.text}. Підтвердження надіслано."
    )
