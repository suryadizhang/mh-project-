"""
JWT token creation and validation utilities.
"""

import logging
import secrets
from datetime import UTC, datetime, timedelta

import jwt
from fastapi import HTTPException, status

from core.config import get_settings

settings = get_settings()
logger = logging.getLogger(__name__)


def create_access_token(data: dict, expires_delta: timedelta | None = None):
    """Create JWT access token with enhanced security."""
    to_encode = data.copy()

    # Add timestamp and jti for token tracking
    now = datetime.now(UTC)
    to_encode.update(
        {
            "iat": now,
            "jti": secrets.token_urlsafe(16),  # Unique token ID
            "aud": "myhibachi-api",  # Audience claim for token validation
            "iss": "myhibachi-crm",  # Issuer claim
        }
    )

    if expires_delta:
        expire = now + expires_delta
    else:
        expire = now + timedelta(minutes=settings.access_token_expire_minutes)

    to_encode.update({"exp": expire})

    try:
        encoded_jwt = jwt.encode(to_encode, settings.secret_key, algorithm=settings.jwt_algorithm)
        return encoded_jwt
    except Exception as e:
        logger.exception(f"Token creation error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Token creation failed",
        )


def decode_access_token(token: str) -> dict | None:
    """
    Decode JWT access token with enhanced validation.

    IMPORTANT: This function is aligned with core/security/tokens.py::decode_access_token
    to ensure consistent token validation across all routers.

    Validates:
    - JWT signature (using SECRET_KEY)
    - Expiration time
    - Audience claim ("myhibachi-api")
    - JTI claim presence (for blacklist support)
    - Token type (rejects refresh tokens)
    """
    try:
        # Validate audience to match tokens created by core/security::create_access_token
        # and api/v1/endpoints/auth.py
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,  # Use uppercase for consistency with core/security
            algorithms=["HS256"],  # Hardcode algorithm for security
            audience="myhibachi-api",  # Validate audience claim
            options={"verify_exp": True, "verify_iat": True, "verify_aud": True},
        )

        # Reject refresh tokens presented as access tokens
        if payload.get("type") == "refresh":
            logger.warning("Refresh token presented as access token - rejected")
            return None

        # Verify JTI claim exists (required for blacklist tracking)
        if "jti" not in payload:
            logger.warning("Token missing JTI claim")
            return None

        return payload
    except jwt.ExpiredSignatureError:
        logger.warning("Token expired")
        return None
    except jwt.InvalidTokenError as e:
        logger.warning(f"Invalid token: {e}")
        return None
    except Exception as e:
        logger.exception(f"Token decode error: {e}")
        return None
