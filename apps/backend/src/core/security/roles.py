"""
Role & Permission Checks
========================

Role-based access control utilities.

See: .github/instructions/22-QUALITY_CONTROL.instructions.md for modularization standards
"""

from utils.auth import UserRole


def get_user_rate_limit_tier(role: str | None) -> str:
    """Get rate limit tier for user role"""
    role_tiers = {
        "super_admin": "unlimited",
        "admin": "high",
        "station_manager": "high",
        "customer_support": "medium",
        "chef": "medium",
        "customer": "standard",
    }
    return role_tiers.get(role.lower() if role else "customer", "standard")


def is_admin_user(role: UserRole | str | None) -> bool:
    """Check if user has admin role"""
    if role is None:
        return False

    if isinstance(role, str):
        # Handle both underscore and no-underscore formats, case-insensitive
        role_normalized = role.lower().replace("_", "")
        return role_normalized in ["admin", "superadmin", "stationmanager"]
    return role in [UserRole.ADMIN, UserRole.SUPER_ADMIN, UserRole.STATION_MANAGER]


def is_super_admin(role: UserRole | str | None) -> bool:
    """Check if user has super admin role"""
    if role is None:
        return False

    if isinstance(role, str):
        # Handle both underscore and no-underscore formats, case-insensitive
        role_normalized = role.lower().replace("_", "")
        return role_normalized == "superadmin"
    return role == UserRole.SUPER_ADMIN


__all__ = [
    "get_user_rate_limit_tier",
    "is_admin_user",
    "is_super_admin",
]
