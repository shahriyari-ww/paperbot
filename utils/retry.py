# utils/retry.py
import asyncio
import time
from functools import wraps
from typing import Type, Union, Tuple, Optional

class RetryError(Exception):
    pass

def retry(
    max_attempts: int = 3,
    delay: float = 1.0,
    backoff: float = 2.0,
    exceptions: Union[Type[Exception], Tuple[Type[Exception], ...]] = Exception,
    max_delay: Optional[float] = None,
):
    """
    دکوریتور تلاش مجدد با Backoff تصاعدی
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            _delay = delay
            last_exception = None
            
            for attempt in range(1, max_attempts + 1):
                try:
                    return await func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e
                    if attempt == max_attempts:
                        raise RetryError(f"Failed after {max_attempts} attempts: {e}") from e
                    
                    # محاسبه تأخیر با Backoff
                    sleep_time = min(_delay, max_delay or float('inf'))
                    print(f"🔄 Retry {attempt}/{max_attempts} for {func.__name__} in {sleep_time:.2f}s (Error: {e})")
                    
                    await asyncio.sleep(sleep_time)
                    _delay *= backoff  # افزایش تصاعدی
            
            raise last_exception  # fallback
        return wrapper
    return decorator
