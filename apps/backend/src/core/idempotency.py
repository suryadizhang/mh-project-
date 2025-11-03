"""
Idempotency Middleware - Prevent Duplicate Operations
Ensures critical operations (payments, messages) can be safely retried
"""

from collections.abc import Callable
import hashlib
import json
import logging

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse

logger = logging.getLogger(__name__)


class IdempotencyMiddleware(BaseHTTPMiddleware):
    """
    Middleware to handle idempotency for critical operations

    Clients send an Idempotency-Key header with a unique identifier.
    If the same key is used within the TTL window, return the cached response.
    """

    def __init__(self, app, cache_service=None, ttl_seconds: int = 86400):
        """
        Initialize idempotency middleware

        Args:
            app: FastAPI application
            cache_service: CacheService instance for storing idempotency keys
            ttl_seconds: How long to store idempotency keys (default 24 hours)
        """
        super().__init__(app)
        self.cache_service = cache_service
        self.ttl_seconds = ttl_seconds
        self.idempotent_methods = {"POST", "PUT", "PATCH", "DELETE"}

        # Paths that require idempotency
        self.idempotent_paths = [
            "/api/stripe/",
            "/api/payments/",
            "/api/bookings",
            "/api/crm/messages",
            "/api/ringcentral/",
        ]

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Process request with idempotency checking"""

        # Only check idempotency for configured methods and paths
        if not self._should_check_idempotency(request):
            return await call_next(request)

        # Get idempotency key from header
        idempotency_key = request.headers.get("Idempotency-Key")

        if not idempotency_key:
            # No idempotency key provided for idempotent endpoint
            logger.warning(f"Missing Idempotency-Key for {request.method} {request.url.path}")
            return await call_next(request)

        # Check if this operation was already completed
        if self.cache_service:
            cached_response = await self._get_cached_response(request, idempotency_key)

            if cached_response:
                logger.info(f"Returning cached response for idempotency key: {idempotency_key}")
                return JSONResponse(
                    content=cached_response["body"],
                    status_code=cached_response["status_code"],
                    headers={**cached_response["headers"], "X-Idempotent-Replay": "true"},
                )

        # Process the request
        response = await call_next(request)

        # Cache successful responses (2xx and 3xx)
        if 200 <= response.status_code < 400 and self.cache_service:
            await self._cache_response(request, idempotency_key, response)

        return response

    def _should_check_idempotency(self, request: Request) -> bool:
        """Check if this request should have idempotency checking"""
        if request.method not in self.idempotent_methods:
            return False

        # Check if path matches any idempotent path
        return any(request.url.path.startswith(path) for path in self.idempotent_paths)

    async def _get_cached_response(self, request: Request, idempotency_key: str) -> dict | None:
        """Get cached response for an idempotency key"""
        try:
            cache_key = self._build_cache_key(request, idempotency_key)
            cached = await self.cache_service.get(cache_key)

            if cached:
                return json.loads(cached)

            return None
        except Exception as e:
            logger.exception(f"Error getting cached response: {e}")
            return None

    async def _cache_response(self, request: Request, idempotency_key: str, response: Response):
        """Cache a response for future idempotency checks"""
        try:
            # Read response body
            body = b""
            async for chunk in response.body_iterator:
                body += chunk

            # Parse body as JSON
            try:
                body_json = json.loads(body.decode())
            except (json.JSONDecodeError, UnicodeDecodeError, AttributeError) as e:
                logger.warning(f"Failed to decode response body as JSON: {e}")
                body_json = {"data": body.decode("utf-8", errors="ignore")}

            # Build cache entry
            cache_entry = {
                "status_code": response.status_code,
                "headers": dict(response.headers),
                "body": body_json,
            }

            cache_key = self._build_cache_key(request, idempotency_key)
            await self.cache_service.set(cache_key, json.dumps(cache_entry), ttl=self.ttl_seconds)

            logger.info(f"Cached response for idempotency key: {idempotency_key}")

        except Exception as e:
            logger.exception(f"Error caching response: {e}")

    def _build_cache_key(self, request: Request, idempotency_key: str) -> str:
        """Build cache key from request and idempotency key"""
        # Include method and path to ensure uniqueness
        key_parts = ["idempotency", request.method, request.url.path, idempotency_key]

        key_string = ":".join(key_parts)
        return hashlib.md5(key_string.encode()).hexdigest()


# Decorator for idempotency at endpoint level
def idempotent(ttl_seconds: int = 86400):
    """
    Decorator to mark endpoints as requiring idempotency

    Example:
        @router.post("/payments")
        @idempotent(ttl_seconds=86400)
        async def create_payment(request: Request, payment_data: PaymentCreate):
            # Payment logic here
            pass
    """

    def decorator(func):
        async def wrapper(*args, **kwargs):
            # Get request from kwargs
            request = None
            for arg in args:
                if isinstance(arg, Request):
                    request = arg
                    break

            if not request:
                for value in kwargs.values():
                    if isinstance(value, Request):
                        request = value
                        break

            if not request:
                # No request found, proceed normally
                return await func(*args, **kwargs)

            # Check for idempotency key
            idempotency_key = request.headers.get("Idempotency-Key")

            if not idempotency_key:
                # Log warning but proceed
                logger.warning(f"Missing Idempotency-Key for {func.__name__}")
                return await func(*args, **kwargs)

            # Check cache
            cache_service = getattr(request.app.state, "cache", None)
            if cache_service:
                cache_key = f"idempotent:{func.__name__}:{idempotency_key}"
                cached = await cache_service.get(cache_key)

                if cached:
                    logger.info(f"Returning cached result for {func.__name__}")
                    return json.loads(cached)

            # Execute function
            result = await func(*args, **kwargs)

            # Cache result
            if cache_service and idempotency_key:
                cache_key = f"idempotent:{func.__name__}:{idempotency_key}"
                await cache_service.set(cache_key, json.dumps(result), ttl=ttl_seconds)

            return result

        return wrapper

    return decorator


def generate_idempotency_key(data: dict) -> str:
    """
    Generate an idempotency key from request data

    Useful for client-side generation or server-side deduplication

    Example:
        key = generate_idempotency_key({
            "user_id": "123",
            "amount": 100.00,
            "timestamp": "2024-01-01T00:00:00Z"
        })
    """
    # Sort keys for consistent hashing
    sorted_data = json.dumps(data, sort_keys=True)
    return hashlib.sha256(sorted_data.encode()).hexdigest()
