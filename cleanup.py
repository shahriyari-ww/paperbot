# cleanup.py
import os
import sys
from db import auto_cleanup, get_cache_stats

def main():
    print("=" * 50)
    print("🧹 **Cache Cleanup Started**")
    print("=" * 50)
    
    # تنظیمات پاکسازی
    MAX_CACHE_SIZE = 100      # حداکثر ۱۰۰ مقاله
    MAX_DAYS = 7              # نگهداری حداکثر ۷ روز
    
    # دریافت آمار قبل از پاکسازی
    stats_before = get_cache_stats()
    print(f"📊 Stats before cleanup: {stats_before}")
    
    # اجرای پاکسازی خودکار
    deleted = auto_cleanup(max_size=MAX_CACHE_SIZE, days=MAX_DAYS)
    
    # دریافت آمار بعد از پاکسازی
    stats_after = get_cache_stats()
    print(f"📊 Stats after cleanup: {stats_after}")
    
    print(f"✅ Cleanup completed. Total deleted: {deleted} records")
    print("=" * 50)
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
