# db.py
from supabase import create_client
from config import SUPABASE_URL, SUPABASE_KEY
import traceback

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

def get_cached(query: str):
    """
    دریافت مقاله از کش (Supabase)
    
    Args:
        query (str): عنوان مقاله یا DOI
        
    Returns:
        dict: اطلاعات مقاله یا None در صورت عدم یافت
    """
    try:
        result = supabase.table("papers").select("*").eq("query", query).execute()
        
        if result.data and len(result.data) > 0:
            print(f"✅ Cache hit for: {query}")
            return result.data[0]
        else:
            print(f"❌ Cache miss for: {query}")
            return None
            
    except Exception as e:
        print(f"⚠️ Error getting cached paper: {e}")
        print(f"📋 Details: {traceback.format_exc()}")
        return None

def save_paper(query, title, file_id, source):
    """
    ذخیره مقاله در کش (Supabase)
    
    Args:
        query (str): عنوان مقاله یا DOI
        title (str): عنوان مقاله
        file_id (str): شناسه فایل در تلگرام
        source (str): منبع مقاله (arxiv, pubmed, etc.)
    """
    try:
        # بررسی اینکه آیا مقاله قبلاً ذخیره شده است
        existing = supabase.table("papers").select("*").eq("query", query).execute()
        if existing.data and len(existing.data) > 0:
            print(f"ℹ️ Paper already exists in cache: {title}")
            return
        
        # ذخیره مقاله جدید
        data = {
            "query": query,
            "title": title,
            "file_id": file_id,
            "source": source
        }
        
        result = supabase.table("papers").insert(data).execute()
        print(f"✅ Paper saved to cache: {title}")
        print(f"📊 Cache size: {len(result.data)} records")
        
    except Exception as e:
        print(f"⚠️ Error saving paper: {e}")
        print(f"📋 Details: {traceback.format_exc()}")

def get_all_cached():
    """
    دریافت همه مقالات ذخیره شده در کش
    
    Returns:
        list: لیست مقالات
    """
    try:
        result = supabase.table("papers").select("*").order("created_at", desc=True).execute()
        if result.data:
            print(f"📚 Total cached papers: {len(result.data)}")
            return result.data
        return []
    except Exception as e:
        print(f"⚠️ Error getting all cached papers: {e}")
        return []

def delete_cached(query: str):
    """
    حذف مقاله از کش
    
    Args:
        query (str): عنوان مقاله یا DOI
    """
    try:
        result = supabase.table("papers").delete().eq("query", query).execute()
        if result.data and len(result.data) > 0:
            print(f"🗑️ Paper deleted from cache: {query}")
            return True
        else:
            print(f"❌ Paper not found in cache: {query}")
            return False
    except Exception as e:
        print(f"⚠️ Error deleting cached paper: {e}")
        return False

def clear_cache():
    """
    پاک کردن کل کش (فقط برای مدیریت)
    """
    try:
        result = supabase.table("papers").delete().neq("id", 0).execute()
        print(f"🗑️ All papers deleted from cache")
        return True
    except Exception as e:
        print(f"⚠️ Error clearing cache: {e}")
        return False
