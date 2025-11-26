"""
Advanced Rate Limiting Middleware with Role-Based Limits and Login Attempt Tracking

Features:
- Role-based rate limits (customer: 10/min, admin: 100/min)
- Failed login attempt tracking with automatic lockout (5 attempts = 15 min lockout)
- Redis-backed for distributed rate limiting
- User warnings before lockout
- Automatic cleanup of expired lockouts
- Detailed logging for security monitoring

Created: October 30, 2025
Author: My Hibachi Chef Development Team
"""

from datetime import datetime, timedelta, timezone
import json
import logging
import time

from core.config import get_settings
from fastapi import HTTPException, Request, status
from fastapi.responses import JSONResponse
from redis import asyncio as aioredis
from starlette.middleware.base import BaseHTTPMiddleware

settings = get_settings()
logger = logging.getLogger(__name__)


class RateLimitConfig:
    """Rate limit configuration constants"""

    # Role-based limits (requests per minute)
    CUSTOMER_LIMIT = 10
    ADMIN_LIMIT = 100
    STATION_MANAGER_LIMIT = 100
    CHEF_LIMIT = 50
    UNAUTHENTICATED_LIMIT = 5

    # Login attempt tracking
    MAX_LOGIN_ATTEMPTS = 5
    LOCKOUT_DURATION_MINUTES = 15
    WARNING_THRESHOLD = 3  # Warn user after 3 failed attempts

    # Redis key prefixes
    RATE_LIMIT_PREFIX = "rate_limit"
    LOGIN_ATTEMPT_PREFIX = "login_attempts"
    LOCKOUT_PREFIX = "account_lockout"

    # Time windows
    RATE_LIMIT_WINDOW_SECONDS = 60
    LOGIN_ATTEMPT_WINDOW_SECONDS = 300  # 5 minutes


class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    Advanced rate limiting middleware with role-based limits and login tracking
    """

    def __init__(self, app, redis_url: str | None = None):
        super().__init__(app)
        self.redis_url = redis_url or settings.redis_url
        self.redis_client: aioredis.Redis | None = None
        self.config = RateLimitConfig()

    async def _get_redis_client(self) -> aioredis.Redis:
        """Get or create Redis client"""
        if self.redis_client is None:
            try:
                self.redis_client = await aioredis.from_url(
                    self.redis_url,
                    encoding="utf-8",
                    decode_responses=True,
                    max_connections=50,
                )
                logger.info("✅ Rate limiter Redis connection established")
            except Exception as e:
                logger.exception(
                    f"❌ Redis connection failed for rate limiter: {e}"
                )
                raise HTTPException(
                    status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                    detail="Rate limiting service temporarily unavailable",
                )
        return self.redis_client

    async def _get_user_info(
        self, request: Request
    ) -> tuple[str | None, str | None]:
        """
        Extract user ID and role from request
        Returns: (user_id, role)
        """
        # Try to get from JWT token in request state (set by auth middleware)
        user_id = getattr(request.state, "user_id", None)
        role = getattr(request.state, "role", None)

        # If not in state, try to decode from Authorization header
        if not user_id:
            auth_header = request.headers.get("authorization", "")
            if auth_header.startswith("Bearer "):
                # Extract from token (simplified - actual implementation should use JWT decode)
                try:
                    # This would normally decode JWT - placeholder for now
                    pass
                except Exception:
                    pass

        return user_id, role

    def _get_rate_limit_for_role(self, role: str | None) -> int:
        """Get rate limit based on user role"""
        role_limits = {
            "super_admin": self.config.ADMIN_LIMIT,
            "admin": self.config.ADMIN_LIMIT,
            "station_manager": self.config.STATION_MANAGER_LIMIT,
            "chef": self.config.CHEF_LIMIT,
            "customer": self.config.CUSTOMER_LIMIT,
        }
        return role_limits.get(role, self.config.UNAUTHENTICATED_LIMIT)

    async def _check_rate_limit(
        self, redis: aioredis.Redis, identifier: str, limit: int
    ) -> tuple[bool, int, int]:
        """
        Check if rate limit is exceeded
        Returns: (is_allowed, current_count, remaining)
        """
        key = f"{self.config.RATE_LIMIT_PREFIX}:{identifier}"
        current_time = int(time.time())
        window_start = current_time - self.config.RATE_LIMIT_WINDOW_SECONDS

        # Use Redis sorted set for sliding window
        pipe = redis.pipeline()

        # Remove old entries
        pipe.zremrangebyscore(key, 0, window_start)

        # Count current requests in window
        pipe.zcard(key)

        # Add current request
        pipe.zadd(key, {str(current_time): current_time})

        # Set expiry
        pipe.expire(key, self.config.RATE_LIMIT_WINDOW_SECONDS + 10)

        results = await pipe.execute()
        current_count = results[1]  # Result from zcard

        remaining = max(0, limit - current_count - 1)
        is_allowed = current_count < limit

        return is_allowed, current_count + 1, remaining

    async def _track_login_attempt(
        self, redis: aioredis.Redis, identifier: str, success: bool
    ) -> dict:
        """
        Track login attempts and check for lockout
        Returns: dict with lockout info and warning messages
        """
        lockout_key = f"{self.config.LOCKOUT_PREFIX}:{identifier}"
        attempt_key = f"{self.config.LOGIN_ATTEMPT_PREFIX}:{identifier}"

        # Check if account is locked out
        lockout_data = await redis.get(lockout_key)
        if lockout_data:
            lockout_info = json.loads(lockout_data)
            lockout_until = datetime.fromisoformat(
                lockout_info["lockout_until"]
            )

            if datetime.now(timezone.utc) < lockout_until:
                remaining_seconds = int(
                    (
                        lockout_until - datetime.now(timezone.utc)
                    ).total_seconds()
                )
                remaining_minutes = remaining_seconds // 60

                return {
                    "locked": True,
                    "remaining_minutes": remaining_minutes,
                    "remaining_seconds": remaining_seconds,
                    "message": f"⚠️ Account locked due to multiple failed login attempts. Please try again in {remaining_minutes} minutes.",
                    "lockout_until": lockout_until.isoformat(),
                }
            else:
                # Lockout expired, clean up
                await redis.delete(lockout_key)
                await redis.delete(attempt_key)

        # If login was successful, clear attempts
        if success:
            await redis.delete(attempt_key)
            return {"locked": False, "attempts": 0}

        # Track failed attempt
        current_time = int(time.time())
        window_start = current_time - self.config.LOGIN_ATTEMPT_WINDOW_SECONDS

        pipe = redis.pipeline()
        pipe.zremrangebyscore(attempt_key, 0, window_start)
        pipe.zadd(attempt_key, {str(current_time): current_time})
        pipe.zcard(attempt_key)
        pipe.expire(attempt_key, self.config.LOGIN_ATTEMPT_WINDOW_SECONDS)

        results = await pipe.execute()
        attempt_count = results[2]

        # Check if we should lock the account
        if attempt_count >= self.config.MAX_LOGIN_ATTEMPTS:
            lockout_until = datetime.now(timezone.utc) + timedelta(
                minutes=self.config.LOCKOUT_DURATION_MINUTES
            )
            lockout_data = {
                "lockout_until": lockout_until.isoformat(),
                "attempts": attempt_count,
                "locked_at": datetime.now(timezone.utc).isoformat(),
            }

            await redis.setex(
                lockout_key,
                self.config.LOCKOUT_DURATION_MINUTES * 60,
                json.dumps(lockout_data),
            )

            # Log security event
            logger.warning(
                f"🔒 SECURITY: Account locked - identifier: {identifier}, "
                f"attempts: {attempt_count}, lockout_until: {lockout_until}"
            )

            return {
                "locked": True,
                "attempts": attempt_count,
                "remaining_minutes": self.config.LOCKOUT_DURATION_MINUTES,
                "message": f"⚠️ Account locked due to {self.config.MAX_LOGIN_ATTEMPTS} failed login attempts. "
                f"Please try again in {self.config.LOCKOUT_DURATION_MINUTES} minutes.",
                "lockout_until": lockout_until.isoformat(),
            }

        # Return warning if approaching limit
        remaining_attempts = self.config.MAX_LOGIN_ATTEMPTS - attempt_count
        warning = None

        if attempt_count >= self.config.WARNING_THRESHOLD:
            warning = (
                f"⚠️ Warning: {remaining_attempts} login attempt(s) remaining before "
                f"{self.config.LOCKOUT_DURATION_MINUTES}-minute lockout."
            )

        return {
            "locked": False,
            "attempts": attempt_count,
            "remaining_attempts": remaining_attempts,
            "warning": warning,
        }

    async def dispatch(self, request: Request, call_next):
        """Process request with rate limiting"""

        # Skip rate limiting for health checks
        if request.url.path in [
            "/health",
            "/health/ready",
            "/health/live",
            "/metrics",
        ]:
            return await call_next(request)

        try:
            redis = await self._get_redis_client()

            # Get user information
            user_id, role = await self._get_user_info(request)

            # Determine identifier (user_id or IP address)
            if user_id:
                identifier = f"user:{user_id}"
            else:
                # Use IP address for unauthenticated requests
                client_ip = (
                    request.client.host if request.client else "unknown"
                )
                identifier = f"ip:{client_ip}"

            # Check for login endpoint
            is_login_endpoint = (
                "/auth/login" in request.url.path
                or "/login" in request.url.path
            )

            if is_login_endpoint:
                # Check for existing lockout before processing
                lockout_check = await self._track_login_attempt(
                    redis, identifier, success=False
                )

                if lockout_check["locked"]:
                    logger.warning(
                        f"🚫 Blocked login attempt for locked account: {identifier}, "
                        f"remaining: {lockout_check['remaining_minutes']} minutes"
                    )

                    return JSONResponse(
                        status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                        content={
                            "detail": lockout_check["message"],
                            "locked": True,
                            "remaining_minutes": lockout_check[
                                "remaining_minutes"
                            ],
                            "remaining_seconds": lockout_check[
                                "remaining_seconds"
                            ],
                            "lockout_until": lockout_check["lockout_until"],
                            "retry_after": lockout_check["remaining_seconds"],
                        },
                        headers={
                            "Retry-After": str(
                                lockout_check["remaining_seconds"]
                            ),
                            "X-RateLimit-Locked": "true",
                            "X-RateLimit-Remaining-Minutes": str(
                                lockout_check["remaining_minutes"]
                            ),
                        },
                    )

            # Apply role-based rate limiting
            limit = self._get_rate_limit_for_role(role)
            is_allowed, current_count, remaining = (
                await self._check_rate_limit(redis, identifier, limit)
            )

            # Add rate limit headers
            response = None
            if is_allowed:
                response = await call_next(request)

                # Track successful login if applicable
                if is_login_endpoint and response.status_code == 200:
                    await self._track_login_attempt(
                        redis, identifier, success=True
                    )
                elif is_login_endpoint and response.status_code in [401, 403]:
                    # Failed login
                    lockout_info = await self._track_login_attempt(
                        redis, identifier, success=False
                    )

                    # Add warning to response if present
                    if lockout_info.get("warning"):
                        # Modify response to include warning
                        body = b""
                        async for chunk in response.body_iterator:
                            body += chunk

                        try:
                            content = json.loads(body)
                            content["warning"] = lockout_info["warning"]
                            content["remaining_attempts"] = lockout_info[
                                "remaining_attempts"
                            ]

                            response = JSONResponse(
                                status_code=response.status_code,
                                content=content,
                                headers=dict(response.headers),
                            )
                        except Exception:
                            # If can't parse JSON, just pass through
                            response = JSONResponse(
                                status_code=response.status_code,
                                content=body.decode(),
                                headers=dict(response.headers),
                            )
            else:
                logger.warning(
                    f"🚫 Rate limit exceeded: {identifier} ({role or 'unauthenticated'}), "
                    f"limit: {limit}/min, current: {current_count}"
                )

                response = JSONResponse(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    content={
                        "detail": f"Rate limit exceeded. Maximum {limit} requests per minute allowed for your role.",
                        "limit": limit,
                        "current": current_count,
                        "remaining": 0,
                        "reset_in_seconds": self.config.RATE_LIMIT_WINDOW_SECONDS,
                        "role": role or "unauthenticated",
                    },
                )

            # Add standard rate limit headers
            response.headers["X-RateLimit-Limit"] = str(limit)
            response.headers["X-RateLimit-Remaining"] = str(remaining)
            response.headers["X-RateLimit-Reset"] = str(
                int(time.time()) + self.config.RATE_LIMIT_WINDOW_SECONDS
            )

            if not is_allowed:
                response.headers["Retry-After"] = str(
                    self.config.RATE_LIMIT_WINDOW_SECONDS
                )

            return response

        except Exception as e:
            # Log error but don't block request if rate limiting fails
            logger.error(f"❌ Rate limiting error: {e}", exc_info=True)

            # Proceed without rate limiting in case of errors (fail open)
            return await call_next(request)


# Standalone function for checking lockout status (can be used in auth endpoints)
async def check_login_lockout(
    identifier: str, redis_url: str | None = None
) -> dict:
    """
    Check if an account is locked out
    Can be called from auth endpoints before processing login

    Args:
        identifier: User identifier (user_id or IP address)
        redis_url: Optional Redis URL override

    Returns:
        Dict with lockout status and details
    """
    redis_url = redis_url or settings.redis_url
    redis = await aioredis.from_url(
        redis_url, encoding="utf-8", decode_responses=True
    )

    lockout_key = f"{RateLimitConfig.LOCKOUT_PREFIX}:{identifier}"
    lockout_data = await redis.get(lockout_key)

    if not lockout_data:
        return {"locked": False}

    lockout_info = json.loads(lockout_data)
    lockout_until = datetime.fromisoformat(lockout_info["lockout_until"])

    if datetime.now(timezone.utc) < lockout_until:
        remaining_seconds = int(
            (lockout_until - datetime.now(timezone.utc)).total_seconds()
        )
        return {
            "locked": True,
            "remaining_minutes": remaining_seconds // 60,
            "remaining_seconds": remaining_seconds,
            "lockout_until": lockout_until.isoformat(),
        }
    else:
        # Expired, clean up
        await redis.delete(lockout_key)
        return {"locked": False}
