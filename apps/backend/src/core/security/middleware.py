"""
Security Middleware
===================

HTTP middleware for security, rate limiting, logging, and metrics.

See: .github/instructions/22-QUALITY_CONTROL.instructions.md for modularization standards
"""

import hashlib
import hmac
import logging
import re
import time
from collections import defaultdict

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

from core.config import settings
from .config import SecurityConfig
from .request_utils import get_client_ip, get_endpoint_pattern

logger = logging.getLogger(__name__)


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Add security headers to all responses"""

    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)

        for header, value in SecurityConfig.SECURITY_HEADERS.items():
            response.headers[header] = value

        return response


class RateLimitByIPMiddleware(BaseHTTPMiddleware):
    """Rate limit requests by IP address"""

    def __init__(self, app, max_requests: int = 100, window_seconds: int = 60):
        super().__init__(app)
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.requests: dict[str, list[float]] = defaultdict(list)
        self._last_cleanup = time.time()

    async def dispatch(self, request: Request, call_next):
        # Periodic cleanup
        now = time.time()
        if now - self._last_cleanup > 60:
            self._cleanup_old_requests()
            self._last_cleanup = now

        client_ip = get_client_ip(request)

        # Check rate limit
        cutoff = now - self.window_seconds
        self.requests[client_ip] = [t for t in self.requests[client_ip] if t > cutoff]

        if len(self.requests[client_ip]) >= self.max_requests:
            logger.warning(f"Rate limit exceeded for IP: {client_ip}")
            return Response(
                content="Rate limit exceeded. Please try again later.",
                status_code=429,
                headers={"Retry-After": str(self.window_seconds)},
            )

        self.requests[client_ip].append(now)
        response = await call_next(request)
        return response

    def _cleanup_old_requests(self):
        """Clean up old request records"""
        cutoff = time.time() - self.window_seconds * 2
        for ip in list(self.requests.keys()):
            self.requests[ip] = [t for t in self.requests[ip] if t > cutoff]
            if not self.requests[ip]:
                del self.requests[ip]


class InputValidationMiddleware(BaseHTTPMiddleware):
    """Validate request input for security"""

    async def dispatch(self, request: Request, call_next):
        # Check content length
        content_length = request.headers.get("content-length")
        if content_length:
            if int(content_length) > SecurityConfig.MAX_REQUEST_SIZE:
                return Response(content="Request body too large", status_code=413)

        # Check for suspicious URL patterns
        path = request.url.path.lower()
        for pattern in SecurityConfig.DANGEROUS_PATTERNS:
            if re.search(pattern, path, re.IGNORECASE):
                logger.warning(f"Blocked suspicious URL pattern: {path}")
                return Response(content="Bad request", status_code=400)

        # Check user agent
        user_agent = request.headers.get("user-agent", "").lower()
        for sus_ua in SecurityConfig.SUSPICIOUS_USER_AGENTS:
            if sus_ua in user_agent:
                logger.warning(f"Blocked suspicious user agent: {user_agent}")
                return Response(content="Bad request", status_code=403)

        return await call_next(request)


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """Log all requests for audit trail"""

    async def dispatch(self, request: Request, call_next):
        start_time = time.time()

        # Get request info
        client_ip = get_client_ip(request)
        method = request.method
        path = request.url.path
        query = str(request.url.query) if request.url.query else ""

        # Process request
        response = await call_next(request)

        # Calculate duration
        duration = time.time() - start_time
        status_code = response.status_code

        # Log request (exclude health checks for less noise)
        if path not in ["/health", "/api/v1/health", "/metrics"]:
            logger.info(
                f"{method} {path} {'?' + query if query else ''} "
                f"- {status_code} - {duration:.3f}s - {client_ip}"
            )

        # Add timing header
        response.headers["X-Response-Time"] = f"{duration:.3f}s"

        return response


class MetricsMiddleware(BaseHTTPMiddleware):
    """Collect request metrics for monitoring"""

    def __init__(self, app):
        super().__init__(app)
        self._request_count = 0
        self._error_count = 0
        self._total_duration = 0.0
        self._status_counts: dict[int, int] = defaultdict(int)

        # Try to use Prometheus if available
        try:
            from prometheus_client import Counter, Histogram

            self.http_requests_total = Counter(
                "http_requests_total",
                "Total HTTP requests",
                ["method", "endpoint", "status"],
            )
            self.http_request_duration = Histogram(
                "http_request_duration_seconds",
                "HTTP request duration",
                ["method", "endpoint"],
            )
            self._prometheus_enabled = True
        except ImportError:
            self._prometheus_enabled = False

    async def dispatch(self, request: Request, call_next):
        start_time = time.time()
        method = request.method
        endpoint = get_endpoint_pattern(request.url.path)

        response = await call_next(request)

        duration = time.time() - start_time
        status_code = response.status_code

        # Update metrics
        self._request_count += 1
        self._total_duration += duration
        self._status_counts[status_code] += 1

        if status_code >= 400:
            self._error_count += 1

        # Prometheus metrics if available
        if self._prometheus_enabled:
            self.http_requests_total.labels(
                method=method, endpoint=endpoint, status=status_code
            ).inc()
            self.http_request_duration.labels(method=method, endpoint=endpoint).observe(duration)

        return response

    def get_stats(self) -> dict:
        """Get current metrics stats"""
        return {
            "total_requests": self._request_count,
            "error_count": self._error_count,
            "avg_duration": (
                self._total_duration / self._request_count if self._request_count > 0 else 0
            ),
            "status_counts": dict(self._status_counts),
        }


class WebhookSecurityMiddleware(BaseHTTPMiddleware):
    """Verify webhook signatures"""

    def __init__(self, app, secret_key: str | None = None):
        super().__init__(app)
        self.secret_key = secret_key or getattr(settings, "WEBHOOK_SECRET", "")

    async def dispatch(self, request: Request, call_next):
        # Only check webhook endpoints
        if not request.url.path.startswith("/api/v1/webhooks"):
            return await call_next(request)

        # Get signature from header
        signature = request.headers.get("X-Webhook-Signature")
        if not signature and self.secret_key:
            logger.warning("Missing webhook signature")
            return Response(content="Missing signature", status_code=401)

        if self.secret_key:
            # Verify signature
            body = await request.body()
            expected_signature = hmac.new(
                self.secret_key.encode(), body, hashlib.sha256
            ).hexdigest()

            if not hmac.compare_digest(signature or "", expected_signature):
                logger.warning("Invalid webhook signature")
                return Response(content="Invalid signature", status_code=401)

        return await call_next(request)


__all__ = [
    "SecurityHeadersMiddleware",
    "RateLimitByIPMiddleware",
    "InputValidationMiddleware",
    "RequestLoggingMiddleware",
    "MetricsMiddleware",
    "WebhookSecurityMiddleware",
]
