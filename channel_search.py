# channel_search.py
import re
import asyncio
from telegram import Update
from telegram.ext import ContextTypes
from db import get_cached, save_paper
from config import CHANNEL_IDS  # لیست کانال‌ها

# لیست کانال‌هایی که باید بررسی شوند
# می‌توانید در config.py تعریف کنید یا اینجا
DEFAULT_CHANNELS = [
    "@nexus_aaron",
    "@scihubot",
    "@sks7777777nexusbot",
    # کانال‌های دیگر را اضافه کنید
]

# لیست کلمات کلیدی برای شناسایی مقاله
DOI_PATTERN = re.compile(r'10\.\d{4,9}/[-._;()/:A-Z0-9]+', re.IGNORECASE)

async def search_in_channels(query: str, bot, context: ContextTypes.DEFAULT_TYPE):
    """
    جستجوی مقاله در کانال‌های مشخص شده
    
    Args:
        query (str): DOI یا عنوان مقاله
        bot: نمونه ربات
        context: context تلگرام
        
    Returns:
        dict: اطلاعات مقاله یا None
    """
    # ابتدا کش را چک کن
    cached = get_cached(query)
    if cached:
        print(f"✅ Cache hit for: {query}")
        return cached
    
    # جستجو در کانال‌ها
    channels = getattr(context.bot_data, 'channels', DEFAULT_CHANNELS)
    
    for channel in channels:
        try:
            print(f"🔍 Searching in {channel}...")
            
            # جستجو در کانال با استفاده از forward
            # این روش فقط برای کانال‌هایی که ربات عضو است کار می‌کند
            try:
                # ارسال پیام به کانال برای تست
                await bot.send_message(
                    chat_id=channel,
                    text=f"/search {query}",
                    disable_notification=True
                )
                
                # منتظر پاسخ بمان (این روش کامل نیست، نیاز به پیاده‌سازی بهتر دارد)
                # در ادامه نسخه کامل‌تر ارائه شده است
                
            except Exception as e:
                print(f"❌ Error in {channel}: {e}")
                continue
                
        except Exception as e:
            print(f"❌ Error searching {channel}: {e}")
            continue
    
    return None

async def get_from_channel(query: str, channel_id: str, bot):
    """
    دریافت مستقیم مقاله از کانال با استفاده از message_id
    
    Args:
        query (str): شناسه مقاله
        channel_id (str): شناسه کانال
        bot: نمونه ربات
        
    Returns:
        dict: اطلاعات مقاله یا None
    """
    try:
        # این تابع نیاز به message_id دارد که باید از قبل ذخیره شده باشد
        # یا با استفاده از فوروارد پیام‌ها
        pass
    except Exception as e:
        print(f"❌ Error getting from channel: {e}")
        return None
