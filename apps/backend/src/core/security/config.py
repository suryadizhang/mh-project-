"""
Security Configuration
======================

Centralized security configuration constants.

See: .github/instructions/22-QUALITY_CONTROL.instructions.md for modularization standards
"""

import logging

logger = logging.getLogger(__name__)


class SecurityConfig:
    """Security configuration constants"""

    # CSRF Protection
    CSRF_TOKEN_EXPIRY = 3600  # 1 hour
    CSRF_HEADER_NAME = "X-CSRF-Token"

    # Rate Limiting
    DEFAULT_RATE_LIMIT = 100  # requests per minute
    AUTH_RATE_LIMIT = 5  # auth attempts per minute
    STRICT_RATE_LIMIT = 20  # for sensitive endpoints

    # Security Headers
    SECURITY_HEADERS = {
        "X-Content-Type-Options": "nosniff",
        "X-Frame-Options": "DENY",
        "X-XSS-Protection": "1; mode=block",
        "Strict-Transport-Security": "max-age=31536000; includeSubDomains",
        "Content-Security-Policy": "default-src 'self'",
        "Referrer-Policy": "strict-origin-when-cross-origin",
        "Permissions-Policy": "geolocation=(), microphone=(), camera=()",
    }

    # Input Validation
    MAX_REQUEST_SIZE = 10 * 1024 * 1024  # 10MB
    MAX_JSON_KEYS = 1000
    MAX_STRING_LENGTH = 10000

    # Trusted Networks (for development)
    TRUSTED_NETWORKS = ["127.0.0.0/8", "10.0.0.0/8", "172.16.0.0/12", "192.168.0.0/16"]

    # Dangerous patterns for input validation
    DANGEROUS_PATTERNS = [
        r"<script[^>]*>.*?</script>",
        r"javascript:",
        r"on\w+\s*=",
        r"<iframe[^>]*>",
        r"eval\s*\(",
        r"expression\s*\(",
        r"--",
        r";.*?--",
        r"union.*?select",
        r"drop\s+table",
    ]

    # Suspicious user agents
    SUSPICIOUS_USER_AGENTS = ["sqlmap", "nikto", "nmap", "masscan", "curl/bot"]


__all__ = ["SecurityConfig"]
