from aiogram.fsm.state import State, StatesGroup


class OrderFlow(StatesGroup):
    venue = State()
    category = State()
    dish = State()
    modifiers = State()
    destination = State()
    payment = State()
