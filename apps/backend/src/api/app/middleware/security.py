"""
Security middleware for MyHibachi Backend API.
Implements security headers, request validation, and monitoring.
"""

import time
import uuid
from typing import Callable
import logging
import re
from fastapi import Request, Response, HTTPException, status
from fastapi.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse
import prometheus_client

logger = logging.getLogger(__name__)

# Metrics for monitoring
REQUEST_COUNT = prometheus_client.Counter(
    'http_requests_total',
    'Total HTTP requests',
    ['method', 'endpoint', 'status_code']
)

REQUEST_DURATION = prometheus_client.Histogram(
    'http_request_duration_seconds',
    'HTTP request duration',
    ['method', 'endpoint']
)

SECURITY_VIOLATIONS = prometheus_client.Counter(
    'security_violations_total',
    'Security violations detected',
    ['violation_type']
)


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Add security headers to all responses."""

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        response = await call_next(request)
        
        # Security headers
        response.headers.update({
            # Prevent XSS attacks
            "X-Content-Type-Options": "nosniff",
            "X-Frame-Options": "DENY",
            "X-XSS-Protection": "1; mode=block",
            
            # HTTPS enforcement (if in production)
            "Strict-Transport-Security": "max-age=31536000; includeSubDomains" if request.url.scheme == "https" else "",
            
            # Content Security Policy
            "Content-Security-Policy": "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline';",
            
            # Referrer policy
            "Referrer-Policy": "strict-origin-when-cross-origin",
            
            # Permission policy
            "Permissions-Policy": "geolocation=(), microphone=(), camera=()",
            
            # Custom headers
            "X-API-Version": "1.0.0",
            "X-Request-ID": str(uuid.uuid4())
        })
        
        # Remove server information
        response.headers.pop("server", None)
        
        return response


class InputValidationMiddleware(BaseHTTPMiddleware):
    """Validate and sanitize incoming requests."""

    # Dangerous patterns to detect
    DANGEROUS_PATTERNS = [
        r'<script[^>]*>.*?</script>',  # Script tags
        r'javascript:',               # JavaScript URLs
        r'on\w+\s*=',                # Event handlers
        r'<iframe[^>]*>',            # Iframes
        r'eval\s*\(',                # Eval calls
        r'expression\s*\(',          # CSS expressions
        r'--',                       # SQL comment
        r';.*?--',                   # SQL injection patterns
        r'union.*?select',           # SQL union
        r'drop\s+table',             # SQL drop
    ]

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Skip validation for certain endpoints
        if request.url.path in ["/docs", "/redoc", "/openapi.json", "/metrics"]:
            return await call_next(request)

        # Validate request size
        content_length = request.headers.get("content-length")
        if content_length and int(content_length) > 10 * 1024 * 1024:  # 10MB limit
            SECURITY_VIOLATIONS.labels(violation_type="large_request").inc()
            return JSONResponse(
                status_code=413,
                content={"detail": "Request too large"}
            )

        # Check for suspicious patterns in URL
        if self._contains_dangerous_patterns(str(request.url)):
            SECURITY_VIOLATIONS.labels(violation_type="malicious_url").inc()
            logger.warning(f"Suspicious URL detected: {request.url}")
            return JSONResponse(
                status_code=400,
                content={"detail": "Invalid request"}
            )

        # Validate headers
        user_agent = request.headers.get("user-agent", "")
        if not user_agent or len(user_agent) > 1000:
            SECURITY_VIOLATIONS.labels(violation_type="invalid_user_agent").inc()
            return JSONResponse(
                status_code=400,
                content={"detail": "Invalid user agent"}
            )

        return await call_next(request)

    def _contains_dangerous_patterns(self, text: str) -> bool:
        """Check if text contains dangerous patterns."""
        text_lower = text.lower()
        for pattern in self.DANGEROUS_PATTERNS:
            if re.search(pattern, text_lower, re.IGNORECASE):
                return True
        return False


class MetricsMiddleware(BaseHTTPMiddleware):
    """Collect metrics for monitoring."""

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        start_time = time.time()
        
        # Get endpoint pattern for metrics
        endpoint = self._get_endpoint_pattern(request.url.path)
        
        try:
            response = await call_next(request)
            status_code = response.status_code
        except Exception as e:
            status_code = 500
            logger.error(f"Request failed: {e}")
            response = JSONResponse(
                status_code=500,
                content={"detail": "Internal server error"}
            )

        # Record metrics
        REQUEST_COUNT.labels(
            method=request.method,
            endpoint=endpoint,
            status_code=status_code
        ).inc()

        REQUEST_DURATION.labels(
            method=request.method,
            endpoint=endpoint
        ).observe(time.time() - start_time)

        return response

    def _get_endpoint_pattern(self, path: str) -> str:
        """Convert path to pattern for metrics grouping."""
        # Replace dynamic segments with placeholders
        patterns = [
            (r'/api/booking/\d+', '/api/booking/{id}'),
            (r'/api/stripe/\w+', '/api/stripe/{id}'),
            (r'/api/auth/\w+', '/api/auth/{action}'),
        ]
        
        for pattern, replacement in patterns:
            path = re.sub(pattern, replacement, path)
        
        return path


class RateLimitByIPMiddleware(BaseHTTPMiddleware):
    """Simple in-memory rate limiting by IP address."""

    def __init__(self, app, requests_per_minute: int = 100):
        super().__init__(app)
        self.requests_per_minute = requests_per_minute
        self.request_counts = {}
        self.last_reset = time.time()

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Reset counts every minute
        current_time = time.time()
        if current_time - self.last_reset > 60:
            self.request_counts.clear()
            self.last_reset = current_time

        # Get client IP
        client_ip = self._get_client_ip(request)
        
        # Check rate limit
        current_count = self.request_counts.get(client_ip, 0)
        if current_count >= self.requests_per_minute:
            SECURITY_VIOLATIONS.labels(violation_type="rate_limit").inc()
            return JSONResponse(
                status_code=429,
                content={"detail": "Rate limit exceeded"},
                headers={"Retry-After": "60"}
            )

        # Increment counter
        self.request_counts[client_ip] = current_count + 1

        return await call_next(request)

    def _get_client_ip(self, request: Request) -> str:
        """Extract client IP from request."""
        # Check forwarded headers
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            return forwarded_for.split(",")[0].strip()
        
        real_ip = request.headers.get("X-Real-IP")
        if real_ip:
            return real_ip
        
        # Fallback to client host
        return getattr(request.client, "host", "unknown")


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """Log requests for monitoring and debugging."""

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        start_time = time.time()
        request_id = str(uuid.uuid4())
        
        # Log request
        logger.info(
            f"Request started",
            extra={
                "request_id": request_id,
                "method": request.method,
                "url": str(request.url),
                "user_agent": request.headers.get("user-agent", ""),
                "client_ip": self._get_client_ip(request),
            }
        )

        try:
            response = await call_next(request)
            duration = time.time() - start_time
            
            # Log response
            logger.info(
                f"Request completed",
                extra={
                    "request_id": request_id,
                    "status_code": response.status_code,
                    "duration": duration,
                }
            )
            
            # Add request ID to response
            response.headers["X-Request-ID"] = request_id
            
            return response
            
        except Exception as e:
            duration = time.time() - start_time
            logger.error(
                f"Request failed",
                extra={
                    "request_id": request_id,
                    "error": str(e),
                    "duration": duration,
                }
            )
            raise

    def _get_client_ip(self, request: Request) -> str:
        """Extract client IP from request."""
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            return forwarded_for.split(",")[0].strip()
        
        real_ip = request.headers.get("X-Real-IP")
        if real_ip:
            return real_ip
        
        return getattr(request.client, "host", "unknown")