from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from utils.locations import COUNTRIES, REGIONS, EDUCATION_LEVELS, MARITAL_STATUSES


def _chunk_rows(items: list[str], per_row: int = 1) -> list[list[KeyboardButton]]:
    rows = []
    for i in range(0, len(items), per_row):
        rows.append([KeyboardButton(text=x) for x in items[i:i + per_row]])
    return rows


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
        keyboard=[[KeyboardButton(text="❌ Bekor qilish")]],
        resize_keyboard=True
    )


def get_skip_kb(text: str = "➡️ O'tkazib yuborish") -> ReplyKeyboardMarkup:
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
            [KeyboardButton(text="Erkak"), KeyboardButton(text="Ayol")],
            [KeyboardButton(text="❌ Bekor qilish")]
        ],
        resize_keyboard=True
    )


def get_country_kb() -> ReplyKeyboardMarkup:
    rows = _chunk_rows(COUNTRIES, per_row=2)
    rows.append([KeyboardButton(text="❌ Bekor qilish")])
    return ReplyKeyboardMarkup(keyboard=rows, resize_keyboard=True)


def get_region_kb() -> ReplyKeyboardMarkup:
    rows = [[KeyboardButton(text=r)] for r in REGIONS.keys()]
    rows.append([KeyboardButton(text="❌ Bekor qilish")])
    return ReplyKeyboardMarkup(keyboard=rows, resize_keyboard=True)


def get_district_kb(region: str) -> ReplyKeyboardMarkup:
    districts = REGIONS.get(region, [])
    if not districts:
        return get_cancel_kb()
    rows = [[KeyboardButton(text=d)] for d in districts]
    rows.append([KeyboardButton(text="❌ Bekor qilish")])
    return ReplyKeyboardMarkup(keyboard=rows, resize_keyboard=True)


def get_education_kb() -> ReplyKeyboardMarkup:
    rows = [[KeyboardButton(text=e)] for e in EDUCATION_LEVELS]
    rows.append([KeyboardButton(text="❌ Bekor qilish")])
    return ReplyKeyboardMarkup(keyboard=rows, resize_keyboard=True)


def get_marital_status_kb() -> ReplyKeyboardMarkup:
    rows = [[KeyboardButton(text=m)] for m in MARITAL_STATUSES]
    rows.append([KeyboardButton(text="❌ Bekor qilish")])
    return ReplyKeyboardMarkup(keyboard=rows, resize_keyboard=True)


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
