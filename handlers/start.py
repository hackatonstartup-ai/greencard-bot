from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import CommandStart, Command
from aiogram.fsm.context import FSMContext
from database import add_or_update_user
from config import ADMIN_IDS, SUPPORT_PHONE, SUPPORT_TELEGRAM, SUPPORT_HOURS
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from keyboards import get_main_menu_kb, SUPPORT_BUTTON_TEXT

router = Router()

PREPARE_TEXT = (
    "📋 <b>ANKETA TO'LDIRISHDAN OLDIN QUYIDAGILARNI TAYYOR QILING</b>\n\n"
    "Anketa bir necha daqiqa oladi. To'xtab qolmaslik uchun oldindan quyidagilarni tayyorlab qo'ying:\n\n"
    "🛂 <b>1. Zagran pasport</b> (o'zingiz uchun)\n"
    "• Pasport raqami va amal qilish muddati\n"
    "• Pasportning rasm va ma'lumotlar joylashgan sahifasi rasmi (aniq, blik tushmagan, to'liq)\n"
    "• Ism va familiya pasportdagi kabi, lotin harflarida\n\n"
    "📸 <b>2. O'zingizning rasmingiz</b>\n"
    "• Oxirgi 6 oy ichida olingan, oppoq fonda, ko'zoynak va bosh kiyimsiz, filtrsiz\n"
    "• Imkon bo'lsa \"Fayl\" (File) ko'rinishida yuboring\n\n"
    "📝 <b>3. Shaxsiy ma'lumotlar</b>\n"
    "• Tug'ilgan sana, davlat, viloyat va tuman/shahar\n"
    "• Hozir yashayotgan davlat, viloyat, tuman va to'liq manzil (ko'cha, uy, xonadon)\n"
    "• Telefon raqam (faol) va email manzil\n"
    "• Ta'lim darajasi (tugatgan eng yuqori bosqich) va oilaviy holat\n\n"
    "💍 <b>4. Agar turmush qurgan bo'lsangiz</b>\n"
    "• Turmush o'rtog'ingizning ism-familiyasi, jinsi, tug'ilgan sanasi va joyi, ma'lumoti\n"
    "• Uning ham alohida rasmi (xuddi shu talablarda)\n\n"
    "👶 <b>5. Agar farzandlaringiz bo'lsa</b> (21 yoshga to'lmagan va turmush qurmagan)\n"
    "• Har bir farzandning ism-familiyasi, jinsi, tug'ilgan sanasi va joyi\n"
    "• Har bir farzandning alohida rasmi (xuddi shu talablarda)\n\n"
    "👇 Pastdagi tugmalar orqali pasport va rasm namunalarini ko'rib oling, so'ng «📝 Anketa to'ldirish» tugmasini bosing."
)


def get_examples_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🛂 Pasport rasmi namunasi", callback_data="example_passport")],
        [InlineKeyboardButton(text="📸 O'z rasmim namunasi", callback_data="example_photo")],
    ])

@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext):
    await state.clear()
    user = message.from_user
    await add_or_update_user(
        user_id=user.id,
        username=user.username,
        full_name=user.full_name
    )
    
    if user.id in ADMIN_IDS:
        await message.answer(
            "👑 <b>Admin paneli.</b>\nKerakli bo'limni tanlang (statistika uchun /admin):",
            reply_markup=get_main_menu_kb(user.id), parse_mode="HTML"
        )
        return

    welcome_text = (
        f"Assalomu alaykum, <b>{user.first_name}</b>!\n\n"
        "🇺🇸 <b>Green Card (DV Lottery) anketasini to'ldirish xizmatiga xush kelibsiz!</b>\n\n"
        "Biz sizning anketangizni AQSh elchixonasi talablari asosida, 100% xatosiz va ishonchli to'ldirib beramiz.\n\n"
        "Kerakli bo'limni tanlang:"
    )
    await message.answer(welcome_text, reply_markup=get_main_menu_kb(user.id), parse_mode="HTML")
    await message.answer(PREPARE_TEXT, reply_markup=get_examples_kb(), parse_mode="HTML")

@router.message(F.text == "❌ Bekor qilish")
@router.message(Command("cancel"))
async def cmd_cancel(message: Message, state: FSMContext):
    await state.clear()
    await message.answer(
        "Amal bekor qilindi. Bosh menyuga qaytdingiz.",
        reply_markup=get_main_menu_kb(message.from_user.id)
    )

@router.message(F.text == "🏠 Asosiy menyu")
async def cmd_main_menu(message: Message, state: FSMContext):
    await state.clear()
    await message.answer(
        "Asosiy menyu:",
        reply_markup=get_main_menu_kb(message.from_user.id)
    )

from pathlib import Path
from aiogram.types import FSInputFile

PHOTO_GUIDE_PATH = Path(__file__).resolve().parent.parent / "assets" / "photo_guide.jpg"

@router.callback_query(F.data == "example_photo")
async def example_photo_cb(callback: CallbackQuery):
    await callback.answer()
    await show_photo_requirements(callback.message)


@router.callback_query(F.data == "example_passport")
async def example_passport_cb(callback: CallbackQuery):
    await callback.answer()
    await show_passport_requirements(callback.message)


@router.message(F.text == "📷 To'g'ri rasm talablari")
async def show_photo_requirements(message: Message):
    text = (
        "📸 <b>GREEN CARD UCHUN RASMGA TUSHISH QOIDALARI:</b>\n\n"
        "Rasm eng muhim talab hisoblanadi. Agar rasm qoidalarga mos kelmasa, "
        "anketa yutsa ham elchixonada viza berilmaydi! Iltimos, quyidagi qoidalarga qat'iy amal qilib rasmga tushing:\n\n"
        "1. ⬜️ <b>Orqa fon:</b> Faqat oppoq va toza devor yoki mato fonida bo'lishi shart. Orqa fonda yoki yuzingizda soya (ten) bo'lmasligi kerak.\n"
        "2. 😐 <b>Yuz holati:</b> Kameraga to'g'ri qarab turasiz. Jilmayish, kulish yoki qovoq uyish mumkin emas (oddiy, jiddiy holatda). Ikkala ko'z aniq va ochiq bo'lishi shart.\n"
        "3. 👓 <b>Taqiqlar:</b> Ko'zoynak, shapka, kepka yoki boshqa bosh kiyimlarida tushish QAT'IYAN TAQIQLANADI (faqat diniy sabablarga ko'ra o'ralgan ro'mol ruxsat etiladi, lekin yuz to'liq ko'rinishi shart).\n"
        "4. ☀️ <b>Yorug'lik:</b> Rasm xira bo'lmasligi, yuzga yorug'lik bir xil tushishi kerak. Kunduzi, derazaga qarab rasmga tushishni tavsiya qilamiz. Sochlar yuzni to'sib qolmasligi kerak.\n"
        "5. 🚫 <b>Filtr va tahrirlash:</b> Telefonning o'z kamerasida, hech qanday filtr (Snapchat, Instagram maskalari) ishlatmasdan rasmga oling. Yuzdagi xol, ajin yoki chandiqlarni tozalash/tahrirlash (Photoshop) umuman mumkin emas.\n"
        "6. 📅 <b>Muddat:</b> Rasm oxirgi 6 oy ichida olingan bo'lishi shart. O'tgan yilgi anketadagi rasmni qayta ishlatish yutuqni avtomatik bekor qiladi.\n\n"
        "✅ <b>YUBORISH:</b> Rasm sifati buzilmasligi uchun uni Telegram orqali \"Rasm\" emas, <b>\"Fayl\" (File)</b> ko'rinishida yuboring! O'lchamlarini o'zimiz rasmiy talabga moslab kesib olamiz."
    )
    if PHOTO_GUIDE_PATH.exists():
        await message.answer_photo(
            photo=FSInputFile(str(PHOTO_GUIDE_PATH)),
            caption="📷 <b>Green Card namunaviy rasm qoidalari (To'g'ri va Noto'g'ri):</b>",
            parse_mode="HTML"
        )
    await message.answer(text, parse_mode="HTML")

PASSPORT_GUIDE_PATH = Path(__file__).resolve().parent.parent / "assets" / "passport_guide.jpg"

@router.message(F.text == "🛂 Pasport rasmi talablari")
async def show_passport_requirements(message: Message):
    text = (
        "🛂 <b>PASPORT NUSXASINI TO'G'RI YUBORISH QOIDALARI:</b>\n\n"
        "Anketangizdagi ism-familiya va tug'ilgan sanalar xatosiz kiritilishi uchun "
        "pasportingiz rasmini quyidagi qoidalarga amal qilib yuboring:\n\n"
        "1. 🔍 <b>Tiniqlik:</b> Pasportdagi barcha yozuvlar va raqamlar aniq o'qiladigan bo'lishi shart. Xira yoki titrab ketgan rasmlar qabul qilinmaydi.\n"
        "2. 💡 <b>Yorug'lik (Blik) tushmasligi:</b> Rasmga olayotganda chiroq yoki quyosh nuri pasport ustida yaraqlab (blik bo'lib) tushmasligiga e'tibor bering. Muhim yozuvlar ko'rinmay qolmasin.\n"
        "3. 📐 <b>To'liq ko'rinish:</b> Pasportning ma'lumotlar va rasm joylashgan sahifasini to'liq rasmga oling. Pasportning 4 ta cheti ham rasmga tushishi kerak.\n"
        "4. ✋ <b>Barmoqlar to'smasin:</b> Rasmga olayotganda barmoqlaringiz matnni yoki pasport seriyasi/raqamini to'sib qo'ymasin.\n"
        "5. 📂 <b>Yuborish:</b> Iloji bo'lsa, rasmni Telegram orqali sifatini yo'qotmaslik uchun <b>\"Fayl\" (File)</b> ko'rinishida yuboring.\n\n"
        "<i>Barcha ma'lumotlar faqatgina anketani to'g'ri to'ldirish uchun ishlatiladi.</i>"
    )
    if PASSPORT_GUIDE_PATH.exists():
        await message.answer_photo(
            photo=FSInputFile(str(PASSPORT_GUIDE_PATH)),
            caption="🛂 <b>Pasport nusxasini to'g'ri rasmga olish namunasi:</b>",
            parse_mode="HTML"
        )
    await message.answer(text, parse_mode="HTML")


@router.message(F.text == SUPPORT_BUTTON_TEXT)
async def show_support(message: Message):
    lines = ["☎️ <b>ALOQA MARKAZI</b>\n", "Savollaringiz bo'lsa yoki yordam kerak bo'lsa, biz bilan bog'laning. Sizga yordam berishdan xursandmiz! 🤝\n"]
    if SUPPORT_PHONE:
        lines.append(f"📞 <b>Telefon:</b> <code>{SUPPORT_PHONE}</code>")
    if SUPPORT_TELEGRAM:
        lines.append(f"💬 <b>Telegram:</b> @{SUPPORT_TELEGRAM}")
    lines.append(f"🕘 <b>Ish vaqti:</b> {SUPPORT_HOURS}")
    if not SUPPORT_PHONE and not SUPPORT_TELEGRAM:
        lines.append("\nAloqa ma'lumotlari tez orada qo'shiladi.")

    kb = None
    if SUPPORT_TELEGRAM:
        kb = InlineKeyboardMarkup(inline_keyboard=[[
            InlineKeyboardButton(text="💬 Operatorga yozish", url=f"https://t.me/{SUPPORT_TELEGRAM}")
        ]])
    await message.answer("\n".join(lines), reply_markup=kb, parse_mode="HTML")
