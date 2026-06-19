import os

BOT_TOKEN = os.getenv("BOT_TOKEN", "")
SUPABASE_URL = os.getenv("SUPABASE_URL", "")
SUPABASE_KEY = os.getenv("SUPABASE_KEY", "")
CHANNEL_ID = int(os.getenv("CHANNEL_ID", "0"))
PORT = os.getenv("PORT", "10000")
