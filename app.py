# app.py
import os
import re
import asyncio
import tempfile
import aiohttp
from datetime import datetime
from typing import Optional, Dict, Any
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters, ContextTypes
from config import BOT_TOKEN, CHANNEL_ID, SEARCH_CHANNELS, PUBLISHER_MAP
from db import get_cached, save_paper
from search_service import search_open_access

# ======================================================
# کش موقت در حافظه
# ======================================================
TEMP_CACHE: Dict[str, Dict[str, Any]] = {}
CACHE_STATS = {
    "hits": 0,
    "misses": 0,
    "total_searches": 0,
    "successful_downloads": 0,
    "failed_downloads": 0,
}

# الگوی تشخیص DOI (پشتیبانی از همه فرمت‌ها)
DOI_PATTERN = re.compile(r'10\.\d{4,9}/[-._;()/:A-Z0-9]+', re.IGNORECASE)
PDF_PATTERN = re.compile(r'\.pdf$', re.IGNORECASE)

# ======================================================
# توابع کمکی برای دکمه‌ها
# ======================================================

def get_main_keyboard() -> InlineKeyboardMarkup:
    """کیبورد اصلی با دکمه‌های تعاملی"""
    keyboard = [
        [
            InlineKeyboardButton("📚 راهنما", callback_data="help"),
            InlineKeyboardButton("📊 آمار", callback_data="stats"),
        ],
        [
            InlineKeyboardButton("📋 لیست کانال‌ها", callback_data="list_channels"),
            InlineKeyboardButton("❓ درباره", callback_data="about"),
        ],
        [
            InlineKeyboardButton("🔄 کش", callback_data="cache_info"),
            InlineKeyboardButton("🔍 جستجوی سریع", switch_inline_query_current_chat=""),
        ]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_help_keyboard() -> InlineKeyboardMarkup:
    """کیبورد بازگشت به منوی اصلی"""
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🔙 بازگشت به منوی اصلی", callback_data="back_to_main")]
    ])

def get_download_keyboard() -> InlineKeyboardMarkup:
    """کیبورد بعد از دانلود"""
    keyboard = [
        [
            InlineKeyboardButton("📥 دانلود مجدد", callback_data="download_again"),
            InlineKeyboardButton("🔍 جستجوی جدید", switch_inline_query_current_chat=""),
        ],
        [InlineKeyboardButton("📚 منوی اصلی", callback_data="back_to_main")],
    ]
    return InlineKeyboardMarkup(keyboard)

# ======================================================
# توابع مدیریت کش
# ======================================================

def get_cache_stats() -> Dict[str, Any]:
    """دریافت آمار کش"""
    return {
        "size": len(TEMP_CACHE),
        "hits": CACHE_STATS["hits"],
        "misses": CACHE_STATS["misses"],
        "hit_rate": CACHE_STATS["hits"] / (CACHE_STATS["hits"] + CACHE_STATS["misses"]) * 100 if (CACHE_STATS["hits"] + CACHE_STATS["misses"]) > 0 else 0,
    }

def update_cache_stats(hit: bool) -> None:
    """به‌روزرسانی آمار کش"""
    if hit:
        CACHE_STATS["hits"] += 1
    else:
        CACHE_STATS["misses"] += 1

# ======================================================
# دستور START
# ======================================================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """دستور شروع با دکمه‌های تعاملی"""
    welcome_text = (
        "سلام 👋\n\n"
        "به **ربات دانلود مقاله** خوش آمدید!\n\n"
        "🔹 **چگونه کار می‌کند؟**\n"
        "• DOI یا عنوان مقاله را ارسال کنید\n"
        "• ربات در ۱۰+ منبع Open Access جستجو می‌کند\n"
        "• اطلاعات کامل مقاله را نمایش می‌دهد\n"
        "• PDF را برای شما ارسال می‌کند\n\n"
        "🔹 **ویژگی‌ها:**\n"
        "• ⚡ جستجوی سریع در چندین منبع\n"
        "• 💾 ذخیره خودکار در کش برای دفعات بعد\n"
        "• 📋 مدیریت کانال‌های تلگرام\n"
        "• 🏷️ شناسایی خودکار ناشر\n\n"
        f"📚 **کانال‌های جستجو:**\n" + "\n".join([f"• @{ch}" for ch in SEARCH_CHANNELS]) + "\n\n"
        "👇 از دکمه‌های زیر استفاده کنید:"
    )
    
    await update.message.reply_text(
        welcome_text,
        reply_markup=get_main_keyboard(),
        parse_mode="Markdown"
    )

# ======================================================
# پردازش دکمه‌ها
# ======================================================
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """پردازش کلیک روی دکمه‌های تعاملی"""
    query = update.callback_query
    await query.answer()
    
    data = query.data
    
    if data == "help":
        help_text = (
            "📚 **راهنمای استفاده از ربات**\n\n"
            "1️⃣ **ارسال DOI:**\n"
            "مثلاً: `10.1016/j.colsurfa.2024.135789`\n\n"
            "2️⃣ **ارسال عنوان مقاله:**\n"
            "مثلاً: `A Novel Coronavirus from Patients with Pneumonia`\n\n"
            "3️⃣ **ارسال لینک مقاله:**\n"
            "مثلاً: `https://doi.org/10.1056/NEJMoa2001017`\n\n"
            "4️⃣ **مدیریت کانال‌ها:**\n"
            "• `/add_channel @channel` - اضافه کردن کانال\n"
            "• `/remove_channel @channel` - حذف کانال\n"
            "• `/list_channels` - نمایش لیست کانال‌ها\n\n"
            "📌 **نکته:** مقالات پس از اولین جستجو در کش ذخیره می‌شوند."
        )
        await query.edit_message_text(
            help_text,
            parse_mode="Markdown",
            reply_markup=get_help_keyboard()
        )
    
    elif data == "stats":
        cache_stats = get_cache_stats()
        stats_text = (
            "📊 **آمار ربات**\n\n"
            f"📚 **مقالات در کش:** {cache_stats['size']}\n"
            f"✅ **Cache Hit:** {cache_stats['hits']}\n"
            f"❌ **Cache Miss:** {cache_stats['misses']}\n"
            f"📈 **نرخ موفقیت:** {cache_stats['hit_rate']:.1f}%\n"
            f"📋 **کانال‌ها:** {len(SEARCH_CHANNELS)}\n"
            f"🏢 **ناشران:** {len(PUBLISHER_MAP)}\n"
            f"🔍 **منابع جستجو:** ۱۰ منبع\n\n"
            f"📥 **دانلود موفق:** {CACHE_STATS['successful_downloads']}\n"
            f"❌ **دانلود ناموفق:** {CACHE_STATS['failed_downloads']}\n"
            f"⚡ **وضعیت:** {'🟢 فعال' if BOT_TOKEN else '🔴 غیرفعال'}\n"
            f"📅 **آخرین بروزرسانی:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        )
        await query.edit_message_text(
            stats_text,
            parse_mode="Markdown",
            reply_markup=get_help_keyboard()
        )
    
    elif data == "cache_info":
        cache_stats = get_cache_stats()
        cache_text = (
            "💾 **اطلاعات کش**\n\n"
            f"📚 **تعداد مقالات:** {cache_stats['size']}\n"
            f"✅ **Cache Hit:** {cache_stats['hits']}\n"
            f"❌ **Cache Miss:** {cache_stats['misses']}\n"
            f"📈 **نرخ موفقیت:** {cache_stats['hit_rate']:.1f}%\n\n"
        )
        if TEMP_CACHE:
            cache_text += "**📄 مقالات اخیر:**\n"
            for i, (key, value) in enumerate(list(TEMP_CACHE.items())[-5:], 1):
                cache_text += f"{i}. {value.get('title', 'Unknown')[:40]}...\n"
        else:
            cache_text += "📭 کش خالی است."
        
        await query.edit_message_text(
            cache_text,
            parse_mode="Markdown",
            reply_markup=get_help_keyboard()
        )
    
    elif data == "list_channels":
        if not SEARCH_CHANNELS:
            list_text = "📭 لیست کانال‌ها خالی است."
        else:
            list_text = "📋 **لیست کانال‌های جستجو:**\n\n"
            for i, ch in enumerate(SEARCH_CHANNELS, 1):
                list_text += f"{i}. @{ch}\n"
        
        await query.edit_message_text(
            list_text,
            parse_mode="Markdown",
            reply_markup=get_help_keyboard()
        )
    
    elif data == "about":
        about_text = (
            "❓ **درباره ربات**\n\n"
            "📌 این ربات برای پیدا کردن نسخه Open Access مقالات علمی طراحی شده است.\n\n"
            "🔹 **منابع جستجو:**\n"
            "• Crossref (اطلاعات کامل)\n"
            "• Unpaywall (PDF قانونی)\n"
            "• Sci-Hub (PDF جایگزین)\n"
            "• PubMed (مقالات پزشکی)\n"
            "• Semantic Scholar\n"
            "• arXiv\n"
            "• CORE\n"
            "• BASE\n"
            "• DOAJ\n"
            "• کانال‌های تلگرام\n\n"
            "🔹 **توسعه‌دهنده:** @Mohammadsh7\n"
            "🔹 **نسخه:** 2.0.0\n"
            "🔹 **وضعیت:** 🟢 فعال"
        )
        await query.edit_message_text(
            about_text,
            parse_mode="Markdown",
            reply_markup=get_help_keyboard()
        )
    
    elif data == "download_again":
        # این دکمه فقط برای دانلود مجدد است، فعلاً پیام می‌دهیم
        await query.edit_message_text(
            "📥 لطفاً دوباره DOI را ارسال کنید تا مقاله دوباره جستجو شود.",
            reply_markup=get_help_keyboard()
        )
    
    elif data == "back_to_main":
        await query.edit_message_text(
            "👋 به منوی اصلی بازگشتید.\n\n"
            "DOI یا عنوان مقاله را ارسال کنید یا از دکمه‌ها استفاده کنید:",
            reply_markup=get_main_keyboard()
        )

# ======================================================
# دستورات مدیریت کانال
# ======================================================
async def add_channel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """اضافه کردن کانال جدید به لیست جستجو"""
    if not context.args:
        await update.message.reply_text(
            "❌ لطفاً نام کانال را وارد کنید.\n"
            "مثال: `/add_channel nexus_aaron`\n\n"
            "📌 نام کانال را بدون @ وارد کنید."
        )
        return
    
    channel = context.args[0].replace("@", "").strip()
    if not channel:
        await update.message.reply_text("❌ نام کانال معتبر نیست.")
        return
    
    if channel in SEARCH_CHANNELS:
        await update.message.reply_text(f"ℹ️ کانال @{channel} قبلاً در لیست وجود دارد.")
        return
    
    SEARCH_CHANNELS.append(channel)
    await update.message.reply_text(
        f"✅ کانال @{channel} به لیست جستجو اضافه شد.\n\n"
        f"📋 لیست فعلی: {', '.join([f'@{ch}' for ch in SEARCH_CHANNELS])}"
    )

async def remove_channel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """حذف کانال از لیست جستجو"""
    if not context.args:
        await update.message.reply_text(
            "❌ لطفاً نام کانال را وارد کنید.\n"
            "مثال: `/remove_channel nexus_aaron`"
        )
        return
    
    channel = context.args[0].replace("@", "").strip()
    if not channel:
        await update.message.reply_text("❌ نام کانال معتبر نیست.")
        return
    
    if channel not in SEARCH_CHANNELS:
        await update.message.reply_text(f"ℹ️ کانال @{channel} در لیست وجود ندارد.")
        return
    
    SEARCH_CHANNELS.remove(channel)
    await update.message.reply_text(
        f"✅ کانال @{channel} از لیست جستجو حذف شد.\n\n"
        f"📋 لیست فعلی: {', '.join([f'@{ch}' for ch in SEARCH_CHANNELS])}"
    )

async def list_channels(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """نمایش لیست کانال‌های جستجو"""
    if not SEARCH_CHANNELS:
        await update.message.reply_text("📭 لیست کانال‌ها خالی است.")
        return
    
    message = "📚 **لیست کانال‌های جستجو:**\n\n"
    for i, ch in enumerate(SEARCH_CHANNELS, 1):
        message += f"{i}. @{ch}\n"
    
    await update.message.reply_text(message, parse_mode="Markdown")

# ======================================================
# تابع دریافت اطلاعات کامل مقاله (با Fallback)
# ======================================================
async def get_complete_metadata(doi: str) -> Optional[Dict[str, Any]]:
    """
    دریافت اطلاعات کامل مقاله از چند منبع با Fallback مکانیزم
    """
    # 1. ابتدا از Crossref دریافت کن
    try:
        result = await asyncio.to_thread(search_open_access, doi)
        if result and result.get("authors") != "Unknown Authors":
            return result
    except Exception as e:
        print(f"⚠️ Error in primary search: {e}")
    
    # 2. اگر کامل نبود، از منابع دیگر استفاده کن
    # (این بخش در search_open_access مدیریت می‌شود)
    return None

# ======================================================
# تابع دانلود PDF با تلاش مجدد
# ======================================================
async def download_pdf_with_retry(url: str, max_retries: int = 3) -> Optional[bytes]:
    """
    دانلود PDF با تلاش مجدد و Backoff تصاعدی
    """
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Accept": "application/pdf,text/html,*/*",
        "Accept-Language": "en-US,en;q=0.5",
    }
    
    for attempt in range(max_retries):
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=headers, timeout=90, allow_redirects=True) as response:
                    if response.status == 200:
                        content = await response.read()
                        content_type = response.headers.get('content-type', '').lower()
                        
                        # اگر محتوا PDF نیست و حجم کم است، تلاش مجدد
                        if ('application/pdf' not in content_type and not url.endswith('.pdf')) or len(content) < 50000:
                            if attempt < max_retries - 1:
                                print(f"🔄 Retry {attempt + 1}/{max_retries} for download...")
                                await asyncio.sleep(2 ** attempt)  # Backoff تصاعدی
                                continue
                        return content
                    
                    if attempt < max_retries - 1:
                        await asyncio.sleep(2 ** attempt)
        except Exception as e:
            print(f"⚠️ Download attempt {attempt + 1} failed: {e}")
            if attempt < max_retries - 1:
                await asyncio.sleep(2 ** attempt)
    
    return None

# ======================================================
# پردازش اصلی پیام‌ها
# ======================================================
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    پردازش اصلی پیام‌های کاربر
    """
    # ============================================================
    # 1. اعتبارسنجی ورودی
    # ============================================================
    if not update.message or not update.message.text:
        return
    
    text = update.message.text.strip()
    if not text or text.startswith('/'):
        return
    
    print(f"📩 Received message: {text[:100]}...")
    CACHE_STATS["total_searches"] += 1
    
    # ============================================================
    # 2. استخراج DOI
    # ============================================================
    doi_match = DOI_PATTERN.search(text)
    query = doi_match.group(0) if doi_match else text
    print(f"🔍 Extracted query: {query}")
    
    # ============================================================
    # 3. بررسی کش (Supabase)
    # ============================================================
    cached = get_cached(query)
    if cached:
        update_cache_stats(True)
        await context.bot.send_document(
            chat_id=update.effective_chat.id,
            document=cached["file_id"],
            caption=f"📄 از کش ارسال شد\n\n📌 {cached.get('title', 'Unknown')}"
        )
        return
    
    # ============================================================
    # 4. بررسی کش موقت
    # ============================================================
    if query in TEMP_CACHE:
        update_cache_stats(True)
        await context.bot.send_document(
            chat_id=update.effective_chat.id,
            document=TEMP_CACHE[query]["file_id"],
            caption=f"📄 از کش موقت ارسال شد\n\n📌 {TEMP_CACHE[query].get('title', 'Unknown')}"
        )
        return
    
    update_cache_stats(False)
    
    # ============================================================
    # 5. جستجو
    # ============================================================
    await update.message.reply_text(
        "🔎 **در حال جستجو در منابع Open Access...**\n"
        "⏳ این عمل ممکن است ۱۰-۲۰ ثانیه طول بکشد.\n\n"
        "📚 منابع جستجو:\n"
        "• Crossref (اطلاعات کامل)\n"
        "• Unpaywall (PDF قانونی)\n"
        "• Sci-Hub (PDF جایگزین)\n"
        "• و ۷ منبع دیگر",
        parse_mode="Markdown"
    )
    
    # دریافت اطلاعات کامل مقاله
    result = await get_complete_metadata(query)
    if not result:
        await update.message.reply_text(
            "❌ **مقاله پیدا نشد.**\n\n"
            "💡 **نکات:**\n"
            "• مطمئن شوید DOI یا عنوان درست است\n"
            "• برخی مقالات ممکن است پولی باشند\n"
            "• از DOI استفاده کنید (مثلاً 10.1038/...)\n"
            "• برای راهنمایی بیشتر، /start را بزنید",
            parse_mode="Markdown"
        )
        CACHE_STATS["failed_downloads"] += 1
        return
    
    try:
        # ============================================================
        # 6. دانلود PDF
        # ============================================================
        await update.message.reply_text("📥 **در حال دانلود PDF...**")
        
        pdf_content = await download_pdf_with_retry(result["pdf_url"])
        if not pdf_content or len(pdf_content) < 50000:
            await update.message.reply_text(
                "⚠️ **دانلود PDF ناموفق بود.**\n"
                "فایل دانلود شده بسیار کوچک است یا معتبر نیست."
            )
            CACHE_STATS["failed_downloads"] += 1
            return
        
        # ============================================================
        # 7. ساخت کپشن کامل
        # ============================================================
        title = result.get("title", "Unknown Title")
        authors = result.get("authors", "Unknown Authors")
        journal = result.get("journal", "Unknown Journal")
        year = result.get("year", "Unknown Year")
        doi = query if query.startswith("10.") else result.get("doi", "")
        
        # استخراج ناشر برای هشتگ
        publisher = "unknown"
        hashtag = ""
        if doi.startswith("10."):
            try:
                publisher_part = doi.split("/")[0].replace("10.", "")
                publisher = PUBLISHER_MAP.get(publisher_part, publisher_part)
                hashtag = f"#pub_{publisher}"
            except:
                pass
        
        full_caption = f"""📄 **{title}**

📝 **Authors:** {authors}
📅 **Published:** {year}
📚 **Journal:** {journal}
🔗 **DOI:** {doi} (https://doi.org/{doi})
📎 **Source:** {result.get('source', 'unknown')}"""
        
        channel_caption = f"{title}\n\n{hashtag}\n{doi} (https://doi.org/{doi})"
        
        # ============================================================
        # 8. ذخیره در کانال
        # ============================================================
        await update.message.reply_text("📤 **در حال ذخیره در کانال...**")
        
        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as f:
            f.write(pdf_content)
            f.flush()
            temp_path = f.name
            
            channel_msg = await context.bot.send_document(
                chat_id=CHANNEL_ID,
                document=open(temp_path, 'rb'),
                caption=channel_caption[:1024]  # Telegram limit
            )
            file_id = channel_msg.document.file_id
            os.remove(temp_path)
        
        # ============================================================
        # 9. ذخیره در کش
        # ============================================================
        save_paper(query=query, title=title, file_id=file_id, source=result.get("source", "unknown"))
        TEMP_CACHE[query] = {"title": title, "file_id": file_id}
        CACHE_STATS["successful_downloads"] += 1
        
        # ============================================================
        # 10. ارسال به کاربر
        # ============================================================
        await context.bot.send_document(
            chat_id=update.effective_chat.id,
            document=file_id,
            caption=full_caption,
            parse_mode="Markdown",
            reply_markup=get_download_keyboard()
        )
        
        print(f"✅ Paper sent successfully: {title[:50]}...")
        
    except asyncio.TimeoutError:
        await update.message.reply_text("⏰ زمان دانلود به پایان رسید. لطفاً دوباره تلاش کنید.")
        CACHE_STATS["failed_downloads"] += 1
    except Exception as e:
        print(f"❌ Error: {e}")
        await update.message.reply_text(f"⚠️ **خطا:** {str(e)}\n\nلطفاً دوباره تلاش کنید.")
        CACHE_STATS["failed_downloads"] += 1

# ======================================================
# تابع اصلی
# ======================================================
def main() -> None:
    """تابع اصلی راه‌اندازی ربات"""
    print("=" * 50)
    print("🤖 **PaperBot Starting...**")
    print(f"📚 Search channels: {SEARCH_CHANNELS}")
    print(f"🏢 Publisher map: {len(PUBLISHER_MAP)} publishers")
    print("=" * 50)
    
    app = Application.builder().token(BOT_TOKEN).build()
    app.bot_data['channels'] = SEARCH_CHANNELS
    
    # ثبت هندلرها
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("add_channel", add_channel))
    app.add_handler(CommandHandler("remove_channel", remove_channel))
    app.add_handler(CommandHandler("list_channels", list_channels))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.add_handler(CallbackQueryHandler(button_handler))
    
    # تشخیص محیط و اجرا
    is_render = os.environ.get("RENDER") or os.environ.get("PORT")
    
    if is_render:
        port = int(os.environ.get("PORT", 10000))
        webhook_url = f"https://paperbot-ng4v.onrender.com/"
        print(f"🚀 Starting with Webhook on port {port}")
        print(f"📡 Webhook URL: {webhook_url}")
        app.run_webhook(
            listen="0.0.0.0",
            port=port,
            webhook_url=webhook_url
        )
    else:
        print("🚀 Starting with Polling (local mode)")
        app.run_polling()

if __name__ == "__main__":
    main()
