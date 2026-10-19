from aiogram.fsm.state import State, StatesGroup

class PaymentStates(StatesGroup):
    waiting_for_receipt = State()

class ApplicationStates(StatesGroup):
    # Passport Photo first
    passport_photo = State()

    # Primary Applicant (Part 1)
    last_name = State()
    first_name = State()
    middle_name = State()
    gender = State()
    birth_date = State()
    birth_city = State()
    birth_country = State()
    photo = State()
    
    # Address & Contacts
    address_line1 = State()
    city = State()
    district_state = State()
    postal_code = State()
    country = State()
    live_country = State()
    phone_number = State()
    email = State()
    
    # Eligibility & Status
    education_level = State()
    marital_status = State()
    children_count = State()

class SpouseStates(StatesGroup):
    # Spouse Details (Part 2)
    last_name = State()
    first_name = State()
    middle_name = State()
    birth_date = State()
    gender = State()
    birth_city = State()
    birth_country = State()
    photo = State()

class ChildStates(StatesGroup):
    # Child Details (Part 3)
    last_name = State()
    first_name = State()
    middle_name = State()
    birth_date = State()
    gender = State()
    birth_city = State()
    birth_country = State()
    photo = State()

class ConfirmStates(StatesGroup):
    confirm = State()

class AdminStates(StatesGroup):
    waiting_for_app_id = State()
    waiting_for_confirmation_code = State()
