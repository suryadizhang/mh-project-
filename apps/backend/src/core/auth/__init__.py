"""
Compatibility shim for core.auth imports

MIGRATION NOTICE:
The old core.auth_DEPRECATED_DO_NOT_USE is archived.
Some endpoints still use old-style imports during migration.

This shim provides backward compatibility by copying old modules to new location.
Eventually these should be migrated to:
- api/deps.py - get_current_user, get_current_user_optional
- api/deps_enhanced.py - Enhanced versions
- db/models/identity.py - User, UserSession models

For now, old Station Auth endpoints will continue to work.
"""

# Re-export from middleware (old system)
from core.auth.middleware import (
    get_current_active_user,
    get_current_user,
    require_permission,
    require_any_permission,
)
from core.auth.models import UserSession
from core.config import UserRole
from db.models.identity import User
from fastapi import Depends, HTTPException, status


def require_roles(roles: list[str | UserRole]):
    """
    Dependency function to require specific roles for endpoint access.

    OLD system - kept for backward compatibility with Station Auth endpoints.
    New endpoints should use api/deps_enhanced.py instead.
    """

    async def role_checker(current_user=Depends(get_current_active_user)):
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
                    required_roles.append(role)
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


# Aliases for backward compatibility
get_db_session = None  # To be implemented if needed

__all__ = [
    "get_current_user",
    "get_current_active_user",
    "require_roles",
    "require_permission",
    "require_any_permission",
    "User",
    "UserSession",
]
