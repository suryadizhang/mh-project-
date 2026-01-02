"""
FastAPI Security Dependencies
=============================

Authentication and authorization dependencies for FastAPI routes.

See: .github/instructions/22-QUALITY_CONTROL.instructions.md for modularization standards
"""

import functools
import logging
from typing import Any

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPBearer

from .tokens import extract_user_from_token
from .roles import is_admin_user, is_super_admin

logger = logging.getLogger(__name__)

# HTTP Bearer security scheme
security = HTTPBearer(auto_error=False)


async def get_current_user(
    request: Request,
    credentials=Depends(security),
) -> dict[str, Any] | None:
    """Get current user from JWT token (optional authentication)"""
    if not credentials:
        return None

    user = extract_user_from_token(credentials.credentials)
    if user:
        request.state.user = user
    return user


async def require_auth(
    request: Request,
    credentials=Depends(security),
) -> dict[str, Any]:
    """Require valid authentication"""
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user = extract_user_from_token(credentials.credentials)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    request.state.user = user
    return user


async def require_admin(user: dict[str, Any] = Depends(require_auth)) -> dict[str, Any]:
    """Require admin role"""
    if not is_admin_user(user.get("role")):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required",
        )
    return user


async def require_super_admin(user: dict[str, Any] = Depends(require_auth)) -> dict[str, Any]:
    """Require super admin role"""
    if not is_super_admin(user.get("role")):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Super admin access required",
        )
    return user


# Decorator for HTTPS requirement
def require_https(func):
    """Decorator to require HTTPS for sensitive endpoints"""

    @functools.wraps(func)
    async def wrapper(*args, **kwargs):
        request = None
        for arg in args:
            if isinstance(arg, Request):
                request = arg
                break
        if not request:
            request = kwargs.get("request")

        if request and request.url.scheme != "https":
            # Allow HTTP in development
            from core.config import settings

            if settings.ENVIRONMENT == "production":
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="HTTPS required for this endpoint",
                )

        return await func(*args, **kwargs)

    return wrapper


__all__ = [
    "security",
    "get_current_user",
    "require_auth",
    "require_admin",
    "require_super_admin",
    "require_https",
]
