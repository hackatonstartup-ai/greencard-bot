# 🇺🇸 Green Card (DV Lottery) Telegram Boti

Ushbu bot mijozlardan rasmiy AQSh Green Card (DV Lottery) anketasi uchun barcha zarur ma'lumotlar va fotosuratlarni yig'ib olish, ma'lumotlarni SQLite bazasida saqlash va operator/admin uchun **Excel (.xlsx)** formatida taqdim etish uchun maxsus ishlab chiqilgan.

---

## 🚀 Imkoniyatlari

1. **Bosqichma-bosqich anketa (FSM):**
   * Asosiy arizachi (Familiya, Ism, Jinsi, Tug'ilgan sana, Tug'ilgan shahar/davlat);
   * 600x600 px o'lchamdagi fotosurat tekshiruvi va avtomatik qirqish/moslash;
   * Yashash manzili, shahar, tuman, pochta indeksi, telefon raqam, email;
   * Ta'lim darajasi va oilaviy holat;
   * Agar oilali bo'lsa: Turmush o'rtog'ining to'liq ma'lumotlari va 600x600 fotosurati;
   * Agar farzandlari bo'lsa: 21 yoshgacha bo'lgan barcha farzandlar ma'lumotlari va fotosuratlari.

2. **Admin paneli (`/admin`):**
   * Yangi arizalar tushganda bot admin(lar)ga arizachi haqida to'liq xabar va suratini yuboradi;
   * **Excel yuklab olish:** Barcha to'ldirilgan anketalarni 1 tugma bilan chiroyli formatdagi `.xlsx` jadvali ko'rinishida yuklab olish (Asosiy anketalar, Turmush o'rtoqlari va Farzandlar alohida varaqlarda);
   * **Confirmation Code yuborish:** Rasmiy saytga kiritganingizdan so'ng, confirmation codeni bot orqali avtomatik mijozga yuborish.

---

## 🛠 O'rnatish va Ishga tushirish

### 1. Bot token va Admin ID ni sozlash

`.env` faylini oching va ma'lumotlarni kiriting:

```env
BOT_TOKEN=7123456789:AAH...sizning_bot_tokeningiz
ADMIN_IDS=123456789
```

> **Eslatma:**
> - `BOT_TOKEN` ni olish uchun Telegramda [@BotFather](https://t.me/BotFather) ga kiring va `/newbot` buyrug'ini bering.
> - O'zingizning Telegram raqamli ID ingizni bilish uchun [@userinfobot](https://t.me/userinfobot) ga `/start` bosing va chiqqan `Id` raqamini `ADMIN_IDS` ga yozing. Bir nechta admin bo'lsa vergul bilan ajrating: `ADMIN_IDS=123456,789101`.

### 2. Botni ishga tushirish

Terminalda quyidagi buyruqni bering:

```bash
source .venv/bin/activate
python3 main.py
```

---

## 📁 Loyiha tuzilishi

```
greencard/
├── .env                # Bot token va admin sozlamalari
├── .env.example        # Misol andoza
├── requirements.txt    # Kerakli Python kutubxonalari
├── main.py             # Botning asosiy kirish fayli
├── config.py           # Sozlamalar va yo'llar
├── database.py         # SQLite ma'lumotlar bazasi (aiosqlite)
├── states.py           # FSM bosqichlari (Arizachi, Oila, Farzandlar)
├── keyboards.py        # Menyular va tugmalar
├── handlers/           # Bot buyruqlari va xabarlar
│   ├── start.py        # /start, rasm qoidalari va yo'riqnomalar
│   ├── application.py  # Anketa to'ldirish to'liq jarayoni
│   └── admin.py        # Admin panel, Excel eksport, kod yuborish
├── utils/
│   ├── photo.py        # Fotosuratni tekshirish va 600x600 ga keltirish
│   └── excel.py        # Ma'lumotlarni Excel formatiga chiqarish
└── data/
    ├── bot.db          # Barcha arizalar bazasi
    ├── photos/         # Mijozlar yuklagan rasmlar
    └── exports/        # Yaratilgan Excel fayllari
```
