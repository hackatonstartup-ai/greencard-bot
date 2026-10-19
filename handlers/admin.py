from datetime import datetime
from pathlib import Path
from aiogram import Router, F, Bot
from aiogram.types import Message, FSInputFile
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext

from config import ADMIN_IDS, EXPORTS_DIR
from database import get_stats, get_all_applications, get_application, update_confirmation_code
from keyboards import get_admin_menu_kb, get_main_menu_kb, get_cancel_kb
from states import AdminStates
from utils.excel import export_applications_to_excel

router = Router()

def is_admin(user_id: int) -> bool:
    return user_id in ADMIN_IDS

@router.message(Command("admin"))
async def cmd_admin(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        await message.answer("Sizda admin huquqlari mavjud emas!")
        return

    await state.clear()
    stats = await get_stats()
    text = (
        "👑 <b>Admin boshqaruv paneliga xush kelibsiz!</b>\n\n"
        "📊 <b>Hozirgi holat:</b>\n"
        f"• Jami arizalar: <b>{stats['total_apps']}</b> ta\n"
        f"• Kutilayotgan (Kiritilishi kerak): <b>{stats['pending_apps']}</b> ta\n"
        f"• Kiritilgan (Tasdiqlangan): <b>{stats['completed_apps']}</b> ta\n"
        f"• Bot foydalanuvchilari soni: <b>{stats['total_users']}</b> ta\n\n"
        "Kerakli bo'limni tanlang:"
    )
    await message.answer(text, reply_markup=get_admin_menu_kb(), parse_mode="HTML")

@router.message(F.text == "📊 Statistika")
async def show_stats(message: Message):
    if not is_admin(message.from_user.id):
        return
        
    stats = await get_stats()
    text = (
        "📊 <b>Bot Statistikasi:</b>\n\n"
        f"• Jami anketalar: <b>{stats['total_apps']}</b>\n"
        f"• Yangi/Kutilayotgan: <b>{stats['pending_apps']}</b>\n"
        f"• Tayyor bo'lgan: <b>{stats['completed_apps']}</b>\n"
        f"• Ro'yxatdan o'tgan foydalanuvchilar: <b>{stats['total_users']}</b>"
    )
    await message.answer(text, parse_mode="HTML")

@router.message(F.text == "📥 Excel formatda yuklab olish")
async def export_excel(message: Message):
    if not is_admin(message.from_user.id):
        return

    wait_msg = await message.answer("⏳ Excel fayl tayyorlanmoqda, kuting...")
    
    apps = await get_all_applications()
    if not apps:
        await wait_msg.edit_text("Hozircha anketalar mavjud emas.")
        return

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    file_path = EXPORTS_DIR / f"greencard_applications_{timestamp}.xlsx"
    export_applications_to_excel(apps, file_path)

    await wait_msg.delete()
    await message.answer_document(
        document=FSInputFile(str(file_path)),
        caption=f"📁 Jami <b>{len(apps)} ta</b> anketa ma'lumotlari Excel formatda yuklandi.\nSana: {datetime.now().strftime('%d.%m.%Y %H:%M')}",
        parse_mode="HTML"
    )

@router.message(F.text == "📨 Mijozga Confirmation Code yuborish")
async def send_code_start(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        return

    await message.answer(
        "Qaysi anketa (ID) ga Confirmation Code yubormoqchisiz?\n"
        "Anketa ID raqamini kiriting (Masalan: <code>1</code>):",
        reply_markup=get_cancel_kb(),
        parse_mode="HTML"
    )
    await state.set_state(AdminStates.waiting_for_app_id)

@router.message(AdminStates.waiting_for_app_id, F.text)
async def process_code_app_id(message: Message, state: FSMContext):
    if not message.text.isdigit():
        await message.answer("⚠️ Iltimos, faqat raqam kiriting (Masalan: <code>1</code>):", parse_mode="HTML")
        return

    app_id = int(message.text.strip())
    app = await get_application(app_id)
    if not app:
        await message.answer(f"⚠️ #{app_id} raqamli anketa topilmadi. Qaytadan tekshirib kiriting:")
        return

    await state.update_data(target_app_id=app_id, target_user_id=app["user_id"], applicant_name=f"{app['first_name']} {app['last_name']}")
    
    await message.answer(
        f"👤 Arizachi: <b>{app['first_name']} {app['last_name']}</b> (Tel: {app['phone_number']})\n\n"
        "Endi rasmiy <b>Confirmation Code</b> ni kiriting (Masalan: <code>20261O0DZK3XYZ89</code>):",
        reply_markup=get_cancel_kb(),
        parse_mode="HTML"
    )
    await state.set_state(AdminStates.waiting_for_confirmation_code)

@router.message(AdminStates.waiting_for_confirmation_code, F.text)
async def process_confirmation_code_send(message: Message, state: FSMContext, bot: Bot):
    code = message.text.strip().upper()
    data = await state.get_data()
    app_id = data.get("target_app_id")
    target_user_id = data.get("target_user_id")
    name = data.get("applicant_name")

    await update_confirmation_code(app_id, code)
    await state.clear()

    # Send confirmation to user
    user_notification = (
        f"🎉 <b>Hurmatli {name}!</b>\n\n"
        "Sizning Green Card (DV Lottery) anketangiz rasmiy AQSh Davlat Departamenti tizimiga muvaffaqiyatli topshirildi!\n\n"
        f"🔑 <b>Sizning rasmiy tasdiqlash raqamingiz (Confirmation Number):</b>\n"
        f"<code>{code}</code>\n\n"
        "📌 <b>DIQQAT:</b> Ushbu kodni skrinshot qilib yoki biror joyga yozib saqlab qo'ying! "
        "Yutuq natijalari e'lon qilinganda natijani faqat ushbu kod orqali tekshirish mumkin bo'ladi.\n\n"
        "Omad tilaymiz! 🇺🇸"
    )

    try:
        await bot.send_message(chat_id=target_user_id, text=user_notification, parse_mode="HTML")
        await message.answer(
            f"✅ #{app_id} raqamli anketaga Confirmation Code muvaffaqiyatli saqlandi va mijozga yuborildi!",
            reply_markup=get_admin_menu_kb()
        )
    except Exception as e:
        await message.answer(
            f"⚠️ Kod bazada saqlandi, lekin foydalanuvchiga yuborishda xatolik: {e}\n"
            f"(Foydalanuvchi botni bloklagan bo'lishi mumkin)",
            reply_markup=get_admin_menu_kb()
        )
