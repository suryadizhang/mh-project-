"""
Security Headers Middleware
Adds essential security headers to all API responses for production security compliance
"""

from collections.abc import Callable

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """
    Add security headers to all responses

    Headers added:
    - Strict-Transport-Security (HSTS): Force HTTPS
    - X-Frame-Options: Prevent clickjacking
    - X-Content-Type-Options: Prevent MIME sniffing
    - X-XSS-Protection: Enable browser XSS filter
    - Referrer-Policy: Control referrer information
    - Content-Security-Policy: XSS and data injection protection
    - Permissions-Policy: Control browser features
    """

    async def dispatch(self, request: Request, call_next: Callable):
        """Add security headers to response"""
        response = await call_next(request)

        # HSTS - Force HTTPS for 1 year (including subdomains)
        # Tells browsers to always use HTTPS for this domain
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"

        # Clickjacking Protection
        # Prevents website from being embedded in iframe (prevents clickjacking attacks)
        response.headers["X-Frame-Options"] = "DENY"

        # MIME Type Sniffing Protection
        # Prevents browsers from MIME-sniffing away from declared content type
        response.headers["X-Content-Type-Options"] = "nosniff"

        # XSS Protection
        # Enables browser's built-in XSS filter (additional layer of protection)
        response.headers["X-XSS-Protection"] = "1; mode=block"

        # Referrer Policy
        # Controls how much referrer information is included with requests
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"

        # Content Security Policy (CSP)
        # Helps prevent XSS, clickjacking, and other code injection attacks
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; "  # Default: only load from same origin
            "script-src 'self' 'unsafe-inline' 'unsafe-eval' https://js.stripe.com; "  # Scripts: allow Stripe
            "style-src 'self' 'unsafe-inline'; "  # Styles: allow inline for styled-components
            "img-src 'self' data: https: http:; "  # Images: allow all (Cloudinary, external)
            "font-src 'self' data:; "  # Fonts: same origin or data URIs
            "connect-src 'self' https://mhapi.mysticdatanode.net https://api.stripe.com; "  # API calls
            "frame-src 'self' https://js.stripe.com; "  # Iframes: only Stripe
            "object-src 'none'; "  # No plugins (Flash, Java, etc.)
            "base-uri 'self'; "  # Restrict <base> tag URLs
            "form-action 'self'"  # Forms can only submit to same origin (NO TRAILING SEMICOLON!)
        )

        # Permissions Policy (formerly Feature-Policy)
        # Disables unused browser features to reduce attack surface
        response.headers["Permissions-Policy"] = (
            "accelerometer=(), "  # No accelerometer access
            "camera=(), "  # No camera access
            "geolocation=(), "  # No geolocation
            "gyroscope=(), "  # No gyroscope
            "magnetometer=(), "  # No magnetometer
            "microphone=(), "  # No microphone
            "payment=(), "  # Payment via Stripe API, not Payment Request API
            "usb=(), "  # No USB device access
            "interest-cohort=()"  # Disable FLoC (privacy)
        )

        return response


class RequestSizeLimiter(BaseHTTPMiddleware):
    """
    Limit request body size to prevent DoS attacks via large file uploads

    Configuration:
    - max_size: Maximum request body size in bytes (default: 10 MB)
    - Returns 413 (Payload Too Large) if exceeded
    """

    def __init__(self, app, max_size: int = 10 * 1024 * 1024):  # 10 MB default
        super().__init__(app)
        self.max_size = max_size

    async def dispatch(self, request: Request, call_next: Callable):
        """Check Content-Length header before processing request"""
        # Get Content-Length from request headers
        content_length = request.headers.get("content-length")

        if content_length and int(content_length) > self.max_size:
            # Request too large - reject before processing
            from fastapi.responses import JSONResponse

            size_mb = self.max_size / 1024 / 1024
            actual_size_mb = int(content_length) / 1024 / 1024

            return JSONResponse(
                status_code=413,
                content={
                    "error": "Request body too large",
                    "max_size_mb": f"{size_mb:.1f}",
                    "actual_size_mb": f"{actual_size_mb:.1f}",
                    "message": f"Maximum request size is {size_mb:.1f}MB. Your request is {actual_size_mb:.1f}MB.",
                },
            )

        # Request size acceptable - continue
        return await call_next(request)
