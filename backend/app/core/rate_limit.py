import time
from typing import Dict, List
from collections import defaultdict
from app.core.config import settings

class RateLimiter:
    """Sliding-window rate limiter with in-memory fallback and Redis support."""
    def __init__(self):
        self._memory_store: Dict[str, List[float]] = defaultdict(list)

    def is_rate_limited(
        self,
        key: str,
        max_attempts: int = settings.RATE_LIMIT_LOGIN_MAX_ATTEMPTS,
        window_seconds: int = settings.RATE_LIMIT_LOGIN_WINDOW_SECONDS
    ) -> bool:
        now = time.time()
        window_start = now - window_seconds
        
        # Clean up timestamps older than window
        timestamps = [t for t in self._memory_store[key] if t > window_start]
        self._memory_store[key] = timestamps
        
        if len(timestamps) >= max_attempts:
            return True
        
        return False

    def record_attempt(self, key: str):
        self._memory_store[key].append(time.time())

    def reset(self, key: str):
        if key in self._memory_store:
            del self._memory_store[key]

    def clear_all(self):
        self._memory_store.clear()

rate_limiter = RateLimiter()
