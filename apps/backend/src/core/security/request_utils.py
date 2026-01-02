"""
Request Utilities
=================

Utilities for extracting information from HTTP requests.

See: .github/instructions/22-QUALITY_CONTROL.instructions.md for modularization standards
"""

import logging
import re

from fastapi import Request

logger = logging.getLogger(__name__)


def get_client_ip(request: Request) -> str:
    """Get real client IP from request (handles proxies)"""
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else "unknown"


def get_endpoint_pattern(path: str) -> str:
    """
    Normalize path for metrics (replace IDs with placeholders).

    Examples:
        /api/v1/bookings/123-456-789 -> /api/v1/bookings/{id}
        /api/v1/users/abc/orders/def -> /api/v1/users/{id}/orders/{id}
    """
    # Replace UUIDs with {id}
    pattern = re.sub(
        r"[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}",
        "{id}",
        path,
    )
    # Replace numeric IDs with {id}
    pattern = re.sub(r"/\d+", "/{id}", pattern)
    return pattern


__all__ = [
    "get_client_ip",
    "get_endpoint_pattern",
]
