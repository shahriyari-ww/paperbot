# db.py
from supabase import create_client
from config import SUPABASE_URL, SUPABASE_KEY

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

def get_cached(query: str):
    """دریافت مقاله از کش"""
    try:
        result = supabase.table("papers").select("*").eq("query", query).execute()
        if result.data and len(result.data) > 0:
            return result.data[0]
        return None
    except Exception as e:
        print(f"⚠️ Error getting cached paper: {e}")
        return None

def save_paper(query, title, file_id, source):
    """ذخیره مقاله در کش"""
    try:
        supabase.table("papers").insert({
            "query": query,
            "title": title,
            "file_id": file_id,
            "source": source
        }).execute()
        print(f"✅ Paper saved to cache: {title}")
    except Exception as e:
        print(f"⚠️ Error saving paper: {e}")
