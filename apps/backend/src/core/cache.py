"""
Redis Cache Service
Provides caching decorators and service for expensive operations
"""

from __future__ import annotations

from collections.abc import Callable
from functools import wraps
import hashlib
import json
import logging
from typing import TYPE_CHECKING, Any, ParamSpec, TypeVar

if TYPE_CHECKING:
    import redis.asyncio as redis
else:
    try:
        import redis.asyncio as redis
    except ImportError:
        redis = None

logger = logging.getLogger(__name__)

P = ParamSpec("P")
T = TypeVar("T")


class CacheService:
    """
    Redis-backed caching service with TTL support

    Features:
    - Async Redis operations
    - JSON serialization
    - TTL management
    - Cache invalidation
    - Key namespacing
    """

    def __init__(self, redis_url: str = "redis://localhost:6379/0", namespace: str = "myhibachi"):
        """
        Initialize cache service

        Args:
            redis_url: Redis connection URL
            namespace: Key namespace prefix
        """
        self.namespace = namespace
        self._redis_url = redis_url
        self._client: redis.Redis[str] | None = None

    async def connect(self):
        """Connect to Redis"""
        if redis is None:
            logger.warning("redis package not installed, caching disabled")
            return

        try:
            self._client = await redis.from_url(
                self._redis_url, encoding="utf-8", decode_responses=True
            )
            await self._client.ping()
            logger.info(f"✅ Redis cache connected: {self._redis_url}")
        except Exception as e:
            logger.exception(f"Failed to connect to Redis at {self._redis_url}: {e}")
            self._client = None

    async def disconnect(self):
        """Close Redis connection"""
        if self._client:
            await self._client.close()
            logger.info("Redis cache disconnected")

    def _make_key(self, key: str) -> str:
        """Generate namespaced cache key"""
        return f"{self.namespace}:{key}"

    async def get(self, key: str) -> Any | None:
        """
        Get value from cache

        Args:
            key: Cache key

        Returns:
            Cached value or None if not found
        """
        if not self._client:
            return None

        try:
            value = await self._client.get(self._make_key(key))
            if value:
                return json.loads(value)
            return None
        except Exception as e:
            logger.exception(f"Cache get error for key {key}: {e}")
            return None

    async def set(self, key: str, value: Any, ttl: int | None = None) -> bool:
        """
        Set value in cache

        Args:
            key: Cache key
            value: Value to cache (must be JSON serializable)
            ttl: Time to live in seconds (None = no expiry)

        Returns:
            True if successful, False otherwise
        """
        if not self._client:
            return False

        try:
            serialized = json.dumps(value, default=str)
            namespaced_key = self._make_key(key)

            if ttl:
                await self._client.setex(namespaced_key, ttl, serialized)
            else:
                await self._client.set(namespaced_key, serialized)

            return True
        except Exception as e:
            logger.exception(f"Cache set error for key {key}: {e}")
            return False

    async def delete(self, key: str) -> bool:
        """
        Delete key from cache

        Args:
            key: Cache key

        Returns:
            True if deleted, False otherwise
        """
        if not self._client:
            return False

        try:
            await self._client.delete(self._make_key(key))
            return True
        except Exception as e:
            logger.exception(f"Cache delete error for key {key}: {e}")
            return False

    async def delete_pattern(self, pattern: str) -> int:
        """
        Delete all keys matching pattern

        Args:
            pattern: Pattern to match (e.g., "bookings:*")

        Returns:
            Number of keys deleted
        """
        if not self._client:
            return 0

        try:
            namespaced_pattern = self._make_key(pattern)
            keys = []
            async for key in self._client.scan_iter(match=namespaced_pattern):
                keys.append(key)

            if keys:
                return await self._client.delete(*keys)
            return 0
        except Exception as e:
            logger.exception(f"Cache delete pattern error for {pattern}: {e}")
            return 0

    async def exists(self, key: str) -> bool:
        """Check if key exists in cache"""
        if not self._client:
            return False

        try:
            return await self._client.exists(self._make_key(key)) > 0
        except Exception as e:
            logger.exception(f"Cache exists error for key {key}: {e}")
            return False

    async def get_ttl(self, key: str) -> int | None:
        """Get remaining TTL for key in seconds"""
        if not self._client:
            return None

        try:
            ttl = await self._client.ttl(self._make_key(key))
            return ttl if ttl > 0 else None
        except Exception as e:
            logger.exception(f"Cache TTL error for key {key}: {e}")
            return None


def cache_key_builder(*args, **kwargs) -> str:
    """
    Build cache key from function arguments

    Args:
        *args: Positional arguments
        **kwargs: Keyword arguments

    Returns:
        MD5 hash of arguments
    """
    # Filter out non-serializable arguments
    serializable_args = []
    for arg in args:
        if isinstance(arg, str | int | float | bool | type(None)):
            serializable_args.append(arg)

    serializable_kwargs = {
        k: v for k, v in kwargs.items() if isinstance(v, str | int | float | bool | type(None))
    }

    key_data = {"args": serializable_args, "kwargs": serializable_kwargs}

    key_str = json.dumps(key_data, sort_keys=True)
    return hashlib.md5(key_str.encode()).hexdigest()


def cached(ttl: int = 300, key_prefix: str = "", key_builder: Callable | None = None):
    """
    Decorator for caching function results

    Args:
        ttl: Cache TTL in seconds (default: 5 minutes)
        key_prefix: Prefix for cache key
        key_builder: Custom function to build cache key from args

    Example:
        @cached(ttl=600, key_prefix="dashboard")
        async def get_dashboard_stats(user_id: str):
            # Expensive computation
            return stats
    """

    def decorator(func: Callable[P, T]) -> Callable[P, T]:
        @wraps(func)
        async def wrapper(*args: P.args, **kwargs: P.kwargs) -> T:
            # Get cache service from first arg if it's self/cls
            cache_service = None
            if args and hasattr(args[0], "cache"):
                cache_service = args[0].cache

            if not cache_service:
                # No cache available, execute function normally
                return await func(*args, **kwargs)

            # Build cache key
            if key_builder:
                key_suffix = key_builder(*args, **kwargs)
            else:
                key_suffix = cache_key_builder(*args[1:], **kwargs)  # Skip self/cls

            cache_key = (
                f"{key_prefix}:{func.__name__}:{key_suffix}"
                if key_prefix
                else f"{func.__name__}:{key_suffix}"
            )

            # Try to get from cache
            cached_value = await cache_service.get(cache_key)

            # Extract key prefix for logging (without exposing full key for security)
            key_prefix_part = cache_key.split(":")[0] if ":" in cache_key else "unknown"

            if cached_value is not None:
                logger.debug("Cache HIT", extra={"key_prefix": key_prefix_part})
                return cached_value

            # Cache miss, execute function
            logger.debug("Cache MISS", extra={"key_prefix": key_prefix_part})
            result = await func(*args, **kwargs)

            # Store in cache
            await cache_service.set(cache_key, result, ttl=ttl)

            return result

        return wrapper

    return decorator


def invalidate_cache(pattern: str):
    """
    Decorator to invalidate cache after function execution

    Args:
        pattern: Cache key pattern to invalidate (e.g., "bookings:*")

    Example:
        @invalidate_cache("bookings:*")
        async def create_booking(data):
            # Create booking
            return booking
    """

    def decorator(func: Callable[P, T]) -> Callable[P, T]:
        @wraps(func)
        async def wrapper(*args: P.args, **kwargs: P.kwargs) -> T:
            result = await func(*args, **kwargs)

            # Invalidate cache
            cache_service = None
            if args and hasattr(args[0], "cache"):
                cache_service = args[0].cache

            if cache_service:
                deleted = await cache_service.delete_pattern(pattern)
                logger.info(f"Invalidated {deleted} cache keys matching {pattern}")

            return result

        return wrapper

    return decorator


# Singleton instance
_cache_service: CacheService | None = None


async def get_cache_service(redis_url: str | None = None) -> CacheService:
    """
    Get or create cache service singleton

    Args:
        redis_url: Redis connection URL (defaults to REDIS_URL env var or localhost)

    Returns:
        CacheService instance
    """
    global _cache_service

    if _cache_service is None:
        import os
        # Use provided URL, or environment variable, or fallback to localhost
        url = redis_url or os.getenv("REDIS_URL", "redis://localhost:6379/0")
        _cache_service = CacheService(url)
        await _cache_service.connect()

    return _cache_service
