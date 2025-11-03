"""
Rate Limit Monitoring and Metrics
Provides visibility into rate limiting behavior and usage patterns
"""

from datetime import datetime
import time
from typing import Any

from core.config import get_settings
from core.rate_limiting import rate_limiter
from fastapi import APIRouter, HTTPException, status

settings = get_settings()
router = APIRouter()


@router.get("/rate-limit/status")
async def get_rate_limit_status():
    """Get overall rate limiting system status"""
    try:
        # Check if Redis is available
        await rate_limiter._init_redis()
        redis_status = "connected" if rate_limiter.redis_available else "unavailable"

        return {
            "status": "operational",
            "redis_backend": redis_status,
            "fallback_active": not rate_limiter.redis_available,
            "tiers": {
                "public": {
                    "per_minute": settings.RATE_LIMIT_PUBLIC_PER_MINUTE,
                    "per_hour": settings.RATE_LIMIT_PUBLIC_PER_HOUR,
                    "burst": settings.RATE_LIMIT_PUBLIC_BURST,
                },
                "admin": {
                    "per_minute": settings.RATE_LIMIT_ADMIN_PER_MINUTE,
                    "per_hour": settings.RATE_LIMIT_ADMIN_PER_HOUR,
                    "burst": settings.RATE_LIMIT_ADMIN_BURST,
                },
                "admin_super": {
                    "per_minute": settings.RATE_LIMIT_ADMIN_SUPER_PER_MINUTE,
                    "per_hour": settings.RATE_LIMIT_ADMIN_SUPER_PER_HOUR,
                    "burst": settings.RATE_LIMIT_ADMIN_SUPER_BURST,
                },
                "ai": {
                    "per_minute": settings.RATE_LIMIT_AI_PER_MINUTE,
                    "per_hour": settings.RATE_LIMIT_AI_PER_HOUR,
                    "burst": settings.RATE_LIMIT_AI_BURST,
                },
                "webhook": {
                    "per_minute": settings.RATE_LIMIT_WEBHOOK_PER_MINUTE,
                    "per_hour": settings.RATE_LIMIT_WEBHOOK_PER_HOUR,
                    "burst": settings.RATE_LIMIT_WEBHOOK_BURST,
                },
            },
            "timestamp": datetime.utcnow().isoformat(),
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error checking rate limit status: {e!s}",
        )


@router.get("/rate-limit/metrics")
async def get_rate_limit_metrics():
    """Get rate limiting metrics and usage statistics"""
    try:
        await rate_limiter._init_redis()

        if rate_limiter.redis_available and rate_limiter.redis_client:
            # Get Redis-based metrics
            metrics = await _get_redis_metrics()
        else:
            # Get memory-based metrics
            metrics = _get_memory_metrics()

        return {
            "metrics": metrics,
            "backend": "redis" if rate_limiter.redis_available else "memory",
            "timestamp": datetime.utcnow().isoformat(),
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving metrics: {e!s}",
        )


@router.get("/rate-limit/test")
async def test_rate_limits():
    """Test endpoint to demonstrate rate limiting tiers"""
    return {
        "message": "This endpoint is rate limited based on your authentication tier",
        "tiers": {
            "public": "20 requests/minute",
            "admin": "100 requests/minute",
            "admin_super": "200 requests/minute",
        },
        "instructions": {
            "public": "Make requests without Authorization header",
            "admin": "Use 'Authorization: Bearer admin_token'",
            "admin_super": "Use 'Authorization: Bearer super_admin_token'",
        },
        "timestamp": datetime.utcnow().isoformat(),
    }


async def _get_redis_metrics() -> dict[str, Any]:
    """Get metrics from Redis backend"""
    try:
        current_time = int(time.time())
        current_time // 60
        current_time // 3600

        # Scan for rate limit keys
        pattern = "rate_limit:*"
        keys = await rate_limiter.redis_client.keys(pattern)

        metrics = {
            "total_active_limits": len(keys),
            "by_tier": {"public": 0, "admin": 0, "admin_super": 0, "ai": 0, "webhook": 0},
            "by_timeframe": {"minute": 0, "hour": 0},
            "active_users": set(),
            "total_requests": 0,
        }

        for key in keys:
            try:
                value = await rate_limiter.redis_client.get(key)
                if value:
                    count = int(value)
                    metrics["total_requests"] += count

                    # Parse key to extract tier and timeframe
                    key_parts = key.split(":")
                    if len(key_parts) >= 4:
                        identifier = key_parts[1]
                        timeframe = key_parts[3]

                        # Count by timeframe
                        if timeframe.startswith("minute"):
                            metrics["by_timeframe"]["minute"] += count
                        elif timeframe.startswith("hour"):
                            metrics["by_timeframe"]["hour"] += count

                        # Track unique users
                        if identifier.startswith("user:"):
                            metrics["active_users"].add(identifier)
            except Exception:
                continue

        metrics["unique_active_users"] = len(metrics["active_users"])
        del metrics["active_users"]  # Remove set for JSON serialization

        return metrics

    except Exception as e:
        return {"error": f"Failed to get Redis metrics: {e!s}"}


def _get_memory_metrics() -> dict[str, Any]:
    """Get metrics from memory fallback backend"""
    try:
        # Access the memory store from the global rate limiter instance
        memory_store = rate_limiter._memory_store

        current_time = time.time()
        metrics = {
            "total_active_limits": len(memory_store),
            "by_tier": {"public": 0, "admin": 0, "admin_super": 0, "ai": 0, "webhook": 0},
            "by_timeframe": {"minute": 0, "hour": 0},
            "unique_active_users": 0,
            "total_requests": 0,
        }

        unique_users = set()

        for identifier, data in memory_store.items():
            if isinstance(data, dict) and "count" in data:
                count = data.get("count", 0)
                timestamp = data.get("timestamp", 0)

                # Only count recent entries (within last hour)
                if current_time - timestamp < 3600:
                    metrics["total_requests"] += count

                    # Determine if it's minute or hour entry
                    if "minute" in identifier:
                        metrics["by_timeframe"]["minute"] += count
                    elif "hour" in identifier:
                        metrics["by_timeframe"]["hour"] += count

                    # Track unique users
                    user_id = identifier.split(":")[0]
                    if user_id.startswith("user"):
                        unique_users.add(user_id)

        metrics["unique_active_users"] = len(unique_users)

        return metrics

    except Exception as e:
        return {"error": f"Failed to get memory metrics: {e!s}"}


@router.get("/rate-limit/admin/stats")
async def get_admin_rate_limit_stats():
    """Admin-only endpoint for detailed rate limiting statistics"""
    # Note: In a real implementation, this would require admin authentication
    # For now, we'll return mock data to demonstrate the structure

    return {
        "summary": {
            "last_24_hours": {
                "total_requests": 15420,
                "rate_limited_requests": 234,
                "unique_users": 89,
                "peak_requests_per_minute": 156,
            },
            "by_tier": {
                "public": {"requests": 12340, "rate_limited": 198, "avg_requests_per_user": 24.5},
                "admin": {"requests": 2890, "rate_limited": 23, "avg_requests_per_user": 82.3},
                "admin_super": {"requests": 190, "rate_limited": 0, "avg_requests_per_user": 95.0},
                "ai": {"requests": 1200, "rate_limited": 13, "avg_requests_per_user": 8.7},
            },
        },
        "performance": {"avg_response_time_ms": 125, "redis_hit_rate": 98.5, "fallback_usage": 1.5},
        "recommendations": [
            "Consider increasing admin limits during peak hours",
            "Monitor AI endpoint usage for cost optimization",
            "Redis performance is optimal",
        ],
        "timestamp": datetime.utcnow().isoformat(),
    }
