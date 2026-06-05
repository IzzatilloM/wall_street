from aiogram.fsm.state import State, StatesGroup


class StudentRegistration(StatesGroup):
    first_name = State()
    last_name = State()
    phone = State()
    email = State()
    confirm = State()
