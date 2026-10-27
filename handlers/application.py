from __future__ import annotations

import re
from datetime import datetime
from pathlib import Path
from typing import Optional

from aiogram import Router, F, Bot
from aiogram.types import Message, CallbackQuery, FSInputFile
from aiogram.filters import StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.storage.base import StorageKey

from states import PaymentStates, ApplicationStates, SpouseStates, ChildStates, ConfirmStates
from keyboards import (
    get_main_menu_kb, get_cancel_kb, get_skip_kb, get_gender_kb,
    get_country_kb, get_region_kb, get_district_kb, get_education_kb,
    get_marital_status_kb, get_children_count_kb, get_confirm_kb,
    get_payment_admin_kb, get_nav_kb, BACK_TEXT, RESTART_TEXT
)
from database import (
    create_application, create_payment, resolve_payment,
    update_payment_status, has_approved_payment
)
from utils.locations import REGIONS, PHOTO_RULES
from utils.photo import validate_and_save_photo
from config import PHOTOS_DIR, ADMIN_IDS

router = Router()

PAYMENT_INSTRUCTIONS = (
    "Biz sizning anketangizni AQSh elchixonasi talablari asosida, "
    "100% xatosiz va ishonchli to'ldirib beramiz. Unutmang, anketadagi kichik xato ham "
    "yutuqni bekor qilishi mumkin, shuning uchun ishni ishonchli mutaxassisga topshiring.\n\n"
    "Umumiy xizmat narxi — <b>50 000 so'm</b>. 💳\n\n"
    "Ishni boshlashimiz uchun dastlab to'lovni amalga oshirishingizni so'raymiz:\n\n"
    "💳 <b>Karta:</b>\n"
    "<code>5614681013312222</code> AK\n"
    "<code>9860350143406659</code> AK\n\n"
    "🏦 <b>Bank:</b> Uzcard / Humo\n\n"
    "✅ <b>To'lov chekini (skrinshot) shu yerga rasm ko'rinishida yuboring.</b> "
    "To'lov tasdiqlanishi bilan darhol anketani to'ldirishni boshlaymiz.\n\n"
    "Ish yakunida sizga yutug'ingizni tekshirish uchun rasmiy "
    "<b>Tasdiqlash Raqami (Confirmation Number)</b> taqdim etiladi. Kutib qolaman! 🤝"
)


def is_valid_date(date_str: str) -> bool:
    try:
        parts = date_str.strip().replace("/", ".").replace("-", ".").split(".")
        if len(parts) != 3:
            return False
        day, month, year = int(parts[0]), int(parts[1]), int(parts[2])
        dt = datetime(year, month, day)
        now = datetime.now()
        if dt > now or year < 1920:
            return False
        return True
    except Exception:
        return False


def format_date(date_str: str) -> str:
    parts = date_str.strip().replace("/", ".").replace("-", ".").split(".")
    day, month, year = int(parts[0]), int(parts[1]), int(parts[2])
    return f"{day:02d}.{month:02d}.{year:04d}"


def is_valid_email(email: str) -> bool:
    pattern = r"^[\w\.-]+@[\w\.-]+\.\w+$"
    return bool(re.match(pattern, email.strip()))


# ==========================================
# 0. NAVIGATSIYA: ORQAGA / BOSHIDAN BOSHLASH
# ==========================================

QUESTIONNAIRE_STATES = StateFilter(ApplicationStates, SpouseStates, ChildStates, ConfirmStates)

STATE_BY_NAME = {
    st.state: st
    for group in (ApplicationStates, SpouseStates, ChildStates, ConfirmStates)
    for st in group.__all_states__
}

UZ_NAMES = ("O'zbekiston", "Uzbekistan", "🇺🇿 O'zbekiston")


async def goto(state: FSMContext, new_state) -> None:
    """Keyingi bosqichga o'tadi va joriy bosqichni 'orqaga' tarixiga yozib qo'yadi."""
    current = await state.get_state()
    data = await state.get_data()
    history = list(data.get("history", []))
    if current and current in STATE_BY_NAME:
        history.append(current)
    await state.update_data(history=history)
    await state.set_state(new_state)


async def ask_state(message: Message, state: FSMContext, st) -> None:
    """Berilgan bosqich savolini qayta beradi (orqaga qaytganda ishlatiladi)."""
    d = await state.get_data()
    n = get_nav_kb
    A, S, C = ApplicationStates, SpouseStates, ChildStates
    child_no = d.get("current_child_index", 1)

    def district_kb(country_key, region_key):
        if d.get(country_key) in UZ_NAMES:
            return get_district_kb(d.get(region_key, ""))
        return n()

    prompts = {
        A.last_name: ("Familiyangizni qayta kiriting (Lotin harflarida, masalan: <code>ALIEV</code>):", n()),
        A.first_name: ("Ismingizni qayta kiriting (Lotin harflarida, masalan: <code>VALI</code>):", n()),
        A.gender: ("Jinsingizni tanlang:", get_gender_kb()),
        A.birth_date: ("Tug'ilgan sanangizni kiriting (<code>kun.oy.yil</code>, masalan: <code>15.05.1994</code>):", n()),
        A.birth_country: ("Tug'ilgan davlatingizni tanlang:", get_country_kb()),
        A.birth_region: ("Tug'ilgan viloyatingizni tanlang:", get_region_kb()),
        A.birth_district: ("Tug'ilgan tuman/shahringizni kiriting yoki tanlang:", district_kb("birth_country", "birth_region")),
        A.passport_photo: ("🛂 Zagran pasportingiz rasmini qayta yuboring:", n()),
        A.photo: (f"{PHOTO_RULES}\n\n📸 Green Card fotosuratingizni qayta yuboring:", n()),
        A.live_country: ("Hozirda yashayotgan davlatingizni tanlang:", get_country_kb()),
        A.live_region: ("Hozirda yashayotgan viloyatingizni tanlang:", get_region_kb()),
        A.live_district: ("Hozirda yashayotgan tuman/shahringizni kiriting yoki tanlang:", district_kb("live_country", "live_region")),
        A.address_line1: ("Yashash manzilingizni kiriting (Ko'cha, uy raqami, xonadon):", n()),
        A.email: ("Email manzilingizni kiriting (yoki 'O'tkazib yuborish' ni bosing):", get_skip_kb()),
        A.phone_number: ("Telefon raqamingizni kiriting (masalan: <code>+998901234567</code>):", n()),
        A.education_level: ("Ta'lim darajangizni tanlang:", get_education_kb()),
        A.marital_status: ("Oilaviy holatingizni tanlang:", get_marital_status_kb()),
        A.children_count: ("21 yoshga to'lmagan, turmush qurmagan nechta farzandingiz bor?", get_children_count_kb()),
        S.last_name: ("Turmush o'rtog'ingizning familiyasini kiriting:", n()),
        S.first_name: ("Turmush o'rtog'ingizning ismini kiriting:", n()),
        S.gender: ("Turmush o'rtog'ingizning jinsini tanlang:", get_gender_kb()),
        S.birth_date: ("Turmush o'rtog'ingizning tug'ilgan sanasini kiriting (<code>kun.oy.yil</code>):", n()),
        S.birth_country: ("Turmush o'rtog'ingiz tug'ilgan davlatni tanlang:", get_country_kb()),
        S.birth_region: ("Turmush o'rtog'ingiz tug'ilgan viloyatni tanlang:", get_region_kb()),
        S.birth_district: ("Turmush o'rtog'ingiz tug'ilgan tuman/shahrni kiriting yoki tanlang:", district_kb("spouse_birth_country", "spouse_birth_region")),
        S.education_level: ("Turmush o'rtog'ingizning ma'lumot darajasini tanlang:", get_education_kb()),
        S.photo: ("📸 Turmush o'rtog'ingizning fotosuratini qayta yuboring:", n()),
        C.last_name: (f"👶 {child_no}-farzandning familiyasini kiriting:", n()),
        C.first_name: (f"{child_no}-farzandning ismini kiriting:", n()),
        C.gender: (f"{child_no}-farzandning jinsini tanlang:", get_gender_kb()),
        C.birth_date: (f"{child_no}-farzandning tug'ilgan sanasini kiriting (<code>kun.oy.yil</code>):", n()),
        C.birth_country: (f"{child_no}-farzand tug'ilgan davlatni tanlang:", get_country_kb()),
        C.birth_region: (f"{child_no}-farzand tug'ilgan viloyatni tanlang:", get_region_kb()),
        C.birth_district: (f"{child_no}-farzand tug'ilgan tuman/shahrni kiriting yoki tanlang:", district_kb("current_child_birth_country", "current_child_birth_region")),
        C.photo: (f"📸 {child_no}-farzandning fotosuratini qayta yuboring:", n()),
    }

    if st == ConfirmStates.confirm:
        await show_confirmation(message, state)
        return
    text, kb = prompts[st]
    await message.answer(f"⬅️ <b>Orqaga qaytdingiz.</b>\n\n{text}", reply_markup=kb, parse_mode="HTML")


@router.message(F.text == BACK_TEXT, QUESTIONNAIRE_STATES)
async def go_back(message: Message, state: FSMContext):
    data = await state.get_data()
    history = list(data.get("history", []))
    if not history:
        await message.answer(
            "Bu birinchi qadam, orqaga qaytib bo'lmaydi.\n"
            "Boshidan boshlash uchun «" + RESTART_TEXT + "» tugmasini bosing.",
            reply_markup=get_nav_kb()
        )
        return

    prev = STATE_BY_NAME[history.pop()]
    updates = {"history": history}

    # Farzand fotosiga qaytilsa — oxirgi saqlangan farzandni olib tashlaymiz,
    # foto qayta yuborilganda u yangidan yoziladi.
    if prev == ChildStates.photo:
        children = list(data.get("children", []))
        if children:
            last = children.pop()
            updates["children"] = children
            updates["current_child_index"] = last.get("child_index", len(children) + 1)

    await state.update_data(**updates)
    await state.set_state(prev)
    await ask_state(message, state, prev)


@router.message(F.text == RESTART_TEXT, QUESTIONNAIRE_STATES)
async def restart_questionnaire(message: Message, state: FSMContext):
    await message.answer("🔁 Anketa boshidan boshlandi. Avvalgi kiritilgan ma'lumotlar o'chirildi.")
    await begin_questionnaire(message, state)


# ==========================================
# 1. TO'LOV JARAYONI (PAYMENT FIRST)
# ==========================================

@router.message(F.text == "📝 Anketa to'ldirish")
async def start_with_payment(message: Message, state: FSMContext):
    user_id = message.from_user.id

    already_paid = await has_approved_payment(user_id)
    if already_paid:
        await begin_questionnaire(message, state)
        return

    await state.clear()
    await message.answer(PAYMENT_INSTRUCTIONS, reply_markup=get_cancel_kb(), parse_mode="HTML")
    await goto(state, PaymentStates.waiting_for_receipt)


@router.message(PaymentStates.waiting_for_receipt, F.photo | F.document)
async def process_payment_receipt(message: Message, state: FSMContext, bot: Bot):
    user_id = message.from_user.id
    timestamp = int(datetime.now().timestamp())
    file_id = message.photo[-1].file_id if message.photo else message.document.file_id

    file_info = await bot.get_file(file_id)
    file_bytes_io = await bot.download_file(file_info.file_path)
    file_bytes = file_bytes_io.read()

    save_filename = f"{user_id}_{timestamp}_receipt.jpg"
    save_path = PHOTOS_DIR / save_filename

    validate_and_save_photo(file_bytes, save_path)

    payment_id = await create_payment(user_id=user_id, receipt_photo=save_filename)
    await state.clear()

    await message.answer(
        "✅ <b>To'lov chekingiz adminga yuborildi!</b>\n\n"
        "Admin to'lovni tekshirib tasdiqlagach (odatda 5-10 daqiqa ichida), "
        "anketa to'ldirish avtomatik boshlanadi. Iltimos, kuting... ⏳",
        reply_markup=get_main_menu_kb(user_id),
        parse_mode="HTML"
    )

    admin_caption = (
        f"💳 <b>Yangi to'lov cheki keldi! (#{payment_id})</b>\n\n"
        f"👤 <b>Foydalanuvchi:</b> {message.from_user.full_name}\n"
        f"Username: @{message.from_user.username or 'yo_q'}\n"
        f"ID: <code>{user_id}</code>\n"
        f"Summa: <b>50 000 so'm</b>\n\n"
        "To'lovni tasdiqlaysizmi?"
    )

    for admin_id in ADMIN_IDS:
        try:
            await bot.send_photo(
                chat_id=admin_id,
                photo=FSInputFile(str(save_path)),
                caption=admin_caption,
                reply_markup=get_payment_admin_kb(payment_id, user_id),
                parse_mode="HTML"
            )
        except Exception as e:
            print(f"Failed to send receipt to admin {admin_id}: {e}")


def _parse_payment_callback(data: str) -> tuple[int, Optional[int]]:
    parts = data.split(":")
    payment_id = int(parts[1])
    user_id = int(parts[2]) if len(parts) >= 3 and parts[2].isdigit() else None
    return payment_id, user_id


def _user_id_from_caption(caption: Optional[str]) -> Optional[int]:
    if not caption:
        return None
    match = re.search(r"ID:\s*(\d+)", caption)
    return int(match.group(1)) if match else None


@router.callback_query(F.data.startswith("pay_approve:"))
async def approve_payment_cb(callback: CallbackQuery, bot: Bot, state: FSMContext):
    payment_id, user_id = _parse_payment_callback(callback.data)
    if user_id is None and callback.message:
        user_id = _user_id_from_caption(callback.message.caption)

    payment = await resolve_payment(payment_id, user_id)

    if not payment:
        await callback.answer("To'lov topilmadi!", show_alert=True)
        return

    await update_payment_status(payment["id"], "approved")
    target_user_id = payment["user_id"]

    if callback.message:
        await callback.message.edit_caption(
            caption=f"{callback.message.caption}\n\n✅ <b>To'lov tasdiqlandi!</b> (Admin: {callback.from_user.full_name})",
            reply_markup=None,
            parse_mode="HTML"
        )
    await callback.answer("To'lov tasdiqlandi!")

    try:
        user_msg = (
            "🎉 <b>To'lovingiz muvaffaqiyatli tasdiqlandi!</b>\n\n"
            "Endi Green Card anketangizni to'ldirishni boshlaymiz.\n\n"
            "1-qadam: <b>Familiyangizni</b> kiriting (Pasportingizdagi lotin harflarida, masalan: <code>ALIEV</code>):"
        )
        # Foydalanuvchining FSM holatini o'rnatamiz, toki familiya kiritganda qabul qilsin!
        user_state = FSMContext(
            storage=state.storage,
            key=StorageKey(bot_id=bot.id, chat_id=target_user_id, user_id=target_user_id)
        )
        await user_state.clear()
        await user_state.update_data(app_data={}, children=[])
        await user_state.set_state(ApplicationStates.last_name)

        await bot.send_message(chat_id=target_user_id, text=user_msg, reply_markup=get_nav_kb(), parse_mode="HTML")
    except Exception as e:
        print(f"Error messaging user {target_user_id}: {e}")


@router.callback_query(F.data.startswith("pay_reject:"))
async def reject_payment_cb(callback: CallbackQuery, bot: Bot):
    payment_id, user_id = _parse_payment_callback(callback.data)
    if user_id is None and callback.message:
        user_id = _user_id_from_caption(callback.message.caption)

    payment = await resolve_payment(payment_id, user_id)

    if not payment:
        await callback.answer("To'lov topilmadi!", show_alert=True)
        return

    await update_payment_status(payment["id"], "rejected")
    target_user_id = payment["user_id"]

    if callback.message:
        await callback.message.edit_caption(
            caption=f"{callback.message.caption}\n\n❌ <b>To'lov rad etildi!</b> (Admin: {callback.from_user.full_name})",
            reply_markup=None,
            parse_mode="HTML"
        )
    await callback.answer("To'lov rad etildi!")

    try:
        reject_msg = (
            "⚠️ <b>To'lov chekingiz tasdiqlanmadi.</b>\n\n"
            "Iltimos, haqiqiy to'lov chekini qayta yuboring yoki admin bilan bog'laning."
        )
        await bot.send_message(chat_id=target_user_id, text=reject_msg, reply_markup=get_main_menu_kb(target_user_id), parse_mode="HTML")
    except Exception as e:
        print(f"Error messaging user {target_user_id}: {e}")


# ==========================================
# 2. ANKETA TO'LDIRISH (QUESTIONNAIRE)
# ==========================================

async def begin_questionnaire(message: Message, state: FSMContext):
    await state.clear()
    await state.update_data(app_data={}, children=[], history=[])

    text = (
        "🇺🇸 <b>Green Card anketasini to'ldirishni boshlaymiz!</b>\n\n"
        "1-qadam: <b>Familiyangizni</b> kiriting (Pasportingizdagi lotin harflarida, masalan: <code>ALIEV</code>):"
    )
    await message.answer(text, reply_markup=get_nav_kb(), parse_mode="HTML")
    await goto(state, ApplicationStates.last_name)


@router.message(ApplicationStates.last_name, F.text)
async def process_last_name(message: Message, state: FSMContext):
    last_name = message.text.strip().upper()
    await state.update_data(last_name=last_name)

    text = f"Familiya: <b>{last_name}</b>\n\n2-qadam: <b>Ismingizni</b> kiriting (Lotin harflarida, masalan: <code>VALI</code>):"
    await message.answer(text, reply_markup=get_nav_kb(), parse_mode="HTML")
    await goto(state, ApplicationStates.first_name)


@router.message(ApplicationStates.first_name, F.text)
async def process_first_name(message: Message, state: FSMContext):
    first_name = message.text.strip().upper()
    await state.update_data(first_name=first_name)

    text = f"Ism: <b>{first_name}</b>\n\n3-qadam: <b>Jinsingizni</b> tanlang:"
    await message.answer(text, reply_markup=get_gender_kb(), parse_mode="HTML")
    await goto(state, ApplicationStates.gender)


@router.message(ApplicationStates.gender, F.text.in_(["Erkak", "Ayol", "Erkak (Male)", "Ayol (Female)"]))
async def process_gender(message: Message, state: FSMContext):
    gender = "Male" if "Erkak" in message.text else "Female"
    await state.update_data(gender=gender)

    text = (
        "4-qadam: <b>Tug'ilgan sanangizni</b> kiriting.\n"
        "Format: <code>kun.oy.yil</code> (Masalan: <code>15.05.1994</code>):"
    )
    await message.answer(text, reply_markup=get_nav_kb(), parse_mode="HTML")
    await goto(state, ApplicationStates.birth_date)


@router.message(ApplicationStates.birth_date, F.text)
async def process_birth_date(message: Message, state: FSMContext):
    if not is_valid_date(message.text):
        await message.answer(
            "⚠️ Iltimos, sanani kun.oy.yil formatida to'g'ri kiriting (Masalan: <code>20.08.1995</code>):",
            parse_mode="HTML"
        )
        return

    formatted = format_date(message.text)
    await state.update_data(birth_date=formatted)

    text = f"Tug'ilgan sana: <b>{formatted}</b>\n\n5-qadam: <b>Tug'ilgan davlatingizni</b> tanlang:"
    await message.answer(text, reply_markup=get_country_kb(), parse_mode="HTML")
    await goto(state, ApplicationStates.birth_country)


@router.message(ApplicationStates.birth_country, F.text)
async def process_birth_country(message: Message, state: FSMContext):
    country = message.text.strip()
    await state.update_data(birth_country=country, birth_region="")

    if country in ("O'zbekiston", "Uzbekistan", "🇺🇿 O'zbekiston"):
        text = "6-qadam: <b>Tug'ilgan viloyatingizni</b> tanlang:"
        await message.answer(text, reply_markup=get_region_kb(), parse_mode="HTML")
        await goto(state, ApplicationStates.birth_region)
    else:
        text = "6-qadam: <b>Tug'ilgan shahar yoki viloyat nomini</b> kiriting:"
        await message.answer(text, reply_markup=get_nav_kb(), parse_mode="HTML")
        await goto(state, ApplicationStates.birth_district)


@router.message(ApplicationStates.birth_region, F.text)
async def process_birth_region(message: Message, state: FSMContext):
    region = message.text.strip()
    if region not in REGIONS:
        await message.answer("Iltimos, tugmalardan viloyatni tanlang:")
        return

    await state.update_data(birth_region=region)
    text = f"<b>{region}</b> tanlandi.\n\n7-qadam: <b>Tug'ilgan tuman yoki shahringizni</b> tanlang:"
    await message.answer(text, reply_markup=get_district_kb(region), parse_mode="HTML")
    await goto(state, ApplicationStates.birth_district)


@router.message(ApplicationStates.birth_district, F.text)
async def process_birth_district(message: Message, state: FSMContext):
    district = message.text.strip()
    await state.update_data(
        birth_district=district,
        birth_city=district,
        passport_number="",
        passport_expiry=""
    )

    text = (
        "8-qadam: 🛂 <b>Xorijga chiqish (Zagran) pasportingiz rasmini yuboring:</b>\n\n"
        "<i>(Asosiy ma'lumotlar sahifasi to'liq, yorug' va aniq ko'rinsin. Ushbu qadam majburiy!)</i>"
    )
    await message.answer(text, reply_markup=get_nav_kb(), parse_mode="HTML")
    await goto(state, ApplicationStates.passport_photo)


@router.message(ApplicationStates.passport_photo, F.photo | F.document)
async def process_passport_photo(message: Message, state: FSMContext, bot: Bot):
    user_id = message.from_user.id
    timestamp = int(datetime.now().timestamp())
    file_id = message.photo[-1].file_id if message.photo else message.document.file_id

    file_info = await bot.get_file(file_id)
    file_bytes_io = await bot.download_file(file_info.file_path)
    file_bytes = file_bytes_io.read()

    save_filename = f"{user_id}_{timestamp}_passport.jpg"
    save_path = PHOTOS_DIR / save_filename

    validate_and_save_photo(file_bytes, save_path)
    await state.update_data(passport_photo_path=save_filename)

    text = (
        f"{PHOTO_RULES}\n\n"
        "9-qadam: 📸 <b>Green Card fotosuratingizni yuboring:</b>"
    )
    await message.answer(text, reply_markup=get_nav_kb(), parse_mode="HTML")
    await goto(state, ApplicationStates.photo)


@router.message(ApplicationStates.passport_photo)
async def invalid_passport_photo(message: Message):
    await message.answer(
        "⚠️ <b>Iltimos, xorijga chiqish (zagran) pasportingiz rasmini rasm yoki fayl ko'rinishida yuboring:</b>\n"
        "<i>(Ushbu qadam majburiy)</i>",
        reply_markup=get_nav_kb(),
        parse_mode="HTML"
    )


@router.message(ApplicationStates.photo, F.photo | F.document)
async def process_photo(message: Message, state: FSMContext, bot: Bot):
    user_id = message.from_user.id
    timestamp = int(datetime.now().timestamp())
    file_id = message.photo[-1].file_id if message.photo else message.document.file_id

    file_info = await bot.get_file(file_id)
    file_bytes_io = await bot.download_file(file_info.file_path)
    file_bytes = file_bytes_io.read()

    save_filename = f"{user_id}_{timestamp}_main.jpg"
    save_path = PHOTOS_DIR / save_filename

    validate_and_save_photo(file_bytes, save_path)
    await state.update_data(photo_path=save_filename)

    text = "✅ Rasm qabul qilindi!\n\n10-qadam: <b>Hozirda yashayotgan davlatingizni tanlang:</b>"
    await message.answer(text, reply_markup=get_country_kb(), parse_mode="HTML")
    await goto(state, ApplicationStates.live_country)


@router.message(ApplicationStates.live_country, F.text)
async def process_live_country(message: Message, state: FSMContext):
    country = message.text.strip()
    await state.update_data(live_country=country, country=country, live_region="", district_state="")

    if country in ("O'zbekiston", "Uzbekistan", "🇺🇿 O'zbekiston"):
        text = "11-qadam: <b>Hozirda yashayotgan viloyatingizni tanlang:</b>"
        await message.answer(text, reply_markup=get_region_kb(), parse_mode="HTML")
        await goto(state, ApplicationStates.live_region)
    else:
        text = "11-qadam: <b>Hozirda yashayotgan shahar/viloyatingiz nomini kiriting:</b>"
        await message.answer(text, reply_markup=get_nav_kb(), parse_mode="HTML")
        await goto(state, ApplicationStates.live_district)


@router.message(ApplicationStates.live_region, F.text)
async def process_live_region(message: Message, state: FSMContext):
    region = message.text.strip()
    if region not in REGIONS:
        await message.answer("Iltimos, tugmalardan viloyatni tanlang:")
        return

    await state.update_data(live_region=region, district_state=region)
    text = f"<b>{region}</b> tanlandi.\n\n12-qadam: <b>Hozirda yashayotgan tumaningizni tanlang:</b>"
    await message.answer(text, reply_markup=get_district_kb(region), parse_mode="HTML")
    await goto(state, ApplicationStates.live_district)


@router.message(ApplicationStates.live_district, F.text)
async def process_live_district(message: Message, state: FSMContext):
    district = message.text.strip()
    await state.update_data(live_district=district, city=district)

    text = (
        "13-qadam: <b>Yashash manzilingizni kiriting</b> (Ko'cha, uy raqami, xonadon):\n"
        "Masalan: <code>Amir Temur ko'chasi, 45-uy</code>"
    )
    await message.answer(text, reply_markup=get_nav_kb(), parse_mode="HTML")
    await goto(state, ApplicationStates.address_line1)


@router.message(ApplicationStates.address_line1, F.text)
async def process_address(message: Message, state: FSMContext):
    address = message.text.strip()
    await state.update_data(address_line1=address)

    text = (
        "14-qadam: <b>Elektron pochta (Email) manzilingizni kiriting:</b>\n"
        "<i>(Yoki 'O'tkazib yuborish' tugmasini bosing):</i>"
    )
    await message.answer(text, reply_markup=get_skip_kb(), parse_mode="HTML")
    await goto(state, ApplicationStates.email)


@router.message(ApplicationStates.email, F.text)
async def process_email(message: Message, state: FSMContext):
    if "O'tkazib yuborish" in message.text:
        email = ""
    else:
        email = message.text.strip().lower()
        if not is_valid_email(email):
            await message.answer("⚠️ Noto'g'ri email formati! Iltimos, to'g'ri email kiriting yoki 'O'tkazib yuborish' bosing:", parse_mode="HTML")
            return

    await state.update_data(email=email)

    text = (
        "15-qadam: <b>Telefon raqamingizni kiriting:</b>\n"
        "Masalan: <code>+998901234567</code>"
    )
    await message.answer(text, reply_markup=get_nav_kb(), parse_mode="HTML")
    await goto(state, ApplicationStates.phone_number)


@router.message(ApplicationStates.phone_number, F.text)
async def process_phone_number(message: Message, state: FSMContext):
    phone = message.text.strip()
    await state.update_data(phone_number=phone)

    text = "16-qadam: <b>Ma'lumotingiz (Ta'lim darajangizni tanlang):</b>"
    await message.answer(text, reply_markup=get_education_kb(), parse_mode="HTML")
    await goto(state, ApplicationStates.education_level)


@router.message(ApplicationStates.education_level, F.text)
async def process_education_level(message: Message, state: FSMContext):
    await state.update_data(education_level=message.text.strip())

    text = "17-qadam: <b>Oilaviy holatingizni tanlang:</b>"
    await message.answer(text, reply_markup=get_marital_status_kb(), parse_mode="HTML")
    await goto(state, ApplicationStates.marital_status)


@router.message(ApplicationStates.marital_status, F.text)
async def process_marital_status(message: Message, state: FSMContext):
    status_text = message.text.strip()
    await state.update_data(marital_status=status_text, spouse=None)

    if "Uylangan" in status_text or "Turmush qurgan" in status_text or "turmushga chiqgan" in status_text:
        text = (
            "💍 <b>Turmush o'rtog'ingiz ma'lumotlari:</b>\n\n"
            "Turmush o'rtog'ingizning <b>Familiyasini</b> kiriting (Lotin harflarida, masalan: <code>ALIEVA</code>):"
        )
        await message.answer(text, reply_markup=get_nav_kb(), parse_mode="HTML")
        await goto(state, SpouseStates.last_name)
    else:
        text = (
            "👶 <b>Farzandlar:</b>\n\n"
            "21 yoshga to'lmagan, turmush qurmagan nechta farzandingiz bor?\n"
            "<i>(Agar farzandingiz bo'lmasa, '0' tugmasini bosing):</i>"
        )
        await message.answer(text, reply_markup=get_children_count_kb(), parse_mode="HTML")
        await goto(state, ApplicationStates.children_count)


# ==========================================
# 3. TURMUSH O'RTOG'I (SPOUSE)
# ==========================================

@router.message(SpouseStates.last_name, F.text)
async def process_spouse_last_name(message: Message, state: FSMContext):
    last_name = message.text.strip().upper()
    await state.update_data(spouse_last_name=last_name)

    text = "Turmush o'rtog'ingizning <b>Ismini</b> kiriting (Lotin harflarida, masalan: <code>NIGORA</code>):"
    await message.answer(text, reply_markup=get_nav_kb(), parse_mode="HTML")
    await goto(state, SpouseStates.first_name)


@router.message(SpouseStates.first_name, F.text)
async def process_spouse_first_name(message: Message, state: FSMContext):
    first_name = message.text.strip().upper()
    await state.update_data(spouse_first_name=first_name)

    text = "Turmush o'rtog'ingizning <b>Jinsini</b> tanlang:"
    await message.answer(text, reply_markup=get_gender_kb(), parse_mode="HTML")
    await goto(state, SpouseStates.gender)


@router.message(SpouseStates.gender, F.text.in_(["Erkak", "Ayol", "Erkak (Male)", "Ayol (Female)"]))
async def process_spouse_gender(message: Message, state: FSMContext):
    gender = "Male" if "Erkak" in message.text else "Female"
    await state.update_data(spouse_gender=gender)

    text = (
        "Turmush o'rtog'ingizning <b>Tug'ilgan sanasini</b> kiriting.\n"
        "Format: <code>kun.oy.yil</code> (Masalan: <code>10.12.1996</code>):"
    )
    await message.answer(text, reply_markup=get_nav_kb(), parse_mode="HTML")
    await goto(state, SpouseStates.birth_date)


@router.message(SpouseStates.birth_date, F.text)
async def process_spouse_birth_date(message: Message, state: FSMContext):
    if not is_valid_date(message.text):
        await message.answer("⚠️ Iltimos, sanani kun.oy.yil formatida to'g'ri kiriting (Masalan: <code>12.06.1996</code>):", parse_mode="HTML")
        return

    formatted = format_date(message.text)
    await state.update_data(spouse_birth_date=formatted)

    text = "Turmush o'rtog'ingiz <b>Tug'ilgan davlatini</b> tanlang:"
    await message.answer(text, reply_markup=get_country_kb(), parse_mode="HTML")
    await goto(state, SpouseStates.birth_country)


@router.message(SpouseStates.birth_country, F.text)
async def process_spouse_birth_country(message: Message, state: FSMContext):
    country = message.text.strip()
    await state.update_data(spouse_birth_country=country, spouse_birth_region="")

    if country in ("O'zbekiston", "Uzbekistan", "🇺🇿 O'zbekiston"):
        text = "Turmush o'rtog'ingiz <b>Tug'ilgan viloyatini</b> tanlang:"
        await message.answer(text, reply_markup=get_region_kb(), parse_mode="HTML")
        await goto(state, SpouseStates.birth_region)
    else:
        text = "Turmush o'rtog'ingiz <b>Tug'ilgan shahar/tuman nomini</b> kiriting:"
        await message.answer(text, reply_markup=get_nav_kb(), parse_mode="HTML")
        await goto(state, SpouseStates.birth_district)


@router.message(SpouseStates.birth_region, F.text)
async def process_spouse_birth_region(message: Message, state: FSMContext):
    region = message.text.strip()
    if region not in REGIONS:
        await message.answer("Iltimos, tugmalardan viloyatni tanlang:")
        return

    await state.update_data(spouse_birth_region=region)
    text = f"<b>{region}</b> tanlandi.\n\nTurmush o'rtog'ingiz <b>Tug'ilgan tuman yoki shahri:</b>"
    await message.answer(text, reply_markup=get_district_kb(region), parse_mode="HTML")
    await goto(state, SpouseStates.birth_district)


@router.message(SpouseStates.birth_district, F.text)
async def process_spouse_birth_district(message: Message, state: FSMContext):
    district = message.text.strip()
    await state.update_data(spouse_birth_district=district, spouse_birth_city=district)

    text = "Turmush o'rtog'ingizning <b>Ma'lumot darajasini</b> tanlang:"
    await message.answer(text, reply_markup=get_education_kb(), parse_mode="HTML")
    await goto(state, SpouseStates.education_level)


@router.message(SpouseStates.education_level, F.text)
async def process_spouse_education(message: Message, state: FSMContext):
    await state.update_data(spouse_education_level=message.text.strip())

    text = "📸 <b>Turmush o'rtog'ingizning Green Card fotosuratini yuboring:</b>"
    await message.answer(text, reply_markup=get_nav_kb(), parse_mode="HTML")
    await goto(state, SpouseStates.photo)


@router.message(SpouseStates.photo, F.photo | F.document)
async def process_spouse_photo(message: Message, state: FSMContext, bot: Bot):
    user_id = message.from_user.id
    timestamp = int(datetime.now().timestamp())
    file_id = message.photo[-1].file_id if message.photo else message.document.file_id

    file_info = await bot.get_file(file_id)
    file_bytes_io = await bot.download_file(file_info.file_path)
    file_bytes = file_bytes_io.read()

    save_filename = f"{user_id}_{timestamp}_spouse.jpg"
    save_path = PHOTOS_DIR / save_filename

    validate_and_save_photo(file_bytes, save_path)

    data = await state.get_data()
    spouse_data = {
        "last_name": data.get("spouse_last_name"),
        "first_name": data.get("spouse_first_name"),
        "middle_name": "",
        "birth_date": data.get("spouse_birth_date"),
        "gender": data.get("spouse_gender"),
        "birth_region": data.get("spouse_birth_region", ""),
        "birth_city": data.get("spouse_birth_city", ""),
        "birth_country": data.get("spouse_birth_country"),
        "education_level": data.get("spouse_education_level", ""),
        "photo_path": save_filename
    }
    await state.update_data(spouse=spouse_data)

    text = (
        "✅ Turmush o'rtog'ingiz surati qabul qilindi!\n\n"
        "👶 <b>Farzandlar:</b>\n"
        "21 yoshga to'lmagan, turmush qurmagan nechta farzandingiz bor?\n"
        "<i>(Agar farzand bo'lmasa, '0' tugmasini bosing):</i>"
    )
    await message.answer(text, reply_markup=get_children_count_kb(), parse_mode="HTML")
    await goto(state, ApplicationStates.children_count)


# ==========================================
# 4. FARZANDLAR (CHILDREN)
# ==========================================

@router.message(ApplicationStates.children_count, F.text)
async def process_children_count(message: Message, state: FSMContext):
    raw_text = message.text.strip()
    if "0" in raw_text:
        count = 0
    elif raw_text.isdigit():
        count = int(raw_text)
    elif "6+" in raw_text:
        count = 6
    else:
        await message.answer("Iltimos, pastdagi tugmalardan birini tanlang:")
        return

    await state.update_data(children_count=count, total_children=count, current_child_index=1, children=[])

    if count == 0:
        await show_confirmation(message, state)
    else:
        await ask_child_info(message, state, child_num=1)


async def ask_child_info(message: Message, state: FSMContext, child_num: int):
    text = (
        f"👶 <b>{child_num}-farzand ma'lumotlari:</b>\n\n"
        f"Farzandingizning <b>Familiyasini</b> kiriting (Lotin harflarida, masalan: <code>ALIEV</code>):"
    )
    await message.answer(text, reply_markup=get_nav_kb(), parse_mode="HTML")
    await goto(state, ChildStates.last_name)


@router.message(ChildStates.last_name, F.text)
async def process_child_last_name(message: Message, state: FSMContext):
    last_name = message.text.strip().upper()
    await state.update_data(current_child_last_name=last_name)

    text = "Farzandingizning <b>Ismini</b> kiriting (Lotin harflarida, masalan: <code>BEHZOD</code>):"
    await message.answer(text, reply_markup=get_nav_kb(), parse_mode="HTML")
    await goto(state, ChildStates.first_name)


@router.message(ChildStates.first_name, F.text)
async def process_child_first_name(message: Message, state: FSMContext):
    first_name = message.text.strip().upper()
    await state.update_data(current_child_first_name=first_name)

    text = "Farzandingizning <b>Jinsini</b> tanlang:"
    await message.answer(text, reply_markup=get_gender_kb(), parse_mode="HTML")
    await goto(state, ChildStates.gender)


@router.message(ChildStates.gender, F.text.in_(["Erkak", "Ayol", "Erkak (Male)", "Ayol (Female)"]))
async def process_child_gender(message: Message, state: FSMContext):
    gender = "Male" if "Erkak" in message.text else "Female"
    await state.update_data(current_child_gender=gender)

    text = (
        "Farzandingizning <b>Tug'ilgan sanasini</b> kiriting.\n"
        "Format: <code>kun.oy.yil</code> (Masalan: <code>01.06.2018</code>):"
    )
    await message.answer(text, reply_markup=get_nav_kb(), parse_mode="HTML")
    await goto(state, ChildStates.birth_date)


@router.message(ChildStates.birth_date, F.text)
async def process_child_birth_date(message: Message, state: FSMContext):
    if not is_valid_date(message.text):
        await message.answer("⚠️ Iltimos, sanani kun.oy.yil formatida to'g'ri kiriting (Masalan: <code>15.03.2015</code>):", parse_mode="HTML")
        return

    formatted = format_date(message.text)
    await state.update_data(current_child_birth_date=formatted)

    text = "Farzandingiz <b>Tug'ilgan davlatini</b> tanlang:"
    await message.answer(text, reply_markup=get_country_kb(), parse_mode="HTML")
    await goto(state, ChildStates.birth_country)


@router.message(ChildStates.birth_country, F.text)
async def process_child_birth_country(message: Message, state: FSMContext):
    country = message.text.strip()
    await state.update_data(current_child_birth_country=country, current_child_birth_region="")

    if country in ("O'zbekiston", "Uzbekistan", "🇺🇿 O'zbekiston"):
        text = "Farzandingiz <b>Tug'ilgan viloyatini</b> tanlang:"
        await message.answer(text, reply_markup=get_region_kb(), parse_mode="HTML")
        await goto(state, ChildStates.birth_region)
    else:
        text = "Farzandingiz <b>Tug'ilgan shahar/tuman nomini</b> kiriting:"
        await message.answer(text, reply_markup=get_nav_kb(), parse_mode="HTML")
        await goto(state, ChildStates.birth_district)


@router.message(ChildStates.birth_region, F.text)
async def process_child_birth_region(message: Message, state: FSMContext):
    region = message.text.strip()
    if region not in REGIONS:
        await message.answer("Iltimos, tugmalardan viloyatni tanlang:")
        return

    await state.update_data(current_child_birth_region=region)
    text = f"<b>{region}</b> tanlandi.\n\nFarzandingiz <b>Tug'ilgan tuman yoki shahri:</b>"
    await message.answer(text, reply_markup=get_district_kb(region), parse_mode="HTML")
    await goto(state, ChildStates.birth_district)


@router.message(ChildStates.birth_district, F.text)
async def process_child_birth_district(message: Message, state: FSMContext):
    district = message.text.strip()
    await state.update_data(current_child_birth_district=district, current_child_birth_city=district)

    text = "📸 <b>Farzandingizning Green Card fotosuratini yuboring:</b>"
    await message.answer(text, reply_markup=get_nav_kb(), parse_mode="HTML")
    await goto(state, ChildStates.photo)


@router.message(ChildStates.photo, F.photo | F.document)
async def process_child_photo(message: Message, state: FSMContext, bot: Bot):
    user_id = message.from_user.id
    timestamp = int(datetime.now().timestamp())
    file_id = message.photo[-1].file_id if message.photo else message.document.file_id

    file_info = await bot.get_file(file_id)
    file_bytes_io = await bot.download_file(file_info.file_path)
    file_bytes = file_bytes_io.read()

    data = await state.get_data()
    curr_idx = data.get("current_child_index", 1)

    save_filename = f"{user_id}_{timestamp}_child_{curr_idx}.jpg"
    save_path = PHOTOS_DIR / save_filename

    validate_and_save_photo(file_bytes, save_path)

    child_data = {
        "child_index": curr_idx,
        "last_name": data.get("current_child_last_name"),
        "first_name": data.get("current_child_first_name"),
        "middle_name": "",
        "birth_date": data.get("current_child_birth_date"),
        "gender": data.get("current_child_gender"),
        "birth_region": data.get("current_child_birth_region", ""),
        "birth_city": data.get("current_child_birth_city", ""),
        "birth_country": data.get("current_child_birth_country"),
        "photo_path": save_filename
    }

    children = data.get("children", [])
    children.append(child_data)
    await state.update_data(children=children)

    total = data.get("total_children", 1)
    if curr_idx < total:
        next_idx = curr_idx + 1
        await state.update_data(current_child_index=next_idx)
        await ask_child_info(message, state, next_idx)
    else:
        await show_confirmation(message, state)


# ==========================================
# 5. YAKUNIY TASDIQLASH (CONFIRMATION)
# ==========================================

async def show_confirmation(message: Message, state: FSMContext):
    data = await state.get_data()

    birth_place = f"{data.get('birth_region', '')} {data.get('birth_district', '')}".strip()
    live_place = f"{data.get('live_region', '')} {data.get('live_district', '')} {data.get('address_line1', '')}".strip()

    summary = (
        "📋 <b>ANKETA MA'LUMOTLARI TEKSHIRUVI</b>\n\n"
        "👤 <b>Asosiy arizachi:</b>\n"
        f"• F.I: {data.get('last_name')} {data.get('first_name')}\n"
        f"• Jinsi: {data.get('gender')}\n"
        f"• Tug'ilgan sana: {data.get('birth_date')}\n"
        f"• Tug'ilgan joyi: {birth_place}, {data.get('birth_country')}\n"
        f"• Pasport seriya: {data.get('passport_number') or 'Kiritilmagan'}\n"
        f"• Yashash manzili: {live_place}, {data.get('live_country')}\n"
        f"• Tel / Email: {data.get('phone_number')} | {data.get('email') or 'Kiritilmagan'}\n"
        f"• Ta'lim: {data.get('education_level')}\n"
        f"• Oilaviy holati: {data.get('marital_status')}\n"
        f"• Farzandlar soni: {data.get('children_count', 0)}\n"
    )

    spouse = data.get("spouse")
    if spouse:
        sp_birth = f"{spouse.get('birth_region', '')} {spouse.get('birth_city', '')}".strip()
        summary += (
            f"\n💍 <b>Turmush o'rtog'i:</b>\n"
            f"• F.I: {spouse.get('last_name')} {spouse.get('first_name')}\n"
            f"• Tug'ilgan sana: {spouse.get('birth_date')}\n"
            f"• Tug'ilgan joyi: {sp_birth}, {spouse.get('birth_country')}\n"
            f"• Ta'lim darajasi: {spouse.get('education_level', '')}\n"
        )

    children = data.get("children", [])
    if children:
        summary += "\n👶 <b>Farzandlar:</b>\n"
        for ch in children:
            ch_birth = f"{ch.get('birth_region', '')} {ch.get('birth_city', '')}".strip()
            summary += (
                f"• #{ch.get('child_index')}: {ch.get('last_name')} {ch.get('first_name')} | "
                f"{ch.get('birth_date')} | {ch_birth}\n"
            )

    summary += "\n⚠️ <b>Barcha ma'lumotlar to'g'ri kiritilganligiga ishonch hosil qiling!</b>"

    await message.answer(summary, reply_markup=get_confirm_kb(), parse_mode="HTML")
    await goto(state, ConfirmStates.confirm)


@router.message(ConfirmStates.confirm, F.text == "✅ Ma'lumotlarni tasdiqlash va yuborish")
async def process_confirm(message: Message, state: FSMContext, bot: Bot):
    data = await state.get_data()
    user_id = message.from_user.id

    app_id = await create_application(user_id=user_id, app_data=data)
    await state.clear()

    success_text = (
        f"🎉 <b>Arizangiz muvaffaqiyatli qabul qilindi!</b>\n\n"
        f"Sizning anketa raqamingiz: <b>#{app_id}</b>\n\n"
        "Mutaxassisimiz anketangizni rasmiy DV dasturi tizimiga kiritadi va "
        "natija (Confirmation Code) ushbu bot orqali sizga taqdim etiladi.\n\n"
        "Xizmatingizdan mamnunmiz! Omad tilaymiz! 🇺🇸"
    )
    await message.answer(success_text, reply_markup=get_main_menu_kb(user_id), parse_mode="HTML")

    birth_place = f"{data.get('birth_region', '')} {data.get('birth_district', '')}".strip()
    passport_val = data.get('passport_number') or "Yo'q"
    email_val = data.get('email') or "Yo'q"
    admin_alert = (
        f"🆕 <b>Yangi anketa kelib tushdi! #ID: {app_id}</b>\n\n"
        f"👤 <b>Arizachi:</b> {data.get('last_name')} {data.get('first_name')}\n"
        f"📅 <b>Tug'ilgan:</b> {data.get('birth_date')} ({birth_place})\n"
        f"🛂 <b>Pasport:</b> {passport_val}\n"
        f"📞 <b>Tel:</b> {data.get('phone_number')}\n"
        f"📧 <b>Email:</b> {email_val}\n"
        f"🎓 <b>Ta'lim:</b> {data.get('education_level')}\n"
        f"💍 <b>Oila:</b> {data.get('marital_status')}\n"
        f"👶 <b>Farzandlar:</b> {data.get('children_count', 0)} ta\n"
        f"Telegram: @{message.from_user.username or 'yo_q'} (ID: {user_id})\n\n"
        "<i>Barcha anketalarni Excel formatda yuklab olish uchun /admin buyrug'idan foydalaning.</i>"
    )

    main_photo_file = PHOTOS_DIR / data.get("photo_path") if data.get("photo_path") else None
    passport_photo_file = PHOTOS_DIR / data.get("passport_photo_path") if data.get("passport_photo_path") else None

    for admin_id in ADMIN_IDS:
        try:
            if main_photo_file and main_photo_file.exists():
                await bot.send_photo(
                    chat_id=admin_id,
                    photo=FSInputFile(str(main_photo_file)),
                    caption=admin_alert,
                    parse_mode="HTML"
                )
            else:
                await bot.send_message(
                    chat_id=admin_id,
                    text=admin_alert,
                    parse_mode="HTML"
                )
            if passport_photo_file and passport_photo_file.exists():
                await bot.send_photo(
                    chat_id=admin_id,
                    photo=FSInputFile(str(passport_photo_file)),
                    caption=f"🛂 #{app_id}-anketa uchun PASPORT ({data.get('last_name')} {data.get('first_name')})",
                    parse_mode="HTML"
                )
        except Exception as e:
            print(f"Failed to notify admin {admin_id}: {e}")


@router.message(ConfirmStates.confirm, F.text == "🔄 Qaytadan to'ldirish")
async def process_restart(message: Message, state: FSMContext):
    await state.clear()
    await begin_questionnaire(message, state)
