from aiogram.fsm.state import State, StatesGroup


class NewTicket(StatesGroup):
    """Texnik murojaat (umumiy) yaratish bosqichlari."""
    category = State()     # kategoriya tanlash (inline)
    description = State()  # muammo tavsifi
    attachment = State()   # ixtiyoriy skrinshot
    contact = State()      # telefon / login
    priority = State()     # muhimlik darajasi
    confirm = State()      # tasdiqlash


class PasswordReset(StatesGroup):
    """«Parolni unutdim» qisqa oqimi."""
    identifier = State()   # login / telefon / email
    confirm = State()
