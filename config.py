import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent

BOT_TOKEN = os.getenv("BOT_TOKEN", "").strip()

raw_admins = os.getenv("ADMIN_IDS", "").strip()
ADMIN_IDS = [int(x.strip()) for x in raw_admins.split(",") if x.strip().isdigit()]

# 1 bo'lsa, adminda hech qanday doimiy (reply) tugma ko'rsatilmaydi; admin buyruqlar bilan ishlaydi.
ADMIN_HIDE_BUTTONS = os.getenv("ADMIN_HIDE_BUTTONS", "1").strip().lower() in ("1", "true", "yes")

DB_PATH = BASE_DIR / os.getenv("DB_PATH", "data/bot.db")
PHOTOS_DIR = BASE_DIR / os.getenv("PHOTOS_DIR", "data/photos")
EXPORTS_DIR = BASE_DIR / os.getenv("EXPORTS_DIR", "data/exports")

# Serverdagi rasmlar necha kundan keyin o'chiriladi
PHOTO_RETENTION_DAYS = int(os.getenv("PHOTO_RETENTION_DAYS", "7") or 7)

PHOTOS_DIR.mkdir(parents=True, exist_ok=True)
EXPORTS_DIR.mkdir(parents=True, exist_ok=True)
DB_PATH.parent.mkdir(parents=True, exist_ok=True)

# --- Avtomatik to'lov (hamyon-api.uz). Ikkalasi ham kiritilsa yoqiladi, aks holda chek usuli ishlaydi ---
HAMYON_SHOP_ID = os.getenv("HAMYON_SHOP_ID", "").strip()
HAMYON_SHOP_KEY = os.getenv("HAMYON_SHOP_KEY", "").strip()
HAMYON_BASE_URL = os.getenv("HAMYON_BASE_URL", "https://hamyon-api.uz").strip().rstrip("/")
PAYMENT_AMOUNT = int(os.getenv("PAYMENT_AMOUNT", "50000") or 50000)  # oddiy narx

# --- Chegirma: PROMO_UNTIL sanasigacha (shu kun ham kiradi, Toshkent vaqti bilan) ---
PROMO_AMOUNT = int(os.getenv("PROMO_AMOUNT", "25000") or 25000)
PROMO_UNTIL = os.getenv("PROMO_UNTIL", "2026-11-15").strip()  # YYYY-MM-DD; bo'sh bo'lsa chegirma yo'q


def get_payment_amount() -> int:
    """Hozirgi narx: chegirma muddatida PROMO_AMOUNT, undan keyin PAYMENT_AMOUNT."""
    from datetime import datetime, timedelta, timezone
    if PROMO_UNTIL:
        try:
            end = datetime.strptime(PROMO_UNTIL, "%Y-%m-%d").date()
            today = datetime.now(timezone(timedelta(hours=5))).date()
            if today <= end:
                return PROMO_AMOUNT
        except ValueError:
            pass
    return PAYMENT_AMOUNT

# --- Aloqa markazi (mijozlar uchun) ---
SUPPORT_PHONE = os.getenv("SUPPORT_PHONE", "+998902301905").strip()          # masalan: +998901234567
SUPPORT_TELEGRAM = os.getenv("SUPPORT_TELEGRAM", "greencarduz_admin").strip().lstrip("@")  # masalan: operator_username
SUPPORT_HOURS = os.getenv("SUPPORT_HOURS", "24/7").strip()
