"""
Security Middleware Setup
=========================

Functions to set up security middleware on FastAPI application.

See: .github/instructions/22-QUALITY_CONTROL.instructions.md for modularization standards
"""

import logging

from fastapi import FastAPI
from starlette.middleware.cors import CORSMiddleware
from starlette.middleware.sessions import SessionMiddleware
from starlette.middleware.trustedhost import TrustedHostMiddleware

from core.config import settings
from .config import SecurityConfig
from .middleware import (
    SecurityHeadersMiddleware,
    RateLimitByIPMiddleware,
    InputValidationMiddleware,
    RequestLoggingMiddleware,
    MetricsMiddleware,
)

logger = logging.getLogger(__name__)


def setup_security_middleware(app: FastAPI) -> None:
    """
    Set up all security middleware on FastAPI app.

    Call this in main.py after creating the app.

    Order matters! Middleware is executed in reverse order of addition:
    - Last added = First executed on request
    - First added = Last executed on request

    Args:
        app: FastAPI application instance
    """
    # CORS (most permissive first in chain)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.ALLOWED_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Session middleware for CSRF protection
    app.add_middleware(
        SessionMiddleware,
        secret_key=settings.SECRET_KEY,
        same_site="lax",
        https_only=settings.ENVIRONMENT == "production",
    )

    # Trusted host middleware (production only)
    if settings.ENVIRONMENT == "production":
        app.add_middleware(
            TrustedHostMiddleware,
            allowed_hosts=settings.ALLOWED_HOSTS,
        )

    # Security headers
    app.add_middleware(SecurityHeadersMiddleware)

    # Request logging (for audit trail)
    app.add_middleware(RequestLoggingMiddleware)

    # Input validation
    app.add_middleware(InputValidationMiddleware)

    # Metrics collection
    app.add_middleware(MetricsMiddleware)

    # Rate limiting by IP
    app.add_middleware(
        RateLimitByIPMiddleware,
        max_requests=SecurityConfig.DEFAULT_RATE_LIMIT,
        window_seconds=60,
    )

    logger.info("✅ Security middleware configured successfully")


def get_security_config() -> SecurityConfig:
    """Get security configuration"""
    return SecurityConfig


__all__ = [
    "setup_security_middleware",
    "get_security_config",
]
