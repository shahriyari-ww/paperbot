# app.py
import os
import re
import sys
import tempfile
import requests
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
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
# دستور START
# ======================================================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "سلام 👋\n\n"
        "DOI یا عنوان مقاله را ارسال کن تا نسخه Open Access آن بررسی شود.\n\n"
        "📌 ربات ابتدا در کش، سپس در کانال‌های مشخص شده جستجو می‌کند.\n\n"
        "📚 کانال‌های جستجو:\n" + "\n".join([f"• @{ch}" for ch in SEARCH_CHANNELS])
    )

# ======================================================
# دستور: اضافه کردن کانال
# ======================================================
async def add_channel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """اضافه کردن کانال جدید به لیست جستجو"""
    if not context.args:
        await update.message.reply_text("❌ لطفاً نام کانال را وارد کنید.\nمثال: /add_channel nexus_aaron")
        return
    
    channel = context.args[0].replace("@", "")
    if channel in SEARCH_CHANNELS:
        await update.message.reply_text(f"ℹ️ کانال @{channel} قبلاً در لیست وجود دارد.")
        return
    
    SEARCH_CHANNELS.append(channel)
    await update.message.reply_text(f"✅ کانال @{channel} به لیست جستجو اضافه شد.")

# ======================================================
# دستور: حذف کانال
# ======================================================
async def remove_channel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """حذف کانال از لیست جستجو"""
    if not context.args:
        await update.message.reply_text("❌ لطفاً نام کانال را وارد کنید.\nمثال: /remove_channel nexus_aaron")
        return
    
    channel = context.args[0].replace("@", "")
    if channel not in SEARCH_CHANNELS:
        await update.message.reply_text(f"ℹ️ کانال @{channel} در لیست وجود ندارد.")
        return
    
    SEARCH_CHANNELS.remove(channel)
    await update.message.reply_text(f"✅ کانال @{channel} از لیست جستجو حذف شد.")

# ======================================================
# دستور: نمایش لیست کانال‌ها
# ======================================================
async def list_channels(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """نمایش لیست کانال‌های جستجو"""
    if not SEARCH_CHANNELS:
        await update.message.reply_text("📭 لیست کانال‌ها خالی است.")
        return
    
    message = "📚 لیست کانال‌های جستجو:\n\n"
    for i, ch in enumerate(SEARCH_CHANNELS, 1):
        message += f"{i}. @{ch}\n"
    
    await update.message.reply_text(message)

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
        await update.message.reply_text("❌ لطفاً یک متن معتبر ارسال کن (عنوان مقاله یا DOI).")
        return
    
    text = update.message.text.strip()
    
    # اگر پیام خالی بود
    if not text:
        await update.message.reply_text("❌ لطفاً یک متن معتبر ارسال کن.")
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
    await update.message.reply_text("🔎 جستجو در منابع Open Access...")
    
    result = search_open_access(query)
    if not result:
        print(f"❌ No results found for: {query}")
        await update.message.reply_text("❌ مقاله پیدا نشد.")
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
        # 11. ارسال به کاربر
        # ============================================================
        await context.bot.send_document(
            chat_id=update.effective_chat.id,
            document=file_id,
            caption=f"📄 {title}\n📚 منبع: {result['source']}"
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
