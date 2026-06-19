# config.py
import os
from typing import List, Dict

# ======================================================
# متغیرهای اصلی ربات
# ======================================================
BOT_TOKEN = os.getenv("BOT_TOKEN", "")
SUPABASE_URL = os.getenv("SUPABASE_URL", "")
SUPABASE_KEY = os.getenv("SUPABASE_KEY", "")
CHANNEL_ID = int(os.getenv("CHANNEL_ID", "0"))
PORT = os.getenv("PORT", "10000")

# ======================================================
# تنظیمات کش
# ======================================================
MAX_CACHE_SIZE = int(os.getenv("MAX_CACHE_SIZE", "100"))  # حداکثر مقالات در کش
MAX_CACHE_DAYS = int(os.getenv("MAX_CACHE_DAYS", "7"))    # روزهای نگهداری مقالات

# ======================================================
# ادمین ربات (برای دستورات مدیریت)
# ======================================================
ADMIN_ID = int(os.getenv("ADMIN_ID", "0"))

# ======================================================
# لیست کانال‌های جستجو (بدون @)
# ======================================================
SEARCH_CHANNELS: List[str] = [
    "Archive_article",    # کانال آرشیو مقالات
    "nexus_aaron",        # کانال Nexus
    # "scihubot",         # غیرفعال (ربات است، نه کانال)
    # "sks7777777nexusbot", # غیرفعال (ربات است، نه کانال)
]

# ======================================================
# شناسه عددی کانال‌ها (برای استفاده در Telethon)
# ======================================================
CHANNEL_IDS: Dict[str, int] = {
    "Archive_article": 0,   # با شناسه واقعی جایگزین کنید
    "nexus_aaron": 0,       # با شناسه واقعی جایگزین کنید
}

# ======================================================
# دیکشنری نگاشت ناشران (برای هشتگ‌ها)
# ======================================================
PUBLISHER_MAP: Dict[str, str] = {
    # ناشران علمی معروف
    "1016": "elsevier_bv",      # Elsevier
    "1038": "nature_publishing", # Nature
    "1126": "aaas",             # Science (AAAS)
    "1371": "plos",             # PLOS
    "1007": "springer",         # Springer
    "1001": "acm",              # ACM
    "1109": "ieee",             # IEEE
    "1056": "nejm",             # NEJM
    "1136": "bmj",              # BMJ
    "1098": "rsl",              # Royal Society
    "1021": "acs",              # American Chemical Society
    "1111": "wiley",            # Wiley
    "1155": "hindawi",          # Hindawi
    "1186": "biomed_central",   # BioMed Central
    
    # ناشران جدید (اختیاری)
    "1172": "jci",              # Journal of Clinical Investigation
    "1245": "peerj",            # PeerJ
    "7717": "peerj",            # PeerJ (همان)
    "2190": "frontiers",        # Frontiers
    "3389": "frontiers",        # Frontiers
    "2470": "mdpi",             # MDPI
    "3390": "mdpi",             # MDPI
}

# ======================================================
# تنظیمات Unpaywall
# ======================================================
UNPAYWALL_EMAIL = os.getenv("UNPAYWALL_EMAIL", "your_email@example.com")

# ======================================================
# تنظیمات Telethon (اختیاری - برای جستجوی کانال‌ها)
# ======================================================
API_ID = int(os.getenv("API_ID", "0"))
API_HASH = os.getenv("API_HASH", "")
PHONE_NUMBER = os.getenv("PHONE_NUMBER", "")

# ======================================================
# تنظیمات پیشرفته
# ======================================================
REQUEST_TIMEOUT = int(os.getenv("REQUEST_TIMEOUT", "30"))  # زمان تایم‌اوت درخواست‌ها
DOWNLOAD_TIMEOUT = int(os.getenv("DOWNLOAD_TIMEOUT", "90"))  # زمان تایم‌اوت دانلود
MAX_RETRIES = int(os.getenv("MAX_RETRIES", "3"))  # تعداد تلاش مجدد

# ======================================================
# وضعیت ربات (برای نمایش در دکمه‌ها)
# ======================================================
BOT_STATUS = "🟢 فعال"
BOT_VERSION = "2.0.0"
BOT_DEVELOPER = "@Mohammadsh7"

# ======================================================
# لیست منابع جستجو (برای نمایش در پیام‌ها)
# ======================================================
SEARCH_SOURCES: List[str] = [
    "Crossref (اطلاعات کامل)",
    "Unpaywall (PDF قانونی)",
    "Sci-Hub (PDF جایگزین)",
    "PubMed (مقالات پزشکی)",
    "Semantic Scholar",
    "arXiv",
    "CORE",
    "BASE",
    "DOAJ",
    "کانال‌های تلگرام",
]
