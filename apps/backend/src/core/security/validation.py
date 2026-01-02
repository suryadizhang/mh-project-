"""
Input Validation & Sanitization
===============================

Utilities for validating and sanitizing user input.

See: .github/instructions/22-QUALITY_CONTROL.instructions.md for modularization standards
"""

import hmac
import ipaddress
import re
from typing import Any

from core.config import settings
from .config import SecurityConfig


def sanitize_input(input_str: str, max_length: int = 1000) -> str:
    """Sanitize user input"""
    if not input_str:
        return ""

    # Truncate to max length
    sanitized = input_str[:max_length]

    # Remove potentially dangerous characters
    sanitized = re.sub(r'[<>"\']', "", sanitized)

    # Remove control characters
    sanitized = "".join(char for char in sanitized if ord(char) >= 32)

    return sanitized.strip()


def validate_email(email: str) -> bool:
    """Validate email format"""
    pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
    return re.match(pattern, email) is not None


def is_safe_url(url: str, allowed_hosts: list[str]) -> bool:
    """Check if URL is safe for redirects"""
    try:
        from urllib.parse import urlparse

        parsed = urlparse(url)

        if not parsed.netloc:
            return True

        return parsed.netloc in allowed_hosts
    except Exception:
        return False


def is_trusted_network(ip: str) -> bool:
    """Check if IP is from trusted network"""
    try:
        ip_addr = ipaddress.ip_address(ip)
        for network in SecurityConfig.TRUSTED_NETWORKS:
            if ip_addr in ipaddress.ip_network(network):
                return True
        return False
    except ValueError:
        return False


def contains_dangerous_patterns(text: str) -> bool:
    """Check if text contains dangerous patterns"""
    text_lower = text.lower()
    for pattern in SecurityConfig.DANGEROUS_PATTERNS:
        if re.search(pattern, text_lower, re.IGNORECASE):
            return True
    return False


def constant_time_compare(a: str, b: str) -> bool:
    """Constant-time string comparison to prevent timing attacks"""
    return hmac.compare_digest(a, b)


def sanitize_business_data(data: dict[str, Any]) -> dict[str, Any]:
    """Remove sensitive business data from public responses"""
    sensitive_fields = [
        "ein",
        "tax_id",
        "ssn",
        "full_address",
        "personal_email",
        "api_key",
        "secret",
    ]

    sanitized = data.copy()
    for field in sensitive_fields:
        if field in sanitized:
            del sanitized[field]

    return sanitized


def get_public_business_info() -> dict[str, Any]:
    """Get public-safe business information"""
    return {
        "business_name": settings.BUSINESS_NAME,
        "email": settings.BUSINESS_EMAIL,
        "phone": settings.BUSINESS_PHONE,
        "city": settings.BUSINESS_CITY,
        "state": settings.BUSINESS_STATE,
        "service_areas": settings.SERVICE_AREAS,
    }


__all__ = [
    "sanitize_input",
    "validate_email",
    "is_safe_url",
    "is_trusted_network",
    "contains_dangerous_patterns",
    "constant_time_compare",
    "sanitize_business_data",
    "get_public_business_info",
]
