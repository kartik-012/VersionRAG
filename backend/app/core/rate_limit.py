import time
import threading
from typing import Dict, List, Optional, Any
from collections import defaultdict
from app.core.config import settings


class RateLimiter:
    """
    Production-grade distributed sliding-window rate limiter with Redis ZSET support
    and automatic zero-downtime fallback to a thread-safe in-memory sliding window.
    """

    def __init__(self, redis_url: Optional[str] = settings.REDIS_URL):
        self._memory_store: Dict[str, List[float]] = defaultdict(list)
        self._lock = threading.Lock()
        self._redis_url = redis_url
        self._redis_client: Optional[Any] = None
        self._init_redis()

    def _init_redis(self) -> None:
        if not self._redis_url:
            return
        try:
            import redis  # type: ignore
            client = redis.Redis.from_url(
                self._redis_url,
                socket_connect_timeout=1.5,
                socket_timeout=1.5,
                decode_responses=True,
            )
            client.ping()
            self._redis_client = client
        except Exception:
            # Zero-downtime fallback to thread-safe in-memory sliding window
            self._redis_client = None

    @property
    def active_backend(self) -> str:
        return "redis_zset" if self._redis_client is not None else "in_memory_sliding_window"

    def is_rate_limited(
        self,
        key: str,
        max_attempts: int = settings.RATE_LIMIT_LOGIN_MAX_ATTEMPTS,
        window_seconds: int = settings.RATE_LIMIT_LOGIN_WINDOW_SECONDS,
    ) -> bool:
        now = time.time()
        window_start = now - window_seconds

        if self._redis_client is not None:
            redis_key = f"versionrag:ratelimit:{key}"
            try:
                pipe = self._redis_client.pipeline()
                pipe.zremrangebyscore(redis_key, 0, window_start)
                pipe.zcard(redis_key)
                _, current_count = pipe.execute()
                return int(current_count) >= max_attempts
            except Exception:
                self._redis_client = None

        with self._lock:
            timestamps = [t for t in self._memory_store[key] if t > window_start]
            self._memory_store[key] = timestamps
            return len(timestamps) >= max_attempts

    def record_attempt(
        self,
        key: str,
        window_seconds: int = settings.RATE_LIMIT_LOGIN_WINDOW_SECONDS,
    ) -> None:
        now = time.time()
        if self._redis_client is not None:
            redis_key = f"versionrag:ratelimit:{key}"
            try:
                pipe = self._redis_client.pipeline()
                pipe.zadd(redis_key, {f"{now:.6f}": now})
                pipe.expire(redis_key, window_seconds + 5)
                pipe.execute()
                return
            except Exception:
                self._redis_client = None

        with self._lock:
            self._memory_store[key].append(now)

    def reset(self, key: str) -> None:
        if self._redis_client is not None:
            try:
                self._redis_client.delete(f"versionrag:ratelimit:{key}")
            except Exception:
                self._redis_client = None
        with self._lock:
            if key in self._memory_store:
                del self._memory_store[key]

    def clear_all(self) -> None:
        with self._lock:
            self._memory_store.clear()


rate_limiter = RateLimiter()

