import os

BOT_TOKEN = os.getenv("BOT_TOKEN", "")
SUPABASE_URL = os.getenv("SUPABASE_URL", "")
SUPABASE_KEY = os.getenv("SUPABASE_KEY", "")
CHANNEL_ID = int(os.getenv("CHANNEL_ID", "0"))
PORT = os.getenv("PORT", "10000")
# config.py
import os
# لیست کانال‌های مورد نظر (برای جستجو)
SEARCH_CHANNELS = [
    "nexus_aaron",
    "scihubot",
    "sks7777777nexusbot",
    # کانال‌های جدید را اضافه کنید
]

# شناسه کانال‌ها (اگر عددی دارید)
CHANNEL_IDS = {
    "nexus_aaron": -1001234567890,  # با شناسه واقعی جایگزین کنید
    "scihubot": -1001234567891,
}
