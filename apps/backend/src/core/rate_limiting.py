"""
Advanced Rate Limiting with Tiered Strategy
Uses Redis for distributed rate limiting (works across multiple workers)
"""
import time
import json
from typing import Optional, Dict, Any
from fastapi import Request, HTTPException, status, Response
from core.config import get_settings, UserRole
import redis.asyncio as redis
import hashlib

settings = get_settings()

# Redis connection
redis_client = redis.from_url(settings.REDIS_URL, encoding="utf-8", decode_responses=True)

class RateLimiter:
    """Advanced rate limiter with Redis backend and tiered strategy"""
    
    def __init__(self):
        self.settings = settings
    
    async def _get_user_identifier(self, request: Request, user: Optional[Any] = None) -> tuple[str, UserRole]:
        """Get unique identifier and role for rate limiting"""
        
        # Check if it's a webhook endpoint
        if request.url.path.startswith("/webhooks/"):
            webhook_key = request.headers.get("authorization") or request.headers.get("x-webhook-secret")
            if webhook_key:
                hashed_key = hashlib.sha256(webhook_key.encode()).hexdigest()[:16]
                return f"webhook:{hashed_key}", None
        
        # Check if user is authenticated
        if user:
            user_role = getattr(user, 'role', UserRole.CUSTOMER)
            user_id = getattr(user, 'id', 'unknown')
            return f"user:{user_id}", user_role
        
        # Check for API key in headers
        api_key = request.headers.get("x-api-key")
        if api_key:
            hashed_key = hashlib.sha256(api_key.encode()).hexdigest()[:16]
            return f"api:{hashed_key}", UserRole.CUSTOMER
        
        # Fall back to IP address for public users
        client_ip = request.client.host if request.client else "unknown"
        return f"ip:{client_ip}", None
    
    async def _get_rate_limit_config(self, path: str, user_role: Optional[UserRole]) -> Dict[str, Any]:
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
                "tier": "webhook"
            }
        
        # User-based limits
        return self.settings.get_rate_limit_for_user(user_role)
    
    async def _check_rate_limit(self, identifier: str, config: Dict[str, Any]) -> Dict[str, Any]:
        """Check rate limits using sliding window algorithm"""
        
        current_time = int(time.time())
        minute_window = current_time // 60
        hour_window = current_time // 3600
        
        # Redis keys
        minute_key = f"rate_limit:{identifier}:minute:{minute_window}"
        hour_key = f"rate_limit:{identifier}:hour:{hour_window}"
        
        # Get current counts
        pipe = redis_client.pipeline()
        pipe.get(minute_key)
        pipe.get(hour_key)
        results = await pipe.execute()
        
        minute_count = int(results[0] or 0)
        hour_count = int(results[1] or 0)
        
        # Check limits
        if minute_count >= config["per_minute"]:
            return {
                "allowed": False,
                "limit_type": "per_minute",
                "current": minute_count,
                "limit": config["per_minute"],
                "reset_seconds": 60 - (current_time % 60),
                "tier": config["tier"]
            }
        
        if hour_count >= config["per_hour"]:
            return {
                "allowed": False,
                "limit_type": "per_hour",
                "current": hour_count,
                "limit": config["per_hour"],
                "reset_seconds": 3600 - (current_time % 3600),
                "tier": config["tier"]
            }
        
        # Increment counters
        pipe = redis_client.pipeline()
        pipe.incr(minute_key)
        pipe.expire(minute_key, 120)  # Keep for 2 minutes
        pipe.incr(hour_key)
        pipe.expire(hour_key, 7200)  # Keep for 2 hours
        await pipe.execute()
        
        return {
            "allowed": True,
            "minute_remaining": config["per_minute"] - minute_count - 1,
            "hour_remaining": config["per_hour"] - hour_count - 1,
            "minute_reset": 60 - (current_time % 60),
            "hour_reset": 3600 - (current_time % 3600),
            "tier": config["tier"]
        }
    
    async def check_and_update(self, request: Request, user: Optional[Any] = None) -> Dict[str, Any]:
        """Check rate limits and update counters"""
        
        identifier, user_role = await self._get_user_identifier(request, user)
        config = await self._get_rate_limit_config(request.url.path, user_role)
        result = await self._check_rate_limit(identifier, config)
        
        return result

# Global rate limiter instance
rate_limiter = RateLimiter()

async def rate_limit_middleware(request: Request, call_next, user: Optional[Any] = None):
    """Rate limiting middleware for FastAPI"""
    
    # Skip rate limiting for health checks
    if request.url.path in ["/health", "/", "/docs", "/redoc", "/openapi.json"]:
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
                    "retry_after_seconds": result["reset_seconds"]
                },
                headers={"Retry-After": str(result["reset_seconds"])}
            )
        
        # Process request
        response = await call_next(request)
        
        # Add rate limit headers
        response.headers["X-RateLimit-Tier"] = result["tier"]
        response.headers["X-RateLimit-Remaining-Minute"] = str(result["minute_remaining"])
        response.headers["X-RateLimit-Remaining-Hour"] = str(result["hour_remaining"])
        response.headers["X-RateLimit-Reset-Minute"] = str(result["minute_reset"])
        response.headers["X-RateLimit-Reset-Hour"] = str(result["hour_reset"])
        
        return response
        
    except Exception as e:
        # If rate limiting fails, allow request but log error
        print(f"Rate limiting error: {e}")
        response = await call_next(request)
        return response

def get_rate_limit_dependency(tier: str = "public"):
    """Dependency for endpoint-specific rate limiting"""
    async def check_rate_limit(request: Request):
        # This would be used for specific endpoints that need custom limits
        # For now, we handle all rate limiting in middleware
        pass
    return check_rate_limit