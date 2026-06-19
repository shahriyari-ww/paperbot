# config.py
import os

# ---------- متغیرهای اصلی ربات ----------
BOT_TOKEN = os.getenv("BOT_TOKEN", "")
SUPABASE_URL = os.getenv("SUPABASE_URL", "")
SUPABASE_KEY = os.getenv("SUPABASE_KEY", "")
CHANNEL_ID = int(os.getenv("CHANNEL_ID", "0"))  # کانال خصوصی برای ذخیره فایل‌ها
PORT = os.getenv("PORT", "10000")

# ---------- لیست کانال‌های عمومی برای جستجو ----------
SEARCH_CHANNELS = [
    "Archive_article",
    "nexus_aaron",
    "scihubot",
    "sks7777777nexusbot",
    # کانال‌های جدید رو اینجا اضافه کنید
]

# ---------- شناسه عددی کانال‌ها (اختیاری) ----------
CHANNEL_IDS = {
    "Archive_article": -1001234567892,
    "nexus_aaron": -1001234567890,  # عدد واقعی رو جایگزین کنید
    "scihubot": -1001234567891,
}

# ---------- دیکشنری نگاشت ناشران ----------
PUBLISHER_MAP = {
    "1016": "elsevier_bv",
    "1038": "nature_publishing",
    "1126": "aaas",  # Science
    "1371": "plos",
    "1007": "springer",
    "1001": "acm",
    "1109": "ieee",
    "1056": "nejm",
    "1136": "bmj",
    "1098": "rsl",  # Royal Society
    "1021": "acs",  # American Chemical Society
    "1111": "wiley",
    "1155": "hindawi",
    "1186": "biomed_central",
    "1234": "example_publisher",
    # می‌توانید ادامه دهید
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
