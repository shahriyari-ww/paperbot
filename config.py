# config.py
import os

BOT_TOKEN = os.getenv("BOT_TOKEN", "")
SUPABASE_URL = os.getenv("SUPABASE_URL", "")
SUPABASE_KEY = os.getenv("SUPABASE_KEY", "")
CHANNEL_ID = int(os.getenv("CHANNEL_ID", "0"))
PORT = os.getenv("PORT", "10000")

# تنظیمات کش
MAX_CACHE_SIZE = int(os.getenv("MAX_CACHE_SIZE", "100"))  # حداکثر مقالات
MAX_CACHE_DAYS = int(os.getenv("MAX_CACHE_DAYS", "7"))    # روزهای نگهداری

# ادمین ربات (برای دستورات مدیریت)
ADMIN_ID = int(os.getenv("ADMIN_ID", "0"))

# لیست کانال‌های جستجو
SEARCH_CHANNELS = [
    "Archive_article",
    "nexus_aaron",
    "scihubot",
    "sks7777777nexusbot",
]

# شناسه عددی کانال‌ها
CHANNEL_IDS = {
    "Archive_article": -1001234567892,
    "nexus_aaron": -1001234567890,
    "scihubot": -1001234567891,
}

# دیکشنری نگاشت ناشران
PUBLISHER_MAP = {
    "1016": "elsevier_bv",
    "1038": "nature_publishing",
    "1126": "aaas",
    "1371": "plos",
    "1007": "springer",
    "1001": "acm",
    "1109": "ieee",
    "1056": "nejm",
    "1136": "bmj",
    "1098": "rsl",
    "1021": "acs",
    "1111": "wiley",
    "1155": "hindawi",
    "1186": "biomed_central",
}
