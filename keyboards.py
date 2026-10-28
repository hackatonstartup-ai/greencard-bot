from aiogram.types import ReplyKeyboardRemove, ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from typing import Optional
from config import ADMIN_IDS, ADMIN_HIDE_BUTTONS
from utils.locations import COUNTRIES, REGIONS, EDUCATION_LEVELS, MARITAL_STATUSES


SUPPORT_BUTTON_TEXT = "☎️ Aloqa markazi"
BACK_TEXT = "⬅️ Orqaga"
RESTART_TEXT = "🔁 Boshidan boshlash"
CANCEL_TEXT = "❌ Bekor qilish"


def _nav_rows() -> list[list[KeyboardButton]]:
    """Anketa davomida har doim ko'rinadigan navigatsiya tugmalari."""
    return [
        [KeyboardButton(text=BACK_TEXT), KeyboardButton(text=RESTART_TEXT)],
        [KeyboardButton(text=CANCEL_TEXT)],
    ]


def get_nav_kb() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(keyboard=_nav_rows(), resize_keyboard=True)


def _chunk_rows(items: list[str], per_row: int = 1) -> list[list[KeyboardButton]]:
    rows = []
    for i in range(0, len(items), per_row):
        rows.append([KeyboardButton(text=x) for x in items[i:i + per_row]])
    return rows


def get_main_menu_kb(user_id: Optional[int] = None):
    """Adminga faqat admin tugmalari, oddiy foydalanuvchiga mijoz tugmalari ko'rsatiladi."""
    if user_id is not None and user_id in ADMIN_IDS:
        return get_admin_menu_kb()
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="📝 Anketa to'ldirish")],
            [KeyboardButton(text="📷 To'g'ri rasm talablari"), KeyboardButton(text="🛂 Pasport rasmi talablari")],
            [KeyboardButton(text=SUPPORT_BUTTON_TEXT)]
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
        keyboard=[[KeyboardButton(text=text)]] + _nav_rows(),
        resize_keyboard=True
    )


def get_gender_kb() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="Erkak"), KeyboardButton(text="Ayol")]] + _nav_rows(),
        resize_keyboard=True
    )


def get_country_kb() -> ReplyKeyboardMarkup:
    rows = _chunk_rows(COUNTRIES, per_row=2)
    rows.extend(_nav_rows())
    return ReplyKeyboardMarkup(keyboard=rows, resize_keyboard=True)


def get_region_kb() -> ReplyKeyboardMarkup:
    rows = [[KeyboardButton(text=r)] for r in REGIONS.keys()]
    rows.extend(_nav_rows())
    return ReplyKeyboardMarkup(keyboard=rows, resize_keyboard=True)


def get_district_kb(region: str) -> ReplyKeyboardMarkup:
    districts = REGIONS.get(region, [])
    if not districts:
        return get_nav_kb()
    rows = [[KeyboardButton(text=d)] for d in districts]
    rows.extend(_nav_rows())
    return ReplyKeyboardMarkup(keyboard=rows, resize_keyboard=True)


def get_education_kb() -> ReplyKeyboardMarkup:
    rows = [[KeyboardButton(text=e)] for e in EDUCATION_LEVELS]
    rows.extend(_nav_rows())
    return ReplyKeyboardMarkup(keyboard=rows, resize_keyboard=True)


def get_marital_status_kb() -> ReplyKeyboardMarkup:
    rows = [[KeyboardButton(text=m)] for m in MARITAL_STATUSES]
    rows.extend(_nav_rows())
    return ReplyKeyboardMarkup(keyboard=rows, resize_keyboard=True)


def get_children_count_kb() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="0 (Farzand yo'q)")],
            [KeyboardButton(text="1"), KeyboardButton(text="2"), KeyboardButton(text="3")],
            [KeyboardButton(text="4"), KeyboardButton(text="5"), KeyboardButton(text="6+")],
            *_nav_rows(),
        ],
        resize_keyboard=True
    )


def get_confirm_kb() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="✅ Ma'lumotlarni tasdiqlash va yuborish")],
            *_nav_rows(),
        ],
        resize_keyboard=True
    )


def get_admin_menu_kb():
    """Admin menyusi. ADMIN_HIDE_BUTTONS yoqilgan bo'lsa, eski tugmalar ham olib tashlanadi."""
    if ADMIN_HIDE_BUTTONS:
        return ReplyKeyboardRemove()
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="📊 Statistika")],
            [KeyboardButton(text="📥 Excel formatda yuklab olish")],
            [KeyboardButton(text="📨 Mijozga Confirmation Code yuborish")],
        ],
        resize_keyboard=True
    )


def get_admin_cancel_kb():
    return ReplyKeyboardRemove() if ADMIN_HIDE_BUTTONS else get_cancel_kb()


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
