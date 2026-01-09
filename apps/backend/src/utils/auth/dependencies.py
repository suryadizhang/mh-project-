"""
FastAPI dependency functions for authentication.

Provides user retrieval dependencies for route handlers.

Security Features (Batch 1.x):
- JTI (JWT ID) verification against blacklist
- Global user session revocation support
- Redis-cached blacklist for performance
- Database fallback when Redis unavailable

Related Files:
- services/token_blacklist_service.py - Blacklist operations
- database/migrations/012_token_blacklist_and_reset.sql - Schema
"""

import logging
import sqlite3
from datetime import datetime, timezone
from typing import Any, Optional

from core.config import get_settings
from fastapi import Depends, HTTPException, Request, status
from fastapi.security import (
    HTTPAuthorizationCredentials,
    HTTPBearer,
    OAuth2PasswordBearer,
)

from .tokens import decode_access_token

settings = get_settings()
logger = logging.getLogger(__name__)

# Security schemes
security = HTTPBearer()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")


async def _check_token_blacklist(
    request: Request,
    jti: str,
    user_id: str,
    iat: Optional[int] = None,
) -> None:
    """
    Check if token is blacklisted (revoked).

    Uses Redis cache first, falls back to database.
    Raises HTTPException 401 if token is revoked.

    Args:
        request: FastAPI request (for app.state access)
        jti: JWT ID to check
        user_id: User ID to check global revocation
        iat: Token issued-at timestamp (for global revocation check)

    Raises:
        HTTPException: 401 if token is blacklisted
    """
    # Get services from app state (set in main.py lifespan)
    cache = getattr(request.app.state, "cache", None)
    db_session_factory = getattr(request.app.state, "db_session_factory", None)

    if not cache and not db_session_factory:
        # No blacklist service available - skip check (fail open for availability)
        # In production, this should be logged as a warning
        logger.warning("Blacklist check skipped - no cache or db available")
        return

    try:
        # Import here to avoid circular imports
        from services.token_blacklist_service import TokenBlacklistService

        # Create blacklist service
        async with db_session_factory() as db:
            blacklist_service = TokenBlacklistService(db=db, cache=cache)

            # Check individual token blacklist
            is_revoked = await blacklist_service.is_blacklisted(jti)
            if is_revoked:
                logger.warning(f"Revoked token attempted: jti={jti[:8]}...")
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Token has been revoked",
                    headers={"WWW-Authenticate": "Bearer"},
                )

            # Check global user session revocation (e.g., "logout all devices")
            if iat:
                iat_datetime = datetime.fromtimestamp(iat, tz=timezone.utc)
                is_user_revoked = await blacklist_service.is_user_blacklisted_since(
                    user_id, iat_datetime
                )
                if is_user_revoked:
                    logger.warning(f"User sessions revoked for user_id={user_id}")
                    raise HTTPException(
                        status_code=status.HTTP_401_UNAUTHORIZED,
                        detail="All sessions have been revoked. Please login again.",
                        headers={"WWW-Authenticate": "Bearer"},
                    )

    except HTTPException:
        raise
    except Exception as e:
        # Log error but don't fail authentication
        # This is a security/availability tradeoff
        logger.error(f"Blacklist check failed: {e}")
        # In production, you might want to fail closed instead:
        # raise HTTPException(status_code=503, detail="Authentication service unavailable")


def get_user_db():
    """Get connection to user database."""
    # For compatibility with source backend
    db_path = "users.db"
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn


async def get_current_user(
    request: Request,
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> dict[str, Any]:
    """
    Get current user from JWT token with security checks.

    Security Checks:
    1. JWT signature and expiry validation
    2. JTI (token ID) blacklist check
    3. Global user session revocation check

    Args:
        request: FastAPI request (for app.state access)
        credentials: Bearer token credentials

    Returns:
        dict: User information from token or database

    Raises:
        HTTPException: 401 if token is invalid or revoked
    """
    try:
        token = credentials.credentials
        payload = decode_access_token(token)

        if not payload:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token",
                headers={"WWW-Authenticate": "Bearer"},
            )

        username = payload.get("sub")
        if not username:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token",
                headers={"WWW-Authenticate": "Bearer"},
            )

        # Extract security fields for blacklist check
        jti = payload.get("jti")
        iat = payload.get("iat")
        user_id = payload.get("user_id") or payload.get("sub")

        # Check token blacklist (revocation)
        if jti and user_id:
            await _check_token_blacklist(request, jti, str(user_id), iat)

        # For development mode with mock user
        if settings.environment == "development" and username == "dev-user":
            return {
                "id": "dev-user-123",
                "username": "dev-user",
                "email": "dev@myhibachi.com",
                "role": "superadmin",
                "is_admin": True,
            }

        # Check user database (compatible with source backend)
        try:
            conn = get_user_db()
            c = conn.cursor()
            c.execute("SELECT * FROM users WHERE username = ?", (username,))
            user = c.fetchone()
            conn.close()

            if user:
                return dict(user)

        except sqlite3.Error as e:
            logger.warning(f"Database error: {e}")

        # Fallback for JWT-only authentication
        return {
            "id": payload.get("user_id", username),
            "username": username,
            "role": payload.get("role", "user"),
            "email": payload.get("email", ""),
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Auth error: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication failed",
            headers={"WWW-Authenticate": "Bearer"},
        )


async def get_current_user_oauth(
    request: Request,
    token: str = Depends(oauth2_scheme),
) -> dict[str, Any]:
    """
    Get current user from OAuth2 token (for compatibility).

    Security Checks:
    1. JWT signature and expiry validation
    2. JTI (token ID) blacklist check
    3. Global user session revocation check
    """
    payload = decode_access_token(token)
    if not payload:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")

    username = payload.get("sub")

    # Extract security fields for blacklist check
    jti = payload.get("jti")
    iat = payload.get("iat")
    user_id = payload.get("user_id") or payload.get("sub")

    # Check token blacklist (revocation)
    if jti and user_id:
        await _check_token_blacklist(request, jti, str(user_id), iat)

    # Mock for development
    if settings.environment == "development":
        return {
            "id": 1,
            "username": username,
            "role": payload.get("role", "admin"),
        }

    # Production user lookup
    try:
        conn = get_user_db()
        c = conn.cursor()
        c.execute("SELECT * FROM users WHERE username = ?", (username,))
        user = c.fetchone()
        conn.close()

        if user:
            return dict(user)

    except sqlite3.Error:
        pass

    raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")


async def get_optional_user(
    request: Request,
    credentials: HTTPAuthorizationCredentials | None = Depends(security),
) -> dict[str, Any] | None:
    """Get current user if authenticated, None otherwise."""
    if not credentials:
        return None

    try:
        return await get_current_user(request, credentials)
    except HTTPException:
        return None
