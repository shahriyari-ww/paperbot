# utils/rate_limiter.py
import asyncio
import time
from collections import defaultdict
from typing import Dict, Optional

class RateLimiter:
    """
    مدیریت محدودیت نرخ درخواست‌ها با پنجره زمانی (Time Window)
    """
    def __init__(self, max_requests: int = 10, time_window: int = 60):
        self.max_requests = max_requests
        self.time_window = time_window
        self.requests: Dict[str, list] = defaultdict(list)
    
    async def acquire(self, key: str = "default") -> bool:
        """
        تلاش برای دریافت مجوز ارسال درخواست
        """
        now = time.time()
        # حذف رکوردهای قدیمی
        self.requests[key] = [t for t in self.requests[key] if t > now - self.time_window]
        
        if len(self.requests[key]) < self.max_requests:
            self.requests[key].append(now)
            return True
        
        # محاسبه زمان انتظار
        oldest = min(self.requests[key])
        wait_time = self.time_window - (now - oldest) + 0.5
        print(f"⏳ Rate limit reached for {key}, waiting {wait_time:.2f}s")
        await asyncio.sleep(max(0, wait_time))
        return await self.acquire(key)
    
    def get_stats(self, key: str = "default") -> Dict:
        """دریافت آمار محدودیت نرخ"""
        now = time.time()
        active = [t for t in self.requests[key] if t > now - self.time_window]
        return {
            "active": len(active),
            "max": self.max_requests,
            "remaining": max(0, self.max_requests - len(active)),
        }

# نمونه سراسری برای استفاده در کل پروژه
global_rate_limiter = RateLimiter(max_requests=10, time_window=30)
