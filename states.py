from aiogram.fsm.state import State, StatesGroup

class PaymentStates(StatesGroup):
    waiting_for_receipt = State()

class ApplicationStates(StatesGroup):
    # SHAXSIY MA'LUMOTLAR (greencards.uz/form tartibida)
    last_name = State()
    first_name = State()
    gender = State()
    birth_date = State()
    birth_country = State()
    birth_region = State()
    birth_district = State()

    # Pasport
    passport_number = State()
    passport_expiry = State()
    passport_photo = State()

    # RASM JOYLASHTIRISH
    photo = State()

    # YASHASH MANZILI
    live_country = State()
    live_region = State()
    live_district = State()
    address_line1 = State()
    email = State()
    phone_number = State()

    # TA'LIM / OILA
    education_level = State()
    marital_status = State()
    children_count = State()

class SpouseStates(StatesGroup):
    last_name = State()
    first_name = State()
    gender = State()
    birth_date = State()
    birth_country = State()
    birth_region = State()
    birth_district = State()
    education_level = State()
    passport_photo = State()
    photo = State()

class ChildStates(StatesGroup):
    last_name = State()
    first_name = State()
    gender = State()
    birth_date = State()
    birth_country = State()
    birth_region = State()
    birth_district = State()
    passport_photo = State()
    photo = State()

class ConfirmStates(StatesGroup):
    confirm = State()

class AdminStates(StatesGroup):
    waiting_for_app_id = State()
    waiting_for_confirmation_code = State()
