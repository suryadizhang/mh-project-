"""
JWT Token Management
====================

JWT token creation, verification, and user extraction.

See: .github/instructions/22-QUALITY_CONTROL.instructions.md for modularization standards
"""

import logging
from datetime import datetime, timedelta, timezone
from typing import Any

from jose import JWTError, jwt

from core.config import settings
from utils.auth import UserRole

logger = logging.getLogger(__name__)


def create_access_token(data: dict[str, Any], expires_delta: timedelta | None = None) -> str:
    """Create JWT access token"""
    to_encode = data.copy()

    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(
            minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
        )

    to_encode.update({"exp": expire, "iat": datetime.now(timezone.utc)})

    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm="HS256")
    return encoded_jwt


def verify_token(token: str) -> dict[str, Any] | None:
    """Verify and decode JWT token"""
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
        return payload
    except JWTError:
        return None


def extract_user_from_token(token: str) -> dict[str, Any] | None:
    """Extract user information from JWT token"""
    payload = verify_token(token)
    if payload:
        user_id: str = payload.get("sub")
        role_str: str = payload.get("role", "customer")
        email: str = payload.get("email")

        if user_id is None:
            return None

        # Safely convert role string to UserRole enum
        try:
            role = UserRole(role_str.lower())
        except (ValueError, AttributeError):
            role = None  # No default role - must be valid staff role

        return {"id": user_id, "email": email, "role": role}
    return None


__all__ = [
    "create_access_token",
    "verify_token",
    "extract_user_from_token",
]
