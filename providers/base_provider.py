# providers/base_provider.py
import asyncio
from abc import ABC, abstractmethod
from typing import Optional, Dict, Any
from utils.retry import retry, RetryError
from utils.rate_limiter import global_rate_limiter

class BaseProvider(ABC):
    """
    کلاس پایه برای همه ارائه‌دهندگان مقالات
    """
    name: str = "base"
    timeout: int = 30
    max_retries: int = 3
    
    def __init__(self):
        self._stats = {
            "success": 0,
            "failure": 0,
            "total_time": 0.0,
        }
    
    @abstractmethod
    async def search(self, query: str) -> Optional[Dict[str, Any]]:
        """
        جستجو در منبع و بازگرداندن اطلاعات مقاله
        """
        pass
    
    @retry(max_attempts=3, delay=1.0, backoff=2.0, max_delay=10.0)
    async def search_with_retry(self, query: str) -> Optional[Dict[str, Any]]:
        """
        جستجو با قابلیت تلاش مجدد
        """
        # اعمال محدودیت نرخ
        await global_rate_limiter.acquire(self.name)
        
        # اجرای جستجو با ثبت زمان
        start_time = asyncio.get_event_loop().time()
        try:
            result = await self.search(query)
            self._stats["success"] += 1
            return result
        except Exception as e:
            self._stats["failure"] += 1
            raise
        finally:
            elapsed = asyncio.get_event_loop().time() - start_time
            self._stats["total_time"] += elapsed
            print(f"⏱️ {self.name} search took {elapsed:.2f}s (Success: {self._stats['success']}, Failure: {self._stats['failure']})")
    
    def get_stats(self) -> Dict[str, Any]:
        """دریافت آمار عملکرد ارائه‌دهنده"""
        total = self._stats["success"] + self._stats["failure"]
        return {
            "name": self.name,
            "success": self._stats["success"],
            "failure": self._stats["failure"],
            "success_rate": self._stats["success"] / total if total > 0 else 0,
            "avg_time": self._stats["total_time"] / total if total > 0 else 0,
        }
