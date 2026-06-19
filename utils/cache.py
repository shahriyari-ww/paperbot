# utils/cache.py
from typing import Optional, Dict, Any
from db import get_cached, save_paper

class CacheManager:
    """
    مدیریت کش با لایه‌های مختلف
    """
    def __init__(self):
        self.temp_cache: Dict[str, Dict[str, Any]] = {}
    
    def get(self, query: str) -> Optional[Dict[str, Any]]:
        """
        جستجو در هر دو لایه کش
        """
        # 1. Supabase (دائمی)
        cached = get_cached(query)
        if cached:
            print(f"✅ Cache hit (Supabase): {query}")
            return cached
        
        # 2. Temporary (موقت)
        if query in self.temp_cache:
            print(f"✅ Cache hit (Temp): {query}")
            return self.temp_cache[query]
        
        return None
    
    def set(self, query: str, data: Dict[str, Any]) -> None:
        """
        ذخیره در هر دو لایه کش
        """
        # ذخیره در Supabase
        save_paper(
            query=query,
            title=data.get("title", "Unknown"),
            file_id=data.get("file_id", ""),
            source=data.get("source", "unknown"),
        )
        
        # ذخیره در کش موقت
        self.temp_cache[query] = data
        print(f"✅ Cached: {query}")

# نمونه سراسری
cache_manager = CacheManager()
