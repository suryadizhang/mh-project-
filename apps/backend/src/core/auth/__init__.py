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

    NOTE: Handles both Role enum (lowercase: "super_admin") from core/auth/models.py
    and UserRole enum (uppercase: "SUPER_ADMIN") from core/config.py.
    """

    async def role_checker(current_user=Depends(get_current_active_user)):
        if not current_user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Not authenticated",
                headers={"WWW-Authenticate": "Bearer"},
            )

        # Get user's role - AuthenticatedUser has 'role' (singular), not 'roles' (plural)
        # The role is a Role enum from core/auth/models.py with lowercase values
        user_role = getattr(current_user, "role", None)
        if user_role is None:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="User has no assigned role",
            )

        # Get the string value of the user's role (lowercase, e.g., "super_admin")
        user_role_value = user_role.value if hasattr(user_role, "value") else str(user_role)

        # Check if user's role matches any of the required roles
        # Handle both UserRole (UPPERCASE) and Role (lowercase) enums
        for role in roles:
            if isinstance(role, UserRole):
                # UserRole has UPPERCASE values like "SUPER_ADMIN"
                # Compare case-insensitively
                if user_role_value.upper() == role.value:
                    return current_user
            elif isinstance(role, str):
                # String comparison - try both cases
                if user_role_value.upper() == role.upper():
                    return current_user
            else:
                # Other enum types - compare values case-insensitively
                role_value = role.value if hasattr(role, "value") else str(role)
                if user_role_value.upper() == role_value.upper():
                    return current_user

        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Insufficient permissions. Required roles: {[str(r) for r in roles]}, User role: {user_role_value}",
        )

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
