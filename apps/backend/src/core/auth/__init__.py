"""
Core authentication module for MyHibachi API.

This module provides authentication and authorization functionality.
Migrated from api.app.auth - Phase 2C Nuclear Refactor.
"""

from core.auth.middleware import (
    AuthenticatedUser,
    get_current_active_user,
    get_current_user,
    require_any_permission,
    require_permission,
    setup_auth_middleware,
)
from core.auth.models import Permission, StationUser, UserSession
from core.config import UserRole  # UserRole is in core.config, not core.auth.models
from fastapi import Depends, HTTPException, status


def require_roles(roles: list[str | UserRole]):
    """
    Dependency function to require specific roles for endpoint access.

    Usage:
        @router.get("/admin")
        async def admin_endpoint(user = Depends(require_roles([UserRole.ADMIN]))):
            return {"message": "Admin access granted"}

        # Or with string roles
        @router.post("/payments")
        async def process_payment(user = Depends(require_roles(["admin", "accountant"]))):
            return {"message": "Payment processed"}

    Args:
        roles: List of required roles (as strings or UserRole enum values)

    Returns:
        FastAPI dependency function that checks user roles

    Raises:
        HTTPException: 401 if not authenticated, 403 if insufficient permissions
    """

    async def role_checker(current_user: AuthenticatedUser = Depends(get_current_active_user)):
        if not current_user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Not authenticated",
                headers={"WWW-Authenticate": "Bearer"},
            )

        # Convert string roles to UserRole if needed
        required_roles = []
        for role in roles:
            if isinstance(role, str):
                try:
                    required_roles.append(UserRole(role))
                except ValueError:
                    required_roles.append(role)  # Keep as string if not valid enum
            else:
                required_roles.append(role)

        # Check if user has any of the required roles
        user_roles = getattr(current_user, "roles", [])
        if not any(role in user_roles for role in required_roles):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Insufficient permissions. Required roles: {[str(r) for r in required_roles]}",
            )

        return current_user

    return role_checker


__all__ = [
    # Models
    "User",
    "UserRole",
    "UserSession",
    "Permission",
    # Middleware/Dependencies
    "get_current_user",
    "get_current_active_user",
    "require_permission",
    "require_any_permission",
    "require_roles",
    "setup_auth_middleware",
    # Types
    "AuthenticatedUser",
]
