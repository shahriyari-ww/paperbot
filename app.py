# app.py
import os
import tempfile
import requests
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from config import BOT_TOKEN, CHANNEL_ID
from db import get_cached, save_paper
from search_service import search_open_access

# ---------------- START COMMAND ----------------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "سلام 👋\n\nDOI یا عنوان مقاله را ارسال کن تا نسخه Open Access آن بررسی شود."
    )

# ---------------- MAIN HANDLER ----------------
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.message.text.strip()
    
    # 1. check cache (Supabase)
    cached = get_cached(query)
    if cached:
        await context.bot.send_document(
            chat_id=update.effective_chat.id,
            document=cached["file_id"],
            caption="📄 از کش ارسال شد"
        )
        return
    
    await update.message.reply_text("🔎 در حال جستجو در منابع Open Access...")
    
    # 2. search providers (arXiv etc.)
    result = search_open_access(query)
    if not result:
        await update.message.reply_text("❌ مقاله Open Access پیدا نشد.")
        return
    
    try:
        # 3. download pdf
        pdf_resp = requests.get(result["pdf_url"], timeout=60)
        if pdf_resp.status_code != 200:
            await update.message.reply_text("❌ دانلود PDF ناموفق بود.")
            return
        
        # 4. save temp file
        with tempfile.NamedTemporaryFile(suffix=".pdf") as f:
            f.write(pdf_resp.content)
            f.flush()
            
            # 5. upload to private channel (Telegram cache storage)
            channel_msg = await context.bot.send_document(
                chat_id=CHANNEL_ID,
                document=f.name,
                caption=result["title"]
            )
            file_id = channel_msg.document.file_id
        
        # 6. save to Supabase
        save_paper(
            query=query,
            title=result["title"],
            file_id=file_id,
            source=result["source"]
        )
        
        # 7. send to user
        await context.bot.send_document(
            chat_id=update.effective_chat.id,
            document=file_id,
            caption="📄 ارسال شد"
        )
        
    except Exception as e:
        await update.message.reply_text(f"⚠️ خطا: {str(e)}")

# ---------------- MAIN ----------------
def main():
    # ایجاد اپلیکیشن
    app = Application.builder().token(BOT_TOKEN).build()
    
    # اضافه کردن هندلرها
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    # دریافت پورت از محیط (Render به طور خودکار تنظیم می‌کند)
    port = int(os.environ.get("PORT", 10000))
    
    # اجرا با Webhook (برای محیط تولید در Render)
    app.run_webhook(
        listen="0.0.0.0",
        port=port,
        webhook_url=f"https://paperbot-ng4v.onrender.com/"  # ← آدرس واقعی خود را جایگزین کنید
    )

if __name__ == "__main__":
    main()
