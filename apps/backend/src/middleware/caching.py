"""
Caching Middleware for FastAPI

Provides:
- Cache-Control headers for different endpoint types
- ETag support for conditional requests
- Configurable cache strategies per route pattern

Usage:
    app.add_middleware(CachingMiddleware)
"""

import hashlib
import logging
import re
import time
from typing import Callable, Dict, List, Optional, Tuple

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

logger = logging.getLogger(__name__)


class CacheConfig:
    """Cache configuration for different route patterns."""

    # Cache durations in seconds
    NO_CACHE = 0
    SHORT = 60  # 1 minute
    MEDIUM = 300  # 5 minutes
    LONG = 3600  # 1 hour
    VERY_LONG = 86400  # 1 day

    # Route patterns and their cache configurations
    # Format: (pattern, max_age, is_private, stale_while_revalidate)
    ROUTE_CONFIGS: List[Tuple[str, int, bool, int]] = [
        # Health endpoints - short cache, public
        (r"^/health.*", SHORT, False, 30),
        (r"^/api/v1/health.*", SHORT, False, 30),
        # Static data endpoints - long cache, public
        (r"^/api/v1/menu.*", LONG, False, 300),
        (r"^/api/v1/packages.*", LONG, False, 300),
        (r"^/api/v1/faqs.*", MEDIUM, False, 120),
        (r"^/api/v1/locations.*", VERY_LONG, False, 3600),
        (r"^/api/v1/pricing/public.*", MEDIUM, False, 120),
        # User-specific data - private cache
        (r"^/api/v1/bookings.*", SHORT, True, 30),
        (r"^/api/v1/users/me.*", SHORT, True, 30),
        (r"^/api/v1/admin.*", NO_CACHE, True, 0),
        # AI endpoints - no cache (dynamic responses)
        (r"^/api/v1/ai.*", NO_CACHE, True, 0),
        (r"^/api/v1/chat.*", NO_CACHE, True, 0),
        # Webhooks - no cache
        (r"^/api/v1/webhooks.*", NO_CACHE, False, 0),
    ]

    # Default cache configuration for unmatched routes
    DEFAULT_CONFIG = (MEDIUM, True, 60)  # 5 min, private, 60s stale


class CachingMiddleware(BaseHTTPMiddleware):
    """
    Middleware that adds appropriate Cache-Control headers to responses.

    Features:
    - Route-based cache configuration
    - ETag support for conditional requests
    - Stale-while-revalidate support
    - Respects existing cache headers
    """

    def __init__(
        self,
        app: ASGIApp,
        enable_etag: bool = True,
        respect_existing_headers: bool = True,
    ):
        super().__init__(app)
        self.enable_etag = enable_etag
        self.respect_existing_headers = respect_existing_headers
        self._compiled_patterns: List[Tuple[re.Pattern, int, bool, int]] = [
            (re.compile(pattern), max_age, is_private, stale)
            for pattern, max_age, is_private, stale in CacheConfig.ROUTE_CONFIGS
        ]

    def _get_cache_config(self, path: str) -> Tuple[int, bool, int]:
        """Get cache configuration for a given path."""
        for pattern, max_age, is_private, stale in self._compiled_patterns:
            if pattern.match(path):
                return (max_age, is_private, stale)
        return CacheConfig.DEFAULT_CONFIG

    def _generate_etag(self, content: bytes) -> Optional[str]:
        """Generate ETag from response content.
        
        Returns None if content is empty or cannot be hashed.
        Uses SHA256 for stronger hashing than MD5.
        """
        if not content or len(content) == 0:
            return None
        try:
            # Use SHA256 for stronger hashing
            return f'"sha256-{hashlib.sha256(content).hexdigest()[:32]}"'
        except Exception:
            return None

    def _build_cache_control(
        self, max_age: int, is_private: bool, stale_while_revalidate: int
    ) -> str:
        """Build Cache-Control header value."""
        parts = []

        if max_age == 0:
            return "no-store, no-cache, must-revalidate"

        if is_private:
            parts.append("private")
        else:
            parts.append("public")

        parts.append(f"max-age={max_age}")

        if stale_while_revalidate > 0:
            parts.append(f"stale-while-revalidate={stale_while_revalidate}")

        return ", ".join(parts)

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Process request and add caching headers to response."""
        # Skip caching for non-GET requests
        if request.method != "GET":
            response = await call_next(request)
            # Ensure non-GET responses are not cached
            if "cache-control" not in response.headers:
                response.headers["cache-control"] = "no-store"
            return response

        # Check for conditional request (If-None-Match)
        if_none_match = request.headers.get("if-none-match")

        # Get response
        response = await call_next(request)

        # Skip if response already has cache headers and we should respect them
        if (
            self.respect_existing_headers
            and "cache-control" in response.headers
        ):
            return response

        # Skip caching for error responses
        if response.status_code >= 400:
            response.headers["cache-control"] = "no-store"
            return response

        # Get cache configuration for this route
        path = request.url.path
        max_age, is_private, stale = self._get_cache_config(path)

        # Set Cache-Control header
        response.headers["cache-control"] = self._build_cache_control(
            max_age, is_private, stale
        )

        # Add Vary header - exclude Authorization for public resources to prevent cache confusion
        if is_private:
            response.headers["vary"] = "Accept, Accept-Encoding, Authorization"
        else:
            response.headers["vary"] = "Accept, Accept-Encoding"

        # Add ETag if enabled, response has body, and is not streaming
        # Only process buffered responses (not StreamingResponse)
        if (
            self.enable_etag
            and hasattr(response, "body")
            and response.body is not None
            and not hasattr(response, "body_iterator")  # Skip streaming responses
        ):
            try:
                body_bytes = response.body
                # Ensure we have actual bytes to hash
                if isinstance(body_bytes, bytes) and len(body_bytes) > 0:
                    etag = self._generate_etag(body_bytes)
                    if etag:  # Only set if generation succeeded
                        response.headers["etag"] = etag

                        # Handle conditional request
                        if if_none_match and if_none_match == etag:
                            return Response(status_code=304, headers={"etag": etag})
            except (AttributeError, TypeError):
                # Response body not accessible or not bytes, skip ETag
                logger.debug("Skipping ETag generation for non-buffered response")

        return response


class CompressionMiddleware(BaseHTTPMiddleware):
    """
    Simple compression info middleware.

    Note: For actual GZip compression, use starlette.middleware.gzip.GZipMiddleware.
    This middleware adds compression-related headers for debugging/monitoring.
    """

    def __init__(
        self,
        app: ASGIApp,
        minimum_size: int = 500,  # Don't compress responses smaller than this
    ):
        super().__init__(app)
        self.minimum_size = minimum_size

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Add compression info headers."""
        response = await call_next(request)

        # Add header indicating compression is available
        accept_encoding = request.headers.get("accept-encoding", "")
        if "gzip" in accept_encoding.lower():
            # Mark that client supports gzip
            response.headers["x-compression-available"] = "gzip"

        return response
