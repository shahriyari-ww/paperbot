# app.py
import os
import re
import tempfile
import requests
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters, ContextTypes
from config import BOT_TOKEN, CHANNEL_ID, SEARCH_CHANNELS, PUBLISHER_MAP
from db import get_cached, save_paper
from search_service import search_open_access

# ======================================================
# کش موقت در حافظه
# ======================================================
TEMP_CACHE = {}

# الگوی تشخیص DOI
DOI_PATTERN = re.compile(r'10\.\d{4,9}/[-._;()/:A-Z0-9]+', re.IGNORECASE)

# ======================================================
# توابع کمکی برای دکمه‌ها
# ======================================================

def get_main_keyboard():
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
    keyboard = [
        [InlineKeyboardButton("🔙 بازگشت به منوی اصلی", callback_data="back_to_main")]
    ]
    return InlineKeyboardMarkup(keyboard)

# ======================================================
# دستور START
# ======================================================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
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
# پردازش دکمه‌ها
# ======================================================
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
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
        await query.edit_message_text(help_text, parse_mode="Markdown", reply_markup=get_help_keyboard())
    
    elif data == "stats":
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
            "• Crossref\n"
            "• Unpaywall\n"
            "• Sci-Hub\n"
            "• PubMed\n"
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
        await query.edit_message_text(
            "👋 به منوی اصلی بازگشتید.\n\n"
            "DOI یا عنوان مقاله را ارسال کنید یا از دکمه‌ها استفاده کنید:",
            reply_markup=get_main_keyboard()
        )

# ======================================================
# دستورات مدیریت کانال
# ======================================================
async def add_channel(update: Update, context: ContextTypes.DEFAULT_TYPE):
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

async def remove_channel(update: Update, context: ContextTypes.DEFAULT_TYPE):
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

async def list_channels(update: Update, context: ContextTypes.DEFAULT_TYPE):
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
    # اعتبارسنجی
    if not update.message or not update.message.text:
        return
    
    text = update.message.text.strip()
    if not text or text.startswith('/'):
        return
    
    print(f"📩 Received message: {text[:100]}...")
    
    # استخراج DOI
    doi_match = DOI_PATTERN.search(text)
    query = doi_match.group(0) if doi_match else text
    print(f"🔍 Extracted DOI: {query}")
    
    # بررسی کش
    cached = get_cached(query)
    if cached:
        await context.bot.send_document(
            chat_id=update.effective_chat.id,
            document=cached["file_id"],
            caption=f"📄 از کش ارسال شد\n\n📌 {cached.get('title', '')}"
        )
        return
    
    if query in TEMP_CACHE:
        await context.bot.send_document(
            chat_id=update.effective_chat.id,
            document=TEMP_CACHE[query]["file_id"],
            caption=f"📄 از کش موقت ارسال شد\n\n📌 {TEMP_CACHE[query].get('title', '')}"
        )
        return
    
    # جستجو
    await update.message.reply_text("🔎 در حال جستجو در منابع Open Access...\n⏳ این عمل ممکن است چند ثانیه طول بکشد.")
    
    result = search_open_access(query)
    if not result:
        await update.message.reply_text("❌ مقاله پیدا نشد.")
        return
    
    try:
        # دانلود PDF
        await update.message.reply_text("📥 در حال دانلود PDF...")
        
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Accept": "application/pdf,text/html,*/*",
        }
        
        pdf_resp = requests.get(result["pdf_url"], headers=headers, timeout=90, allow_redirects=True)
        
        if pdf_resp.status_code != 200:
            await update.message.reply_text(f"❌ دانلود PDF ناموفق بود. (کد: {pdf_resp.status_code})")
            return
        
        # بررسی محتوا
        content_type = pdf_resp.headers.get('content-type', '').lower()
        content_length = len(pdf_resp.content)
        
        if 'text/html' in content_type or content_length < 50000:
            await update.message.reply_text("🔄 تلاش مجدد برای دریافت PDF...")
            headers["Accept"] = "application/pdf"
            pdf_resp = requests.get(result["pdf_url"], headers=headers, timeout=90, allow_redirects=True)
            
            if pdf_resp.status_code != 200:
                await update.message.reply_text("❌ دانلود PDF ناموفق بود.")
                return
            
            content_type = pdf_resp.headers.get('content-type', '').lower()
            content_length = len(pdf_resp.content)
        
        if 'application/pdf' not in content_type and not pdf_resp.url.endswith('.pdf'):
            await update.message.reply_text(f"⚠️ فایل دانلود شده PDF نیست. (نوع: {content_type})")
            return
        
        if content_length < 50000:
            await update.message.reply_text("⚠️ فایل دانلود شده بسیار کوچک است.")
            return
        
        # ساخت کپشن
        title = result.get("title", "Unknown Title")
        authors = result.get("authors", "Unknown Authors")
        journal = result.get("journal", "Unknown Journal")
        year = result.get("year", "Unknown Year")
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
        
        full_caption = f"""📄 **{title}**

📝 **Authors:** {authors}
📅 **Published:** {year}
📚 **Journal:** {journal}
🔗 **DOI:** {doi} (https://doi.org/{doi})"""
        
        channel_caption = f"{title}\n\n{hashtag}\n{doi} (https://doi.org/{doi})"
        
        # ذخیره در کانال
        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as f:
            f.write(pdf_resp.content)
            f.flush()
            temp_path = f.name
            
            channel_msg = await context.bot.send_document(
                chat_id=CHANNEL_ID,
                document=open(temp_path, 'rb'),
                caption=channel_caption
            )
            file_id = channel_msg.document.file_id
            os.remove(temp_path)
        
        # ذخیره در کش
        save_paper(query=query, title=title, file_id=file_id, source=result.get("source", "unknown"))
        TEMP_CACHE[query] = {"title": title, "file_id": file_id}
        
        # ارسال به کاربر
        keyboard = [
            [
                InlineKeyboardButton("📥 دانلود مجدد", callback_data="download_again"),
                InlineKeyboardButton("🔍 جستجوی جدید", switch_inline_query_current_chat=""),
            ],
            [
                InlineKeyboardButton("📚 منوی اصلی", callback_data="back_to_main"),
            ]
        ]
        
        await context.bot.send_document(
            chat_id=update.effective_chat.id,
            document=file_id,
            caption=full_caption,
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        
    except Exception as e:
        await update.message.reply_text(f"⚠️ خطا: {str(e)}")

# ======================================================
# تابع اصلی
# ======================================================
def main():
    print("🤖 Starting PaperBot...")
    print(f"📚 Search channels: {SEARCH_CHANNELS}")
    print(f"📚 Publisher map: {len(PUBLISHER_MAP)} publishers")
    
    app = Application.builder().token(BOT_TOKEN).build()
    app.bot_data['channels'] = SEARCH_CHANNELS
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("add_channel", add_channel))
    app.add_handler(CommandHandler("remove_channel", remove_channel))
    app.add_handler(CommandHandler("list_channels", list_channels))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.add_handler(CallbackQueryHandler(button_handler))
    
    is_render = os.environ.get("RENDER") or os.environ.get("PORT")
    
    if is_render:
        port = int(os.environ.get("PORT", 10000))
        webhook_url = f"https://paperbot-ng4v.onrender.com/"
        print(f"🚀 Starting with Webhook on port {port}")
        app.run_webhook(listen="0.0.0.0", port=port, webhook_url=webhook_url)
    else:
        print("🚀 Starting with Polling (local mode)")
        app.run_polling()

if __name__ == "__main__":
    main()
