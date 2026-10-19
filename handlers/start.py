from aiogram import Router, F
from aiogram.types import Message
from aiogram.filters import CommandStart, Command
from aiogram.fsm.context import FSMContext
from database import add_or_update_user
from keyboards import get_main_menu_kb

router = Router()

@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext):
    await state.clear()
    user = message.from_user
    await add_or_update_user(
        user_id=user.id,
        username=user.username,
        full_name=user.full_name
    )
    
    welcome_text = (
        f"Assalomu alaykum, <b>{user.first_name}</b>!\n\n"
        "🇺🇸 <b>Green Card (DV Lottery) anketasini to'ldirish xizmatiga xush kelibsiz!</b>\n\n"
        "Biz sizning anketangizni AQSh elchixonasi talablari asosida, 100% xatosiz va ishonchli to'ldirib beramiz.\n\n"
        "Kerakli bo'limni tanlang:"
    )
    await message.answer(welcome_text, reply_markup=get_main_menu_kb(), parse_mode="HTML")

@router.message(F.text == "❌ Bekor qilish")
@router.message(Command("cancel"))
async def cmd_cancel(message: Message, state: FSMContext):
    await state.clear()
    await message.answer(
        "Amal bekor qilindi. Bosh menyuga qaytdingiz.",
        reply_markup=get_main_menu_kb()
    )

@router.message(F.text == "🏠 Asosiy menyu")
async def cmd_main_menu(message: Message, state: FSMContext):
    await state.clear()
    await message.answer(
        "Asosiy menyu:",
        reply_markup=get_main_menu_kb()
    )

from pathlib import Path
from aiogram.types import FSInputFile

PHOTO_GUIDE_PATH = Path(__file__).resolve().parent.parent / "assets" / "photo_guide.jpg"

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
