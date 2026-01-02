"""
FastAPI dependency functions for authentication.

Provides user retrieval dependencies for route handlers.
"""

import logging
import sqlite3
from typing import Any

from core.config import get_settings
from fastapi import Depends, HTTPException, status
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


def get_user_db():
    """Get connection to user database."""
    # For compatibility with source backend
    db_path = "users.db"
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> dict[str, Any]:
    """Get current user from JWT token."""
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
    token: str = Depends(oauth2_scheme),
) -> dict[str, Any]:
    """Get current user from OAuth2 token (for compatibility)."""
    payload = decode_access_token(token)
    if not payload:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")

    username = payload.get("sub")

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
    credentials: HTTPAuthorizationCredentials | None = Depends(security),
) -> dict[str, Any] | None:
    """Get current user if authenticated, None otherwise."""
    if not credentials:
        return None

    try:
        return await get_current_user(credentials)
    except HTTPException:
        return None
