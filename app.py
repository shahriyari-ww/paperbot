# app.py
import os
import tempfile
import requests
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from config import BOT_TOKEN, CHANNEL_ID, SEARCH_CHANNELS
from db import get_cached, save_paper
from search_service import search_open_access
from channel_search import search_in_channels

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
    
    # 1. check cache (Supabase)
    cached = get_cached(query)
    if cached:
        await context.bot.send_document(
            chat_id=update.effective_chat.id,
            document=cached["file_id"],
            caption=f"📄 از کش ارسال شد\n\n📌 {cached.get('title', '')}"
        )
        return
    
    # 2. جستجو در کانال‌های مشخص شده
    await update.message.reply_text("🔍 در حال جستجو در کانال‌های ذخیره شده...")
    
    # جستجو در کانال‌ها
    channel_result = await search_in_channels(query, context.bot, context)
    if channel_result:
        # اگر در کانال پیدا شد
        await context.bot.send_document(
            chat_id=update.effective_chat.id,
            document=channel_result["file_id"],
            caption=f"📄 از کانال @{channel_result.get('channel', 'unknown')} ارسال شد"
        )
        # ذخیره در کش
        save_paper(
            query=query,
            title=channel_result.get("title", "Unknown"),
            file_id=channel_result["file_id"],
            source="channel"
        )
        return
    
    # 3. جستجوی معمولی
    await update.message.reply_text("🔎 جستجو در منابع Open Access...")
    result = search_open_access(query)
    if not result:
        await update.message.reply_text("❌ مقاله پیدا نشد.")
        return
    
    try:
        # دانلود و ارسال (کد قبلی)
        pdf_resp = requests.get(result["pdf_url"], timeout=60)
        if pdf_resp.status_code != 200:
            await update.message.reply_text("❌ دانلود PDF ناموفق بود.")
            return
        
        with tempfile.NamedTemporaryFile(suffix=".pdf") as f:
            f.write(pdf_resp.content)
            f.flush()
            
            channel_msg = await context.bot.send_document(
                chat_id=CHANNEL_ID,
                document=f.name,
                caption=result["title"]
            )
            file_id = channel_msg.document.file_id
        
        save_paper(
            query=query,
            title=result["title"],
            file_id=file_id,
            source=result["source"]
        )
        
        await context.bot.send_document(
            chat_id=update.effective_chat.id,
            document=file_id,
            caption=f"📄 {result['title']}\n📚 منبع: {result['source']}"
        )
        
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
