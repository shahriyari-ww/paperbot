# config.py
import os

# ---------- متغیرهای اصلی ربات ----------
BOT_TOKEN = os.getenv("BOT_TOKEN", "")
SUPABASE_URL = os.getenv("SUPABASE_URL", "")
SUPABASE_KEY = os.getenv("SUPABASE_KEY", "")
CHANNEL_ID = int(os.getenv("CHANNEL_ID", "0"))
PORT = os.getenv("PORT", "10000")

# ---------- لیست کانال‌های عمومی برای جستجو ----------
SEARCH_CHANNELS = [
    "nexus_aaron",
    "scihubot",
    "sks7777777nexusbot",
]

# ---------- شناسه عددی کانال‌ها (اختیاری) ----------
CHANNEL_IDS = {
    "nexus_aaron": -1001234567890,
    "scihubot": -1001234567891,
}

# ---------- Telethon غیرفعال شد ----------
# API_ID = int(os.getenv("API_ID", "0"))
# API_HASH = os.getenv("API_HASH", "")
# PHONE_NUMBER = os.getenv("PHONE_NUMBER", "")

# ---------- لیست گروه‌ها (غیرفعال) ----------
ALLOWED_GROUPS = []

# ---------- تنظیمات پیشرفته ----------
SEARCH_LIMIT = 100
REQUEST_DELAY = 1.5
