"""
JWT Token Management
====================

JWT token creation, verification, and user extraction.
Includes separate refresh token functionality with different secret.

See: .github/instructions/22-QUALITY_CONTROL.instructions.md for modularization standards
"""

import logging
import uuid
from datetime import datetime, timedelta, timezone
from typing import Any

from jose import JWTError, jwt

from core.config import settings
from utils.auth import UserRole

logger = logging.getLogger(__name__)


def create_access_token(data: dict[str, Any], expires_delta: timedelta | None = None) -> str:
    """
    Create JWT access token with JTI for blacklist tracking.

    Args:
        data: Token payload data (must include "sub" for user ID)
        expires_delta: Custom expiration time (default: ACCESS_TOKEN_EXPIRE_MINUTES)

    Returns:
        Encoded JWT access token
    """
    to_encode = data.copy()

    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(
            minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
        )

    # Add standard claims
    to_encode.update(
        {
            "exp": expire,
            "iat": datetime.now(timezone.utc),
            "jti": str(uuid.uuid4()),  # Unique token ID for blacklisting
            "type": "access",
        }
    )

    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm="HS256")
    return encoded_jwt


def create_refresh_token(user_id: str, expires_delta: timedelta | None = None) -> str:
    """
    Create JWT refresh token with separate secret and longer expiry.

    SECURITY: Uses REFRESH_TOKEN_SECRET (falls back to SECRET_KEY + suffix if not set).
    Refresh tokens should have a 7-day expiry by default.

    Args:
        user_id: User ID (UUID string)
        expires_delta: Custom expiration time (default: REFRESH_TOKEN_EXPIRE_DAYS)

    Returns:
        Encoded JWT refresh token
    """
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)

    to_encode = {
        "sub": user_id,
        "exp": expire,
        "iat": datetime.now(timezone.utc),
        "jti": str(uuid.uuid4()),  # Unique token ID for blacklisting
        "type": "refresh",
    }

    # Use separate secret for refresh tokens (more secure)
    secret = settings.REFRESH_TOKEN_SECRET or f"{settings.SECRET_KEY}_refresh"

    encoded_jwt = jwt.encode(to_encode, secret, algorithm="HS256")
    return encoded_jwt


def verify_refresh_token(token: str) -> dict[str, Any] | None:
    """
    Verify and decode JWT refresh token.

    SECURITY: Uses separate REFRESH_TOKEN_SECRET.
    Returns None if token is invalid, expired, or wrong type.

    Args:
        token: JWT refresh token string

    Returns:
        Decoded payload if valid, None otherwise
    """
    try:
        # Use separate secret for refresh tokens
        secret = settings.REFRESH_TOKEN_SECRET or f"{settings.SECRET_KEY}_refresh"

        payload = jwt.decode(token, secret, algorithms=["HS256"])

        # Verify this is actually a refresh token
        if payload.get("type") != "refresh":
            logger.warning("Token presented as refresh token but has wrong type")
            return None

        return payload
    except JWTError as e:
        logger.warning(f"Refresh token verification failed: {e}")
        return None


def verify_token(token: str) -> dict[str, Any] | None:
    """
    Verify and decode JWT access token.

    SECURITY: Rejects refresh tokens to prevent token type confusion attacks.

    Args:
        token: JWT access token string

    Returns:
        Decoded payload if valid, None otherwise
    """
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])

        # Reject refresh tokens presented as access tokens
        if payload.get("type") == "refresh":
            logger.warning("Refresh token presented as access token - rejected")
            return None

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


def decode_access_token(token: str) -> dict[str, Any] | None:
    """
    Decode JWT access token with validation.

    This is an alias for verify_token for compatibility with auth router.
    Includes JTI claim verification for token blacklisting support.

    Args:
        token: JWT access token string

    Returns:
        Decoded payload if valid, None otherwise
    """
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])

        # Reject refresh tokens presented as access tokens
        if payload.get("type") == "refresh":
            logger.warning("Refresh token presented as access token - rejected")
            return None

        # Verify JTI claim exists (required for blacklist tracking)
        if "jti" not in payload:
            logger.warning("Token missing JTI claim")
            return None

        return payload
    except JWTError as e:
        logger.warning(f"Token decode failed: {e}")
        return None


__all__ = [
    "create_access_token",
    "create_refresh_token",
    "verify_token",
    "verify_refresh_token",
    "extract_user_from_token",
    "decode_access_token",
]
