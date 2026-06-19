# db.py
from supabase import create_client
from config import SUPABASE_URL, SUPABASE_KEY
import traceback
import datetime
from typing import Optional, List, Dict, Any

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# ======================================================
# توابع اصلی کش
# ======================================================

def get_cached(query: str) -> Optional[Dict[str, Any]]:
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

def save_paper(query: str, title: str, file_id: str, source: str) -> None:
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

def get_all_cached() -> List[Dict[str, Any]]:
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

def delete_cached(query: str) -> bool:
    """
    حذف مقاله از کش
    
    Args:
        query (str): عنوان مقاله یا DOI
        
    Returns:
        bool: موفقیت عملیات
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

def clear_cache() -> bool:
    """
    پاک کردن کل کش (فقط برای مدیریت)
    
    Returns:
        bool: موفقیت عملیات
    """
    try:
        result = supabase.table("papers").delete().neq("id", 0).execute()
        print(f"🗑️ All papers deleted from cache")
        return True
    except Exception as e:
        print(f"⚠️ Error clearing cache: {e}")
        return False

# ======================================================
# توابع مدیریت حجم کش
# ======================================================

def get_cache_size() -> int:
    """
    دریافت تعداد مقالات در کش
    
    Returns:
        int: تعداد مقالات
    """
    try:
        result = supabase.table("papers").select("*", count="exact").execute()
        return result.count
    except Exception as e:
        print(f"⚠️ Error getting cache size: {e}")
        return 0

def delete_old_papers(days: int = 30) -> int:
    """
    حذف مقالات قدیمی‌تر از تعداد روز مشخص
    
    Args:
        days (int): تعداد روز برای نگهداری مقالات
        
    Returns:
        int: تعداد مقالات حذف شده
    """
    try:
        cutoff_date = datetime.datetime.now() - datetime.timedelta(days=days)
        cutoff_str = cutoff_date.isoformat()
        
        # دریافت تعداد مقالات قبل از حذف
        count_before = get_cache_size()
        
        # حذف مقالات قدیمی
        result = supabase.table("papers").delete().lt("created_at", cutoff_str).execute()
        
        deleted_count = len(result.data) if result.data else 0
        print(f"🗑️ Deleted {deleted_count} old papers (older than {days} days)")
        print(f"📊 Cache size before: {count_before}, after: {get_cache_size()}")
        
        return deleted_count
    except Exception as e:
        print(f"⚠️ Error deleting old papers: {e}")
        print(f"📋 Details: {traceback.format_exc()}")
        return 0

def get_cache_stats() -> Dict[str, Any]:
    """
    دریافت آمار کامل کش
    
    Returns:
        dict: آمار کش
    """
    try:
        total = get_cache_size()
        
        # دریافت مقالات قدیمی‌ترین و جدیدترین
        oldest = supabase.table("papers").select("*").order("created_at", asc=True).limit(1).execute()
        newest = supabase.table("papers").select("*").order("created_at", desc=True).limit(1).execute()
        
        stats = {
            "total_papers": total,
            "oldest": oldest.data[0]["created_at"] if oldest.data else None,
            "newest": newest.data[0]["created_at"] if newest.data else None,
            "sources": {},
        }
        
        # آمار بر اساس منبع
        sources = supabase.table("papers").select("source", count="exact").execute()
        for item in sources.data:
            source = item.get("source", "unknown")
            stats["sources"][source] = stats["sources"].get(source, 0) + 1
        
        return stats
    except Exception as e:
        print(f"⚠️ Error getting cache stats: {e}")
        return {"total_papers": 0, "sources": {}}

def auto_cleanup(max_size: int = 100, days: int = 30) -> int:
    """
    پاکسازی خودکار کش بر اساس حجم و زمان
    
    Args:
        max_size (int): حداکثر تعداد مقالات مجاز
        days (int): حداکثر روزهای نگهداری
        
    Returns:
        int: تعداد مقالات حذف شده
    """
    total_deleted = 0
    
    # 1. حذف مقالات قدیمی
    deleted = delete_old_papers(days)
    total_deleted += deleted
    
    # 2. اگر هنوز حجم زیاد است، قدیمی‌ترین مقالات را حذف کن
    current_size = get_cache_size()
    if current_size > max_size:
        try:
            # دریافت مقالات قدیمی برای حذف
            excess = current_size - max_size
            old_papers = supabase.table("papers").select("*").order("created_at", asc=True).limit(excess).execute()
            
            if old_papers.data:
                ids = [p["id"] for p in old_papers.data]
                result = supabase.table("papers").delete().in_("id", ids).execute()
                deleted_count = len(result.data) if result.data else 0
                total_deleted += deleted_count
                print(f"🗑️ Deleted {deleted_count} excess papers (max_size: {max_size})")
        except Exception as e:
            print(f"⚠️ Error deleting excess papers: {e}")
    
    return total_deleted
