from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton

def get_main_menu_kb() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="📝 Anketa to'ldirish")],
            [KeyboardButton(text="📷 To'g'ri rasm talablari"), KeyboardButton(text="🛂 Pasport rasmi talablari")]
        ],
        resize_keyboard=True
    )

def get_cancel_kb() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="❌ Bekor qilish")]
        ],
        resize_keyboard=True
    )

def get_skip_kb(text: str = "➡️ O'tkazib yuborish (Mavjud emas)") -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text=text)],
            [KeyboardButton(text="❌ Bekor qilish")]
        ],
        resize_keyboard=True
    )

def get_gender_kb() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="Erkak (Male)"), KeyboardButton(text="Ayol (Female)")],
            [KeyboardButton(text="❌ Bekor qilish")]
        ],
        resize_keyboard=True
    )

def get_country_kb() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="🇺🇿 O'zbekiston")],
            [KeyboardButton(text="❌ Bekor qilish")]
        ],
        resize_keyboard=True
    )

def get_education_kb() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="Maktab / Kollej / Litsey (High School degree)")],
            [KeyboardButton(text="Bakalavr diplomi (University Degree)")],
            [KeyboardButton(text="Magistr diplomi (Master's Degree)")],
            [KeyboardButton(text="Oliy ta'lim talabasi (Some University Courses)")],
            [KeyboardButton(text="Kasb-hunar maktabi (Vocational School)")],
            [KeyboardButton(text="Faqat boshlang'ich / Maktab bitirmagan")],
            [KeyboardButton(text="Doktorantura / PhD")],
            [KeyboardButton(text="❌ Bekor qilish")]
        ],
        resize_keyboard=True
    )

def get_marital_status_kb() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="Turmush qurmagan (Unmarried)")],
            [KeyboardButton(text="Turmush qurgan (Married)")],
            [KeyboardButton(text="Ajrashgan (Divorced)")],
            [KeyboardButton(text="Beva (Widowed)")],
            [KeyboardButton(text="❌ Bekor qilish")]
        ],
        resize_keyboard=True
    )

def get_children_count_kb() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="0 (Farzand yo'q)")],
            [KeyboardButton(text="1"), KeyboardButton(text="2"), KeyboardButton(text="3")],
            [KeyboardButton(text="4"), KeyboardButton(text="5"), KeyboardButton(text="6+")]
        ],
        resize_keyboard=True
    )

def get_confirm_kb() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="✅ Ma'lumotlarni tasdiqlash va yuborish")],
            [KeyboardButton(text="🔄 Qaytadan to'ldirish")],
            [KeyboardButton(text="❌ Bekor qilish")]
        ],
        resize_keyboard=True
    )

def get_admin_menu_kb() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="📊 Statistika")],
            [KeyboardButton(text="📥 Excel formatda yuklab olish")],
            [KeyboardButton(text="📨 Mijozga Confirmation Code yuborish")],
            [KeyboardButton(text="🏠 Asosiy menyu")]
        ],
        resize_keyboard=True
    )

def get_payment_admin_kb(payment_id: int, user_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="✅ To'lovni tasdiqlash",
                    callback_data=f"pay_approve:{payment_id}:{user_id}",
                ),
                InlineKeyboardButton(
                    text="❌ Rad etish",
                    callback_data=f"pay_reject:{payment_id}:{user_id}",
                ),
            ]
        ]
    )
