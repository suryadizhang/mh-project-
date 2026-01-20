"""
Role-based access control decorators and dependencies.

Provides FastAPI dependencies for enforcing role requirements.
"""

from collections.abc import Callable
from typing import TYPE_CHECKING

from fastapi import Depends, HTTPException, status

from .dependencies import get_current_user, get_current_user_oauth
from .roles import UserRole, normalize_role

if TYPE_CHECKING:
    from .permissions import Permission


def superadmin_required(user=Depends(get_current_user_oauth)):
    """Dependency to require superadmin privileges."""
    user_role = normalize_role(user.get("role"))
    if user_role != UserRole.SUPER_ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Superadmin privileges required",
        )
    return user


def admin_required(user=Depends(get_current_user_oauth)):
    """Dependency to require admin privileges."""
    user_role = normalize_role(user.get("role"))
    if user_role not in (UserRole.ADMIN, UserRole.SUPER_ADMIN):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin privileges required",
        )
    return user


async def get_admin_user(
    current_user: dict = Depends(get_current_user),
) -> dict:
    """Ensure current user is admin (legacy compatibility)."""
    user_role = normalize_role(current_user.get("role"))
    if user_role not in (UserRole.ADMIN, UserRole.SUPER_ADMIN):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required",
        )
    return current_user


def require_role(allowed_roles: list[UserRole]) -> Callable:
    """
    Dependency factory to require specific roles.

    Usage:
        @router.get("/admin/bookings")
        async def get_bookings(
            current_user: dict = Depends(require_role([UserRole.SUPER_ADMIN, UserRole.ADMIN, UserRole.CUSTOMER_SUPPORT]))
        ):
            # Only SUPER_ADMIN, ADMIN, or CUSTOMER_SUPPORT can access
            ...

    Args:
        allowed_roles: List of roles that can access the endpoint

    Returns:
        Dependency function that validates user role
    """

    async def role_checker(
        current_user: dict = Depends(get_current_user),
    ) -> dict:
        # Get user role (support both new and legacy formats)
        user_role_str = current_user.get("role")

        # Try to get role from enum or mapping
        user_role = normalize_role(user_role_str)

        if user_role is None:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Invalid user role: {user_role_str}",
            )

        if user_role not in allowed_roles:
            allowed_role_names = ", ".join([r.value for r in allowed_roles])
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access denied. Required role: {allowed_role_names}. Your role: {user_role.value}",
            )

        return current_user

    return role_checker


# ========== CONVENIENCE DEPENDENCIES ==========


def require_super_admin() -> Callable:
    """Require SUPER_ADMIN role (full system access)."""
    return require_role([UserRole.SUPER_ADMIN])


def require_admin() -> Callable:
    """Require ADMIN or SUPER_ADMIN role (most operations)."""
    return require_role([UserRole.SUPER_ADMIN, UserRole.ADMIN])


def require_customer_support() -> Callable:
    """Require CUSTOMER_SUPPORT, ADMIN, or SUPER_ADMIN role (customer-facing operations)."""
    return require_role(
        [UserRole.SUPER_ADMIN, UserRole.ADMIN, UserRole.CUSTOMER_SUPPORT]
    )


def require_station_manager() -> Callable:
    """Require STATION_MANAGER role (station-specific operations)."""
    return require_role([UserRole.STATION_MANAGER])


def require_any_admin() -> Callable:
    """Require any admin role (any authenticated admin user)."""
    return require_role(
        [
            UserRole.SUPER_ADMIN,
            UserRole.ADMIN,
            UserRole.CUSTOMER_SUPPORT,
            UserRole.STATION_MANAGER,
        ]
    )


def require_permissions(allowed_roles: list[UserRole]) -> Callable:
    """
    Dependency factory to require specific permissions.

    This is a wrapper around require_role that accepts Permission class attributes
    (which are lists of UserRole).

    Usage:
        from utils.auth import Permission, require_permissions

        @router.get("/payments")
        async def get_payments(
            current_user: dict = Depends(require_permissions(Permission.MANAGE_PAYMENTS))
        ):
            # Only users with MANAGE_PAYMENTS permission can access
            ...

    Args:
        allowed_roles: Permission class attribute (list of roles that can access)

    Returns:
        Dependency function that validates user has required permission
    """
    return require_role(allowed_roles)
