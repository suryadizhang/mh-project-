"""
Role definitions and role-based access control.

Defines the 5-tier RBAC system for My Hibachi admin access control.
"""

from enum import Enum


class UserRole(str, Enum):
    """
    5-tier role hierarchy for admin access control.

    Roles (highest to lowest):
    - SUPER_ADMIN: Full system access, can manage admins
    - ADMIN: Most operations, cannot manage admin accounts
    - CUSTOMER_SUPPORT: Customer-facing operations only (all bookings)
    - STATION_MANAGER: Station-specific view + chef scheduling, can work as chef
    - CHEF: View own schedule, update availability, see assigned event details

    ROLE-SPECIFIC PAGE VIEWS:
    =========================
    Each role has a dedicated page/view in the admin panel:
    - SUPER_ADMIN: Full admin dashboard with all menu options
    - ADMIN: Admin dashboard scoped to assigned stations
    - CUSTOMER_SUPPORT: Customer-focused dashboard (bookings, reviews, leads)
    - STATION_MANAGER: Station dashboard (chef scheduling, station bookings)
    - CHEF: Chef portal (own schedule, availability, assigned event details)

    Each role ONLY sees options relevant to their job tasks.
    No role can access pages/features outside their scope.
    """

    SUPER_ADMIN = "SUPER_ADMIN"
    ADMIN = "ADMIN"
    CUSTOMER_SUPPORT = "CUSTOMER_SUPPORT"
    STATION_MANAGER = "STATION_MANAGER"
    CHEF = "CHEF"


def get_role_hierarchy_level(role: UserRole) -> int:
    """
    Get numeric level for role hierarchy (higher = more permissions).

    Returns:
        4: SUPER_ADMIN
        3: ADMIN
        2: CUSTOMER_SUPPORT
        1: STATION_MANAGER
        0: Unknown
    """
    hierarchy = {
        UserRole.SUPER_ADMIN: 4,
        UserRole.ADMIN: 3,
        UserRole.CUSTOMER_SUPPORT: 2,
        UserRole.STATION_MANAGER: 1,
    }
    return hierarchy.get(role, 0)


# Legacy role mapping for backwards compatibility
LEGACY_ROLE_MAPPING = {
    "superadmin": UserRole.SUPER_ADMIN,
    "admin": UserRole.ADMIN,
    "staff": UserRole.CUSTOMER_SUPPORT,
    "support": UserRole.CUSTOMER_SUPPORT,
    "manager": UserRole.STATION_MANAGER,
    "chef": UserRole.CHEF,
}


def normalize_role(role_str: str) -> UserRole | None:
    """
    Normalize a role string to UserRole enum.

    Handles both new enum values and legacy role names.

    Args:
        role_str: Role string (e.g., 'SUPER_ADMIN', 'superadmin', 'admin')

    Returns:
        UserRole enum value or None if invalid
    """
    if not role_str:
        return None

    # Try direct enum value match first
    try:
        if role_str in [r.value for r in UserRole]:
            return UserRole(role_str)
    except (ValueError, AttributeError):
        pass

    # Try legacy mapping
    return LEGACY_ROLE_MAPPING.get(role_str.lower())
