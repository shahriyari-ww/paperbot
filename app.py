# app.py
import os
import re
import sys
import tempfile
import requests
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters, ContextTypes
from config import BOT_TOKEN, CHANNEL_ID, SEARCH_CHANNELS, PUBLISHER_MAP
from db import get_cached, save_paper
from search_service import search_open_access

# ======================================================
# کش موقت در حافظه (برای مواقعی که Supabase کار نمی‌کند)
# ======================================================
TEMP_CACHE = {}

# الگوی تشخیص DOI از متن (پشتیبانی از URL کامل و DOI خالص)
DOI_PATTERN = re.compile(r'10\.\d{4,9}/[-._;()/:A-Z0-9]+', re.IGNORECASE)

# ======================================================
# توابع کمکی برای دکمه‌ها
# ======================================================

def get_main_keyboard():
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
            InlineKeyboardButton("🔍 جستجوی سریع", switch_inline_query_current_chat=""),
        ]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_help_keyboard():
    """کیبورد بازگشت به منوی اصلی"""
    keyboard = [
        [InlineKeyboardButton("🔙 بازگشت به منوی اصلی", callback_data="back_to_main")]
    ]
    return InlineKeyboardMarkup(keyboard)

# ======================================================
# توضیحات در چت خالی (Before Start)
# ======================================================

async def handle_empty_chat(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """هنگامی که کاربر ربات را در چت خالی باز می‌کند"""
    # بررسی اینکه آیا کاربر تازه وارد شده و چت خالی است
    if update.message and not update.message.text:
        await update.message.reply_text(
            "👋 به ربات دانلود مقاله خوش آمدید!\n\n"
            "برای شروع کار، یکی از گزینه‌های زیر را انتخاب کنید:\n"
            "• دکمه /start را بزنید\n"
            "• یک DOI یا عنوان مقاله ارسال کنید\n"
            "• از دکمه‌های زیر استفاده کنید\n\n"
            "📌 ربات به شما کمک می‌کند تا نسخه Open Access مقالات را پیدا کنید.",
            reply_markup=get_main_keyboard()
        )
        return

# ======================================================
# دستور START با دکمه‌ها و توضیحات
# ======================================================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """دستور شروع با دکمه‌های تعاملی"""
    welcome_text = (
        "سلام 👋\n\n"
        "به ربات دانلود مقاله خوش آمدید!\n\n"
        "🔹 **چگونه کار می‌کند؟**\n"
        "• DOI یا عنوان مقاله را ارسال کنید\n"
        "• ربات در منابع Open Access جستجو می‌کند\n"
        "• در صورت پیدا شدن، PDF را برای شما ارسال می‌کند\n\n"
        "🔹 **ویژگی‌ها:**\n"
        "• جستجو در ۱۰ منبع مختلف\n"
        "• ذخیره خودکار در کش برای دفعات بعد\n"
        "• پشتیبانی از کانال‌های تلگرام\n\n"
        "📚 **کانال‌های جستجو:**\n" + "\n".join([f"• @{ch}" for ch in SEARCH_CHANNELS]) + "\n\n"
        "👇 از دکمه‌های زیر برای اطلاعات بیشتر استفاده کنید:"
    )
    
    await update.message.reply_text(
        welcome_text,
        reply_markup=get_main_keyboard(),
        parse_mode="Markdown"
    )

# ======================================================
# پردازش دکمه‌ها (Callback Query)
# ======================================================
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """پردازش کلیک روی دکمه‌های تعاملی"""
    query = update.callback_query
    await query.answer()  # پاسخ به تلگرام برای جلوگیری از خطا
    
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
        await query.edit_message_text(help_text, parse_mode="Markdown", reply_markup=get_help_keyboard())
    
    elif data == "stats":
        # آمار ربات
        total_cached = len(TEMP_CACHE)
        total_channels = len(SEARCH_CHANNELS)
        total_publishers = len(PUBLISHER_MAP)
        
        stats_text = (
            "📊 **آمار ربات**\n\n"
            f"📚 **تعداد مقالات در کش:** {total_cached}\n"
            f"📋 **تعداد کانال‌های جستجو:** {total_channels}\n"
            f"🏢 **تعداد ناشران شناسایی‌شده:** {total_publishers}\n"
            f"🔍 **منابع جستجو:** ۱۰ منبع\n\n"
            f"⚡ **وضعیت:** {'فعال ✅' if BOT_TOKEN else 'غیرفعال ❌'}\n"
            f"📅 **آخرین بروزرسانی:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        )
        await query.edit_message_text(stats_text, parse_mode="Markdown", reply_markup=get_help_keyboard())
    
    elif data == "list_channels":
        if not SEARCH_CHANNELS:
            list_text = "📭 لیست کانال‌ها خالی است."
        else:
            list_text = "📋 **لیست کانال‌های جستجو:**\n\n"
            for i, ch in enumerate(SEARCH_CHANNELS, 1):
                list_text += f"{i}. @{ch}\n"
        
        await query.edit_message_text(list_text, parse_mode="Markdown", reply_markup=get_help_keyboard())
    
    elif data == "about":
        about_text = (
            "❓ **درباره ربات**\n\n"
            "📌 این ربات برای پیدا کردن نسخه Open Access مقالات علمی طراحی شده است.\n\n"
            "🔹 **منابع جستجو:**\n"
            "• Sci-Hub\n"
            "• PubMed\n"
            "• Crossref\n"
            "• Unpaywall\n"
            "• Semantic Scholar\n"
            "• arXiv\n"
            "• CORE\n"
            "• BASE\n"
            "• DOAJ\n"
            "• و کانال‌های تلگرام\n\n"
            "🔹 **توسعه‌دهنده:** @Mohammadsh7\n"
            "🔹 **نسخه:** 2.0.0\n"
            "🔹 **وضعیت:** 🟢 فعال"
        )
        await query.edit_message_text(about_text, parse_mode="Markdown", reply_markup=get_help_keyboard())
    
    elif data == "back_to_main":
        # بازگشت به منوی اصلی
        await query.edit_message_text(
            "👋 به منوی اصلی بازگشتید.\n\n"
            "DOI یا عنوان مقاله را ارسال کنید یا از دکمه‌ها استفاده کنید:",
            reply_markup=get_main_keyboard()
        )

# ======================================================
# دستور: اضافه کردن کانال
# ======================================================
async def add_channel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """اضافه کردن کانال جدید به لیست جستجو"""
    if not context.args:
        await update.message.reply_text(
            "❌ لطفاً نام کانال را وارد کنید.\n"
            "مثال: `/add_channel nexus_aaron`\n\n"
            "📌 نام کانال را بدون @ وارد کنید."
        )
        return
    
    channel = context.args[0].replace("@", "")
    if channel in SEARCH_CHANNELS:
        await update.message.reply_text(f"ℹ️ کانال @{channel} قبلاً در لیست وجود دارد.")
        return
    
    SEARCH_CHANNELS.append(channel)
    await update.message.reply_text(
        f"✅ کانال @{channel} به لیست جستجو اضافه شد.\n\n"
        f"📋 لیست فعلی: {', '.join([f'@{ch}' for ch in SEARCH_CHANNELS])}"
    )

# ======================================================
# دستور: حذف کانال
# ======================================================
async def remove_channel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """حذف کانال از لیست جستجو"""
    if not context.args:
        await update.message.reply_text(
            "❌ لطفاً نام کانال را وارد کنید.\n"
            "مثال: `/remove_channel nexus_aaron`"
        )
        return
    
    channel = context.args[0].replace("@", "")
    if channel not in SEARCH_CHANNELS:
        await update.message.reply_text(f"ℹ️ کانال @{channel} در لیست وجود ندارد.")
        return
    
    SEARCH_CHANNELS.remove(channel)
    await update.message.reply_text(
        f"✅ کانال @{channel} از لیست جستجو حذف شد.\n\n"
        f"📋 لیست فعلی: {', '.join([f'@{ch}' for ch in SEARCH_CHANNELS])}"
    )

# ======================================================
# دستور: نمایش لیست کانال‌ها
# ======================================================
async def list_channels(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """نمایش لیست کانال‌های جستجو"""
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
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # ============================================================
    # 1. اعتبارسنجی ورودی
    # ============================================================
    # بررسی وجود پیام
    if not update.message:
        return
    
    # بررسی وجود متن در پیام
    if not update.message.text:
        await update.message.reply_text(
            "❌ لطفاً یک متن معتبر ارسال کن (عنوان مقاله یا DOI).\n\n"
            "💡 می‌توانید از دکمه /start برای راهنمایی استفاده کنید."
        )
        return
    
    text = update.message.text.strip()
    
    # اگر پیام خالی بود
    if not text:
        await update.message.reply_text(
            "❌ لطفاً یک متن معتبر ارسال کن.\n\n"
            "💡 برای راهنمایی، دکمه /start را بزنید."
        )
        return
    
    # اگر پیام با / شروع شد (دستور است)، پردازش نمی‌شود
    if text.startswith('/'):
        return
    
    # لاگ دریافت پیام (برای عیب‌یابی)
    print(f"📩 Received message: {text[:100]}...")
    
    # ============================================================
    # 2. استخراج هوشمند query از ورودی کاربر
    # ============================================================
    # ابتدا بررسی کن که آیا کاربر یک DOI کامل (با URL) فرستاده یا خالص
    doi_match = DOI_PATTERN.search(text)
    
    if doi_match:
        # اگر DOI پیدا شد، از آن استفاده کن
        query = doi_match.group(0)
        print(f"🔍 Extracted DOI: {query}")
    else:
        # در غیر این صورت از کل متن به عنوان query استفاده کن
        query = text
        print(f"🔍 Using text as query: {query[:100]}...")
    
    # ============================================================
    # 3. Check cache (Supabase)
    # ============================================================
    print(f"🔍 Checking cache for: {query}")
    cached = get_cached(query)
    if cached:
        print(f"✅ Cache hit for: {query}")
        await context.bot.send_document(
            chat_id=update.effective_chat.id,
            document=cached["file_id"],
            caption=f"📄 از کش ارسال شد\n\n📌 {cached.get('title', '')}"
        )
        return
    
    # ============================================================
    # 4. Check temp cache (اگر Supabase کار نمی‌کند)
    # ============================================================
    if query in TEMP_CACHE:
        print(f"✅ Temp cache hit for: {query}")
        await context.bot.send_document(
            chat_id=update.effective_chat.id,
            document=TEMP_CACHE[query]["file_id"],
            caption=f"📄 از کش موقت ارسال شد\n\n📌 {TEMP_CACHE[query].get('title', '')}"
        )
        return
    
    # ============================================================
    # 5. Search (با اولویت‌بندی جدید)
    # ============================================================
    print(f"🔍 Searching for: {query}")
    await update.message.reply_text(
        "🔎 در حال جستجو در منابع Open Access...\n"
        "⏳ این عمل ممکن است چند ثانیه طول بکشد."
    )
    
    result = search_open_access(query)
    if not result:
        print(f"❌ No results found for: {query}")
        await update.message.reply_text(
            "❌ مقاله پیدا نشد.\n\n"
            "💡 **نکات:**\n"
            "• مطمئن شوید DOI یا عنوان درست است\n"
            "• برخی مقالات ممکن است پولی باشند\n"
            "• از DOI استفاده کنید (مثلاً 10.1038/...)\n"
            "• برای راهنمایی بیشتر، /start را بزنید"
        )
        return
    
    print(f"✅ Found result: {result.get('title', 'Unknown')[:50]}...")
    
    try:
        # ============================================================
        # 6. دانلود PDF با هدرهای مناسب
        # ============================================================
        await update.message.reply_text("📥 در حال دانلود PDF...")
        
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
            "Accept": "application/pdf, text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
            "Connection": "keep-alive",
        }
        
        print(f"📥 Downloading PDF from: {result['pdf_url']}")
        pdf_resp = requests.get(result["pdf_url"], headers=headers, timeout=90, allow_redirects=True)
        
        # بررسی وضعیت دانلود
        if pdf_resp.status_code != 200:
            print(f"❌ Download failed with status: {pdf_resp.status_code}")
            await update.message.reply_text(f"❌ دانلود PDF ناموفق بود. (کد: {pdf_resp.status_code})")
            return
        
        # ============================================================
        # 7. بررسی اینکه آیا محتوا واقعاً PDF است
        # ============================================================
        content_type = pdf_resp.headers.get('content-type', '').lower()
        content_length = len(pdf_resp.content)
        print(f"📄 Content type: {content_type}, Size: {content_length} bytes")
        
        # اگر محتوا HTML بود، تلاش مجدد برای پیدا کردن PDF
        if 'text/html' in content_type or content_length < 50000:
            await update.message.reply_text("🔄 تلاش مجدد برای دریافت PDF...")
            
            # تلاش با هدرهای مختلف
            headers["Accept"] = "application/pdf"
            pdf_resp = requests.get(result["pdf_url"], headers=headers, timeout=90, allow_redirects=True)
            
            if pdf_resp.status_code != 200:
                print(f"❌ Retry download failed with status: {pdf_resp.status_code}")
                await update.message.reply_text("❌ دانلود PDF ناموفق بود.")
                return
            
            # بررسی مجدد محتوا
            content_type = pdf_resp.headers.get('content-type', '').lower()
            content_length = len(pdf_resp.content)
            print(f"📄 Retry content type: {content_type}, Size: {content_length} bytes")
        
        # اگر هنوز PDF نیست یا حجم فایل کم است
        if 'application/pdf' not in content_type and not pdf_resp.url.endswith('.pdf'):
            print(f"❌ Not a PDF file. Content type: {content_type}")
            await update.message.reply_text(f"⚠️ فایل دانلود شده PDF نیست. (نوع: {content_type})")
            return
        
        if content_length < 50000:  # کمتر از 50 کیلوبایت
            print(f"❌ File too small: {content_length} bytes")
            await update.message.reply_text("⚠️ فایل دانلود شده بسیار کوچک است. احتمالاً مقاله در دسترس نیست.")
            return
        
        # ============================================================
        # 8. ساخت کپشن با هشتگ ناشر
        # ============================================================
        title = result["title"]
        doi = query if query.startswith("10.") else result.get("doi", "")
        publisher = "unknown"
        hashtag = ""
        if doi.startswith("10."):
            try:
                publisher_part = doi.split("/")[0].replace("10.", "")
                publisher = PUBLISHER_MAP.get(publisher_part, publisher_part)
                hashtag = f"#pub_{publisher}"
            except:
                pass
        
        if hashtag:
            caption = f"{title}\n\n{hashtag}\n{doi} (https://doi.org/{doi})"
        else:
            caption = f"{title}\n\n{doi} (https://doi.org/{doi})"
        
        # ============================================================
        # 9. ذخیره در کانال و کش
        # ============================================================
        await update.message.reply_text("📤 در حال ذخیره در کانال...")
        
        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as f:
            f.write(pdf_resp.content)
            f.flush()
            temp_path = f.name
            
            channel_msg = await context.bot.send_document(
                chat_id=CHANNEL_ID,
                document=open(temp_path, 'rb'),
                caption=caption
            )
            file_id = channel_msg.document.file_id
            
            # پاک کردن فایل موقت
            os.remove(temp_path)
        
        # ============================================================
        # 10. ذخیره در Supabase و کش موقت
        # ============================================================
        save_paper(query=query, title=title, file_id=file_id, source=result["source"])
        TEMP_CACHE[query] = {"title": title, "file_id": file_id}
        print(f"✅ Paper saved to cache: {title[:50]}...")
        
        # ============================================================
        # 11. ارسال به کاربر با دکمه‌های تعاملی
        # ============================================================
        keyboard = [
            [
                InlineKeyboardButton("📥 دانلود مجدد", callback_data="download_again"),
                InlineKeyboardButton("🔍 جستجوی جدید", switch_inline_query_current_chat=""),
            ],
            [
                InlineKeyboardButton("📚 منوی اصلی", callback_data="back_to_main"),
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await context.bot.send_document(
            chat_id=update.effective_chat.id,
            document=file_id,
            caption=f"📄 {title}\n📚 منبع: {result['source']}\n✅ ذخیره شده در کش برای دفعات بعد",
            reply_markup=reply_markup
        )
        print(f"✅ Paper sent to user: {update.effective_chat.id}")
        
    except requests.exceptions.Timeout:
        print("❌ Download timeout")
        await update.message.reply_text("⏰ زمان دانلود به پایان رسید. لطفاً دوباره تلاش کنید.")
    except requests.exceptions.RequestException as e:
        print(f"❌ Download request error: {e}")
        await update.message.reply_text(f"❌ خطا در دانلود: {str(e)}")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        await update.message.reply_text(f"⚠️ خطا: {str(e)}")

# ======================================================
# تابع اصلی
# ======================================================
def main():
    print("🤖 Starting PaperBot...")
    print(f"📚 Search channels: {SEARCH_CHANNELS}")
    print(f"📚 Publisher map: {len(PUBLISHER_MAP)} publishers")
    
    app = Application.builder().token(BOT_TOKEN).build()
    
    # ذخیره لیست کانال‌ها در context
    app.bot_data['channels'] = SEARCH_CHANNELS
    
    # هندلرها
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("add_channel", add_channel))
    app.add_handler(CommandHandler("remove_channel", remove_channel))
    app.add_handler(CommandHandler("list_channels", list_channels))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.add_handler(CallbackQueryHandler(button_handler))
    
    # ============================================================
    # انتخاب روش اجرا (Webhook یا Polling)
    # ============================================================
    # تشخیص محیط: اگر در Render هستیم، از Webhook استفاده کن
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
        # در محیط محلی، از Polling استفاده کن
        print("🚀 Starting with Polling (local mode)")
        app.run_polling()

if __name__ == "__main__":
    main()
