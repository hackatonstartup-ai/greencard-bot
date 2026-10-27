import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent

BOT_TOKEN = os.getenv("BOT_TOKEN", "").strip()

raw_admins = os.getenv("ADMIN_IDS", "").strip()
ADMIN_IDS = [int(x.strip()) for x in raw_admins.split(",") if x.strip().isdigit()]

# 1 bo'lsa, admin ham mijoz tugmalarini ko'radi (sinash uchun). Odatda 0.
ADMIN_SEES_ALL = os.getenv("ADMIN_SEES_ALL", "0").strip().lower() in ("1", "true", "yes")

DB_PATH = BASE_DIR / os.getenv("DB_PATH", "data/bot.db")
PHOTOS_DIR = BASE_DIR / os.getenv("PHOTOS_DIR", "data/photos")
EXPORTS_DIR = BASE_DIR / os.getenv("EXPORTS_DIR", "data/exports")

PHOTOS_DIR.mkdir(parents=True, exist_ok=True)
EXPORTS_DIR.mkdir(parents=True, exist_ok=True)
DB_PATH.parent.mkdir(parents=True, exist_ok=True)
