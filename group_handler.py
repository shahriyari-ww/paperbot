# group_handler.py
async def handle_group_media(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """ذخیره فایل‌های ارسال‌شده در گروه"""
    if update.effective_chat.type not in ['group', 'supergroup']:
        return
    
    # اگر فایل PDF در گروه ارسال شد
    if update.message.document:
        file = update.message.document
        if file.mime_type == "application/pdf":
            # ذخیره فایل برای استفاده بعدی
            file_id = file.file_id
            title = file.file_name or "Unknown"
            # ذخیره در دیتابیس
            save_paper(
                query=title,  # می‌توانید از محتوای پیام استفاده کنید
                title=title,
                file_id=file_id,
                source="group"
            )
            await update.message.reply_text("📄 PDF در کش ذخیره شد!")
