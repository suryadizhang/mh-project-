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


def normalize_role_str(role: str | None) -> str:
    """
    Normalize a role string for case-insensitive comparison.

    Handles:
    - UPPERCASE values from UserRole enum ("SUPER_ADMIN", "ADMIN")
    - lowercase values from StationRole enum ("super_admin", "admin")
    - No-underscore variants ("superadmin")

    Returns:
        Normalized lowercase string without underscores (e.g., "superadmin")
    """
    if role is None:
        return ""
    return role.lower().replace("_", "")


def role_matches(role: str | None, *targets: str) -> bool:
    """
    Check if role matches any of the target role strings.

    Handles case/underscore variations automatically.

    Args:
        role: The role string to check (can be any case/format)
        *targets: Target role names to match against (normalized internally)

    Returns:
        True if role matches any target

    Examples:
        role_matches("SUPER_ADMIN", "super_admin")  # True
        role_matches("super_admin", "superadmin")   # True
        role_matches("ADMIN", "admin", "superadmin") # True
    """
    if role is None:
        return False

    normalized = normalize_role_str(role)
    normalized_targets = [normalize_role_str(t) for t in targets]
    return normalized in normalized_targets


__all__ = [
    "get_user_rate_limit_tier",
    "is_admin_user",
    "is_super_admin",
    "normalize_role_str",
    "role_matches",
]
