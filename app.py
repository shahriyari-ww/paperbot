# app.py
import os
import tempfile
import requests
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from config import BOT_TOKEN, CHANNEL_ID, SEARCH_CHANNELS, PUBLISHER_MAP
from db import get_cached, save_paper
from search_service import search_open_access

# کش موقت در حافظه (برای مواقعی که Supabase کار نمی‌کند)
TEMP_CACHE = {}

# ---------------- START COMMAND ----------------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "سلام 👋\n\n"
        "DOI یا عنوان مقاله را ارسال کن تا نسخه Open Access آن بررسی شود.\n\n"
        "📌 ربات ابتدا در کش، سپس در کانال‌های مشخص شده جستجو می‌کند.\n\n"
        "📚 کانال‌های جستجو:\n" + "\n".join([f"• @{ch}" for ch in SEARCH_CHANNELS])
    )

# ---------------- COMMAND: ADD CHANNEL ----------------
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

# ---------------- COMMAND: REMOVE CHANNEL ----------------
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

# ---------------- COMMAND: LIST CHANNELS ----------------
async def list_channels(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """نمایش لیست کانال‌های جستجو"""
    if not SEARCH_CHANNELS:
        await update.message.reply_text("📭 لیست کانال‌ها خالی است.")
        return
    
    message = "📚 لیست کانال‌های جستجو:\n\n"
    for i, ch in enumerate(SEARCH_CHANNELS, 1):
        message += f"{i}. @{ch}\n"
    
    await update.message.reply_text(message)

# ---------------- MAIN HANDLER ----------------
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.message.text.strip()
    
    if not query:
        await update.message.reply_text("❌ لطفاً یک متن معتبر ارسال کن.")
        return
    
    # 1. Check cache (Supabase)
    cached = get_cached(query)
    if cached:
        await context.bot.send_document(
            chat_id=update.effective_chat.id,
            document=cached["file_id"],
            caption=f"📄 از کش ارسال شد\n\n📌 {cached.get('title', '')}"
        )
        return
    
    # 2. Check temp cache (اگر Supabase کار نمی‌کند)
    if query in TEMP_CACHE:
        await context.bot.send_document(
            chat_id=update.effective_chat.id,
            document=TEMP_CACHE[query]["file_id"],
            caption=f"📄 از کش موقت ارسال شد\n\n📌 {TEMP_CACHE[query].get('title', '')}"
        )
        return
    
    # 3. Search (با اولویت‌بندی جدید)
    await update.message.reply_text("🔎 جستجو در منابع Open Access...")
    result = search_open_access(query)
    if not result:
        await update.message.reply_text("❌ مقاله پیدا نشد.")
        return
    
    try:
        # دانلود PDF با هدرهای مناسب
        await update.message.reply_text("📥 در حال دانلود PDF...")
        
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
            "Accept": "application/pdf, text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
            "Connection": "keep-alive",
        }
        
        pdf_resp = requests.get(result["pdf_url"], headers=headers, timeout=90, allow_redirects=True)
        
        # بررسی وضعیت دانلود
        if pdf_resp.status_code != 200:
            await update.message.reply_text(f"❌ دانلود PDF ناموفق بود. (کد: {pdf_resp.status_code})")
            return
        
        # بررسی اینکه آیا محتوا واقعاً PDF است
        content_type = pdf_resp.headers.get('content-type', '').lower()
        content_length = len(pdf_resp.content)
        
        # اگر محتوا HTML بود، تلاش مجدد برای پیدا کردن PDF
        if 'text/html' in content_type or content_length < 50000:
            await update.message.reply_text("🔄 تلاش مجدد برای دریافت PDF...")
            
            # تلاش با هدرهای مختلف
            headers["Accept"] = "application/pdf"
            pdf_resp = requests.get(result["pdf_url"], headers=headers, timeout=90, allow_redirects=True)
            
            if pdf_resp.status_code != 200:
                await update.message.reply_text("❌ دانلود PDF ناموفق بود.")
                return
            
            # بررسی مجدد محتوا
            content_type = pdf_resp.headers.get('content-type', '').lower()
            content_length = len(pdf_resp.content)
        
        # اگر هنوز PDF نیست یا حجم فایل کم است
        if 'application/pdf' not in content_type and not pdf_resp.url.endswith('.pdf'):
            await update.message.reply_text(f"⚠️ فایل دانلود شده PDF نیست. (نوع: {content_type})")
            # ادامه نمی‌دهیم
            return
        
        if content_length < 50000:  # کمتر از 50 کیلوبایت
            await update.message.reply_text("⚠️ فایل دانلود شده بسیار کوچک است. احتمالاً مقاله در دسترس نیست.")
            return
        
        # ساخت کپشن با هشتگ ناشر
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
        
        # ذخیره در کانال و کش
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
        
        # ذخیره در Supabase و کش موقت
        save_paper(query=query, title=title, file_id=file_id, source=result["source"])
        TEMP_CACHE[query] = {"title": title, "file_id": file_id}
        
        # ارسال به کاربر
        await context.bot.send_document(
            chat_id=update.effective_chat.id,
            document=file_id,
            caption=f"📄 {title}\n📚 منبع: {result['source']}"
        )
        
    except requests.exceptions.Timeout:
        await update.message.reply_text("⏰ زمان دانلود به پایان رسید. لطفاً دوباره تلاش کنید.")
    except requests.exceptions.RequestException as e:
        await update.message.reply_text(f"❌ خطا در دانلود: {str(e)}")
    except Exception as e:
        await update.message.reply_text(f"⚠️ خطا: {str(e)}")

# ---------------- MAIN ----------------
def main():
    app = Application.builder().token(BOT_TOKEN).build()
    
    # ذخیره لیست کانال‌ها در context
    app.bot_data['channels'] = SEARCH_CHANNELS
    
    # هندلرها
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("add_channel", add_channel))
    app.add_handler(CommandHandler("remove_channel", remove_channel))
    app.add_handler(CommandHandler("list_channels", list_channels))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    port = int(os.environ.get("PORT", 10000))
    app.run_webhook(
        listen="0.0.0.0",
        port=port,
        webhook_url=f"https://paperbot-ng4v.onrender.com/"
    )

if __name__ == "__main__":
    main()
