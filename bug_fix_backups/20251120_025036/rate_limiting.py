"""
Advanced Rate Limiting with Tiered Strategy
Uses Redis for distributed rate limiting (works across multiple workers)
Falls back to in-memory limiting if Redis unavailable
"""

import hashlib
from pathlib import Path
import time
from typing import Any

from core.config import UserRole, get_settings
from fastapi import HTTPException, Request, status

# Handle Redis import gracefully
try:
    import redis.asyncio as redis

    REDIS_AVAILABLE = True
except ImportError:
    redis = None
    REDIS_AVAILABLE = False

settings = get_settings()


class RateLimiter:
    """Advanced rate limiter with Redis backend and fallback strategy"""

    def __init__(self):
        self.settings = settings
        self.redis_client = None
        self.redis_available = False
        self.rate_limit_script = None
        # Instance-based memory store for better isolation
        self._memory_store = {}

    async def _init_redis(self):
        """Initialize Redis connection with fallback"""
        if self.redis_client is None:
            try:
                if not REDIS_AVAILABLE:
                    self.redis_client = None
                    self.redis_available = False
                    return

                self.redis_client = redis.from_url(
                    settings.REDIS_URL, encoding="utf-8", decode_responses=True
                )
                # Test connection
                await self.redis_client.ping()
                self.redis_available = True

                # Load atomic rate limiting Lua script
                script_path = Path(__file__).parent / "rate_limit.lua"
                with open(script_path) as f:
                    self.rate_limit_script = self.redis_client.register_script(
                        f.read()
                    )

            except Exception:
                self.redis_client = None
                self.redis_available = False

    async def _get_user_identifier(
        self, request: Request, user: Any | None = None
    ) -> tuple[str, UserRole]:
        """Get unique identifier and role for rate limiting"""

        # Check if it's a webhook endpoint
        if request.url.path.startswith("/webhooks/"):
            webhook_key = request.headers.get(
                "authorization"
            ) or request.headers.get("x-webhook-secret")
            if webhook_key:
                hashed_key = hashlib.sha256(webhook_key.encode()).hexdigest()[
                    :16
                ]
                return f"webhook:{hashed_key}", None

        # Check if user is authenticated
        if user:
            user_role = getattr(
                user, "role", None
            )  # No default role - must be authenticated staff
            user_id = getattr(user, "id", "unknown")
            return f"user:{user_id}", user_role

        # Check for API key in headers
        api_key = request.headers.get("x-api-key")
        if api_key:
            hashed_key = hashlib.sha256(api_key.encode()).hexdigest()[:16]
            return (
                f"api:{hashed_key}",
                None,
            )  # API keys are for integrations, not role-based

        # Fall back to IP address for public users (customers don't need login)
        client_ip = request.client.host if request.client else "unknown"
        return f"ip:{client_ip}", None

    async def _get_rate_limit_config(
        self, path: str, user_role: UserRole | None
    ) -> dict[str, Any]:
        """Get rate limit configuration based on endpoint and user role"""

        # AI endpoints have special limits regardless of user role
        if "/ai/" in path:
            return self.settings.get_ai_rate_limit()

        # Webhook endpoints
        if path.startswith("/webhooks/"):
            return {
                "per_minute": self.settings.RATE_LIMIT_WEBHOOK_PER_MINUTE,
                "per_hour": self.settings.RATE_LIMIT_WEBHOOK_PER_HOUR,
                "burst": self.settings.RATE_LIMIT_WEBHOOK_BURST,
                "tier": "webhook",
            }

        # User-based limits
        return self.settings.get_rate_limit_for_user(user_role)

    async def _check_rate_limit(
        self, identifier: str, config: dict[str, Any]
    ) -> dict[str, Any]:
        """Check rate limits using sliding window algorithm"""

        await self._init_redis()

        current_time = int(time.time())
        minute_window = current_time // 60
        hour_window = current_time // 3600

        if self.redis_available and self.redis_client:
            return await self._check_redis_rate_limit(
                identifier, config, current_time, minute_window, hour_window
            )
        else:
            return await self._check_memory_rate_limit(
                identifier, config, current_time, minute_window, hour_window
            )

    async def _check_redis_rate_limit(
        self,
        identifier: str,
        config: dict[str, Any],
        current_time: int,
        minute_window: int,
        hour_window: int,
    ) -> dict[str, Any]:
        """Check rate limits using Redis with atomic Lua script to prevent race conditions"""
        # Redis keys
        minute_key = f"rate_limit:{identifier}:minute:{minute_window}"
        hour_key = f"rate_limit:{identifier}:hour:{hour_window}"

        # Execute atomic rate limit check using Lua script
        # This prevents race conditions in high-concurrency scenarios by ensuring
        # check and increment happen atomically in a single Redis operation
        result = await self.rate_limit_script(
            keys=[minute_key, hour_key],
            args=[
                config["per_minute"],  # minute_limit
                config["per_hour"],  # hour_limit
                120,  # minute_ttl (2 minutes)
                7200,  # hour_ttl (2 hours)
            ],
        )

        # Parse Lua script result
        # result[0] = 1 if allowed, 0 if denied
        # result[1] = minute_count (current or incremented)
        # result[2] = hour_count (current or incremented)
        # result[3] = limit_type (only if denied)
        allowed = result[0] == 1
        minute_count = result[1]
        hour_count = result[2]

        if not allowed:
            # Request denied - limit exceeded
            limit_type = result[3] if len(result) > 3 else "unknown"

            if limit_type == "per_minute":
                return {
                    "allowed": False,
                    "limit_type": "per_minute",
                    "current": minute_count,
                    "limit": config["per_minute"],
                    "reset_seconds": 60 - (current_time % 60),
                    "tier": config["tier"],
                }
            else:  # per_hour
                return {
                    "allowed": False,
                    "limit_type": "per_hour",
                    "current": hour_count,
                    "limit": config["per_hour"],
                    "reset_seconds": 3600 - (current_time % 3600),
                    "tier": config["tier"],
                }

        # Request allowed - counters already incremented atomically
        return {
            "allowed": True,
            "minute_remaining": config["per_minute"] - minute_count,
            "hour_remaining": config["per_hour"] - hour_count,
            "minute_reset": 60 - (current_time % 60),
            "hour_reset": 3600 - (current_time % 3600),
            "tier": config["tier"],
        }

    async def _check_memory_rate_limit(
        self,
        identifier: str,
        config: dict[str, Any],
        current_time: int,
        minute_window: int,
        hour_window: int,
    ) -> dict[str, Any]:
        """Fallback in-memory rate limiting"""

        # Clean old entries
        current_time_int = int(current_time)
        self._memory_store = {
            k: v
            for k, v in self._memory_store.items()
            if current_time_int - v.get("timestamp", 0) < 7200
        }  # Keep for 2 hours

        minute_key = f"{identifier}:minute:{minute_window}"
        hour_key = f"{identifier}:hour:{hour_window}"

        minute_count = self._memory_store.get(minute_key, {}).get("count", 0)
        hour_count = self._memory_store.get(hour_key, {}).get("count", 0)

        # Check limits
        if minute_count >= config["per_minute"]:
            return {
                "allowed": False,
                "limit_type": "per_minute",
                "current": minute_count,
                "limit": config["per_minute"],
                "reset_seconds": 60 - (current_time % 60),
                "tier": config["tier"],
            }

        if hour_count >= config["per_hour"]:
            return {
                "allowed": False,
                "limit_type": "per_hour",
                "current": hour_count,
                "limit": config["per_hour"],
                "reset_seconds": 3600 - (current_time % 3600),
                "tier": config["tier"],
            }

        # Increment counters
        self._memory_store[minute_key] = {
            "count": minute_count + 1,
            "timestamp": current_time_int,
        }
        self._memory_store[hour_key] = {
            "count": hour_count + 1,
            "timestamp": current_time_int,
        }

        return {
            "allowed": True,
            "minute_remaining": config["per_minute"] - minute_count - 1,
            "hour_remaining": config["per_hour"] - hour_count - 1,
            "minute_reset": 60 - (current_time % 60),
            "hour_reset": 3600 - (current_time % 3600),
            "tier": config["tier"],
        }

    async def check_and_update(
        self, request: Request, user: Any | None = None
    ) -> dict[str, Any]:
        """Check rate limits and update counters"""

        identifier, user_role = await self._get_user_identifier(request, user)
        config = await self._get_rate_limit_config(request.url.path, user_role)
        result = await self._check_rate_limit(identifier, config)

        return result


# Global rate limiter instance
rate_limiter = RateLimiter()


async def rate_limit_middleware(
    request: Request, call_next, user: Any | None = None
):
    """Rate limiting middleware for FastAPI"""

    # Skip rate limiting for health checks
    if request.url.path in [
        "/health",
        "/",
        "/docs",
        "/redoc",
        "/openapi.json",
    ]:
        response = await call_next(request)
        return response

    try:
        result = await rate_limiter.check_and_update(request, user)

        if not result["allowed"]:
            # Rate limit exceeded
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail={
                    "error": "Rate limit exceeded",
                    "tier": result["tier"],
                    "limit": result["limit_type"],
                    "limit_value": result["limit"],
                    "current": result["current"],
                    "retry_after_seconds": result["reset_seconds"],
                },
                headers={"Retry-After": str(result["reset_seconds"])},
            )

        # Process request
        response = await call_next(request)

        # Add rate limit headers with backend indicator
        response.headers["X-RateLimit-Tier"] = result["tier"]
        response.headers["X-RateLimit-Remaining-Minute"] = str(
            result["minute_remaining"]
        )
        response.headers["X-RateLimit-Remaining-Hour"] = str(
            result["hour_remaining"]
        )
        response.headers["X-RateLimit-Reset-Minute"] = str(
            result["minute_reset"]
        )
        response.headers["X-RateLimit-Reset-Hour"] = str(result["hour_reset"])
        response.headers["X-RateLimit-Backend"] = (
            "redis" if rate_limiter.redis_available else "memory"
        )

        return response

    except HTTPException:
        # Re-raise HTTP exceptions (like 429)
        raise
    except Exception:
        # If rate limiting fails, allow request but log error
        response = await call_next(request)
        response.headers["X-RateLimit-Tier"] = "fallback"
        return response


def get_rate_limit_dependency(tier: str = "public"):
    """Dependency for endpoint-specific rate limiting"""

    async def check_rate_limit(request: Request):
        # This would be used for specific endpoints that need custom limits
        # For now, we handle all rate limiting in middleware
        pass

    return check_rate_limit
