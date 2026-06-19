# app.py
import os
import re
import asyncio
import tempfile
import aiohttp
import urllib.parse
from datetime import datetime
from typing import Optional, Dict, Any
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters, ContextTypes
from config import BOT_TOKEN, CHANNEL_ID, SEARCH_CHANNELS, PUBLISHER_MAP
from db import get_cached, save_paper
from search_service import search_open_access
from channel_search import search_in_channels

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
    "channel_hits": 0,
}

# الگوی تشخیص DOI
DOI_PATTERN = re.compile(r'10\.\d{4,9}/[-._;()/:A-Z0-9]+', re.IGNORECASE)

# ======================================================
# توابع کمکی برای نام فایل
# ======================================================

def sanitize_filename(filename: str) -> str:
    """پاک‌سازی نام فایل از کاراکترهای غیرمجاز"""
    filename = re.sub(r'[<>:"/\\|?*]', '_', filename)
    filename = re.sub(r'\s+', ' ', filename).strip()
    if len(filename) > 150:
        name, ext = os.path.splitext(filename)
        filename = name[:140] + "..." + ext
    return filename

def get_filename_from_metadata(result: Dict[str, Any], pdf_url: str = None) -> str:
    """دریافت نام فایل از اطلاعات مقاله با اولویت‌بندی"""
    # 1. از عنوان مقاله
    title = result.get("title", "")
    if title and title != "Unknown Title" and title != "Article from Sci-Hub":
        safe_title = "".join(c for c in title if c.isalnum() or c in " .-_,")
        safe_title = re.sub(r'\s+', ' ', safe_title).strip()
        safe_title = sanitize_filename(safe_title)
        if safe_title and len(safe_title) > 3:
            return f"{safe_title[:100]}.pdf"
    
    # 2. از URL
    if pdf_url:
        parsed_url = urllib.parse.urlparse(pdf_url)
        original_name = os.path.basename(parsed_url.path)
        if original_name and original_name.endswith('.pdf'):
            clean_name = sanitize_filename(original_name)
            if clean_name and len(clean_name) > 3:
                return clean_name
    
    # 3. از DOI
    doi = result.get("doi", "")
    if doi:
        safe_doi = doi.replace("/", "_").replace(".", "_")
        return sanitize_filename(f"{safe_doi}.pdf")
    
    # 4. پیش‌فرض
    return sanitize_filename("article.pdf")

# ======================================================
# توابع کمکی برای دکمه‌ها
# ======================================================

def get_main_keyboard() -> InlineKeyboardMarkup:
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
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🔙 بازگشت به منوی اصلی", callback_data="back_to_main")]
    ])

def get_download_keyboard() -> InlineKeyboardMarkup:
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
    total = CACHE_STATS["hits"] + CACHE_STATS["misses"]
    return {
        "size": len(TEMP_CACHE),
        "hits": CACHE_STATS["hits"],
        "misses": CACHE_STATS["misses"],
        "hit_rate": (CACHE_STATS["hits"] / total * 100) if total > 0 else 0,
        "successful_downloads": CACHE_STATS["successful_downloads"],
        "failed_downloads": CACHE_STATS["failed_downloads"],
        "channel_hits": CACHE_STATS["channel_hits"],
    }

def update_cache_stats(hit: bool) -> None:
    if hit:
        CACHE_STATS["hits"] += 1
    else:
        CACHE_STATS["misses"] += 1

# ======================================================
# تابع دانلود PDF با تلاش مجدد
# ======================================================

async def download_pdf_with_retry(url: str, max_retries: int = 3) -> Optional[bytes]:
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
                        
                        if ('application/pdf' not in content_type and not url.endswith('.pdf')) or len(content) < 50000:
                            if attempt < max_retries - 1:
                                print(f"🔄 Retry {attempt + 1}/{max_retries} for download...")
                                await asyncio.sleep(2 ** attempt)
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
# دستور START
# ======================================================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    welcome_text = (
        "سلام 👋\n\n"
        "به **ربات دانلود مقاله** خوش آمدید!\n\n"
        "🔹 **چگونه کار می‌کند؟**\n"
        "• DOI یا عنوان مقاله را ارسال کنید\n"
        "• ربات ابتدا در کانال‌های تلگرام جستجو می‌کند\n"
        "• سپس در ۱۰+ منبع Open Access جستجو می‌کند\n"
        "• اطلاعات کامل مقاله را نمایش می‌دهد\n"
        "• PDF را با نام اصلی مقاله ارسال می‌کند\n\n"
        "🔹 **ویژگی‌ها:**\n"
        "• ⚡ جستجوی سریع در کانال‌ها و منابع\n"
        "• 💾 ذخیره خودکار در کش برای دفعات بعد\n"
        "• 📋 مدیریت کانال‌های تلگرام\n"
        "• 🏷️ شناسایی خودکار ناشر\n"
        "• 📄 حفظ نام اصلی فایل PDF\n\n"
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
            "📌 **ترتیب جستجو:**\n"
            "1. کش (Supabase)\n"
            "2. کانال‌های تلگرام\n"
            "3. منابع Open Access\n\n"
            "📄 **نام فایل:** ربات نام اصلی مقاله را حفظ می‌کند."
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
            f"📈 **نرخ موفقیت کش:** {cache_stats['hit_rate']:.1f}%\n"
            f"📥 **دانلود موفق:** {cache_stats['successful_downloads']}\n"
            f"❌ **دانلود ناموفق:** {cache_stats['failed_downloads']}\n"
            f"📋 **کانال‌ها:** {len(SEARCH_CHANNELS)}\n"
            f"🏢 **ناشران:** {len(PUBLISHER_MAP)}\n"
            f"🔍 **منابع جستجو:** ۱۰ منبع\n\n"
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
            "🔹 **ترتیب جستجو:**\n"
            "1️⃣ کش (Supabase)\n"
            "2️⃣ کانال‌های تلگرام\n"
            "3️⃣ منابع Open Access\n\n"
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
            "🔹 **ویژگی ویژه:**\n"
            "• حفظ نام اصلی فایل PDF\n"
            "• شناسایی خودکار ناشر\n\n"
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
        await query.edit_message_text(
            "📥 لطفاً دوباره DOI را ارسال کنید تا مقاله دوباره جستجو شود.\n\n"
            "💡 برای جستجوی جدید، از دکمه 🔍 جستجوی سریع استفاده کنید.",
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
    if not SEARCH_CHANNELS:
        await update.message.reply_text("📭 لیست کانال‌ها خالی است.")
        return
    
    message = "📚 **لیست کانال‌های جستجو:**\n\n"
    for i, ch in enumerate(SEARCH_CHANNELS, 1):
        message += f"{i}. @{ch}\n"
    
    await update.message.reply_text(message, parse_mode="Markdown")

# ======================================================
# پردازش اصلی پیام‌ها
# ======================================================

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
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
    # 5. جستجو در کانال‌های تلگرام (اولویت اول)
    # ============================================================
    await update.message.reply_text(
        "🔍 **در حال جستجو در کانال‌های تلگرام...**\n"
        f"📋 کانال‌ها: {', '.join([f'@{ch}' for ch in SEARCH_CHANNELS])}",
        parse_mode="Markdown"
    )
    
    channel_result = None
    try:
        channel_result = await search_in_channels(query, context.bot, context)
        if channel_result:
            print(f"✅ Found in Telegram channels")
            CACHE_STATS["channel_hits"] += 1
            
            # اگر file_id موجود باشد، مستقیماً ارسال کن
            if channel_result.get("file_id"):
                await context.bot.send_document(
                    chat_id=update.effective_chat.id,
                    document=channel_result["file_id"],
                    caption=f"📄 از کانال @{channel_result.get('channel', 'unknown')} ارسال شد\n\n📌 {channel_result.get('title', 'Unknown')}"
                )
                # ذخیره در کش
                save_paper(
                    query=query,
                    title=channel_result.get("title", "Unknown"),
                    file_id=channel_result["file_id"],
                    source="channel"
                )
                TEMP_CACHE[query] = {
                    "title": channel_result.get("title", "Unknown"),
                    "file_id": channel_result["file_id"]
                }
                return
            
            # اگر file_id نبود اما pdf_url داشت، دانلود کن
            if channel_result.get("pdf_url"):
                result = channel_result
            else:
                await update.message.reply_text("❌ مقاله در کانال پیدا شد اما قابل دانلود نیست.")
                return
        else:
            raise Exception("No result from channel search")
            
    except Exception as e:
        print(f"⚠️ Channel search failed or no result: {e}")
        # ============================================================
        # 6. جستجو در منابع Open Access (اگر در کانال پیدا نشد)
        # ============================================================
        await update.message.reply_text(
            "🔎 **جستجو در منابع Open Access...**\n"
            "⏳ این عمل ممکن است ۱۰-۲۰ ثانیه طول بکشد.\n\n"
            "📚 منابع جستجو:\n"
            "• Crossref (اطلاعات کامل)\n"
            "• Unpaywall (PDF قانونی)\n"
            "• Sci-Hub (PDF جایگزین)\n"
            "• و ۷ منبع دیگر",
            parse_mode="Markdown"
        )
        
        try:
            result = await asyncio.to_thread(search_open_access, query)
        except Exception as e:
            print(f"❌ Search error: {e}")
            result = None
    
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
        # 7. دانلود PDF
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
        # 8. ساخت کپشن کامل
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
        # 9. دریافت نام اصلی فایل
        # ============================================================
        original_filename = get_filename_from_metadata(result, result.get("pdf_url", ""))
        print(f"📄 Original filename: {original_filename}")
        
        # ============================================================
        # 10. ذخیره در کانال با نام اصلی
        # ============================================================
        await update.message.reply_text("📤 **در حال ذخیره در کانال...**")
        
        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as f:
            f.write(pdf_content)
            f.flush()
            temp_path = f.name
            
            try:
                channel_msg = await context.bot.send_document(
                    chat_id=CHANNEL_ID,
                    document=open(temp_path, 'rb'),
                    filename=original_filename,
                    caption=channel_caption[:1024]
                )
                print(f"✅ Uploaded to channel: {original_filename}")
            except Exception as e:
                print(f"❌ Channel upload error: {e}")
                channel_msg = await context.bot.send_document(
                    chat_id=CHANNEL_ID,
                    document=open(temp_path, 'rb'),
                    caption=channel_caption[:1024]
                )
            finally:
                os.remove(temp_path)
        
        file_id = channel_msg.document.file_id
        
        # ============================================================
        # 11. ذخیره در کش
        # ============================================================
        save_paper(query=query, title=title, file_id=file_id, source=result.get("source", "unknown"))
        TEMP_CACHE[query] = {"title": title, "file_id": file_id}
        CACHE_STATS["successful_downloads"] += 1
        
        # ============================================================
        # 12. ارسال به کاربر با نام اصلی
        # ============================================================
        try:
            await context.bot.send_document(
                chat_id=update.effective_chat.id,
                document=file_id,
                filename=original_filename,
                caption=full_caption,
                parse_mode="Markdown",
                reply_markup=get_download_keyboard()
            )
            print(f"✅ Sent to user: {original_filename}")
        except Exception as e:
            print(f"❌ User send error: {e}")
            await context.bot.send_document(
                chat_id=update.effective_chat.id,
                document=file_id,
                caption=full_caption,
                parse_mode="Markdown",
                reply_markup=get_download_keyboard()
            )
        
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
    print("=" * 50)
    print("🤖 **PaperBot Starting...**")
    print(f"📚 Search channels: {SEARCH_CHANNELS}")
    print(f"🏢 Publisher map: {len(PUBLISHER_MAP)} publishers")
    print(f"📄 Filename: Preserving original PDF names")
    print(f"📋 Search order: Cache → Telegram Channels → Open Access Sources")
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
