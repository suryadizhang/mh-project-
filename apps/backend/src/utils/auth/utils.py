"""
Utility functions for role-based access control.

Provides helper functions for permission checking in business logic.
"""

from .roles import UserRole, normalize_role


def has_permission(user: dict, allowed_roles: list[UserRole]) -> bool:
    """
    Check if user has permission (utility function for non-endpoint logic).

    Usage:
        if has_permission(current_user, Permission.BOOKING_DELETE):
            # User can delete bookings
            ...

    Args:
        user: User dictionary
        allowed_roles: List of roles that have permission

    Returns:
        True if user has permission, False otherwise
    """
    user_role_str = user.get("role")
    user_role = normalize_role(user_role_str)

    if user_role is None:
        return False

    return user_role in allowed_roles


def can_access_station(user: dict, station_id: str) -> bool:
    """
    Check if user can access a specific station (My Hibachi Business Model - CORRECTED).

    Station Access Rules:
    - SUPER_ADMIN: Can access ALL stations (platform-wide)
    - ADMIN: Can access ASSIGNED stations (multiple possible, assigned by SUPER_ADMIN)
    - CUSTOMER_SUPPORT: Can access all stations (for customer support across all stations)
    - STATION_MANAGER: Can access ONLY their single assigned station (view-only)

    Args:
        user: User dictionary with 'role', 'assigned_station_ids' (list), and 'assigned_station_id' (single) fields
        station_id: Station ID to check access for

    Returns:
        True if user can access station, False otherwise
    """
    user_role_str = user.get("role")

    # Get assigned stations (support both list and single value)
    assigned_station_ids = user.get("assigned_station_ids", [])  # List of assigned stations
    assigned_station_id = user.get("assigned_station_id")  # Single station (legacy/station_manager)

    # Ensure assigned_station_ids is a list
    if not isinstance(assigned_station_ids, list):
        assigned_station_ids = [assigned_station_ids] if assigned_station_ids else []

    # Include single assigned_station_id in the list if present
    if assigned_station_id and assigned_station_id not in assigned_station_ids:
        assigned_station_ids.append(assigned_station_id)

    # SUPER_ADMIN can access everything (platform owner)
    if user_role_str in [
        UserRole.SUPER_ADMIN.value,
        "superadmin",
        "SUPER_ADMIN",
        "super_admin",
    ]:
        return True

    # CUSTOMER_SUPPORT can view all stations (for customer needs across all stations)
    if user_role_str in [
        UserRole.CUSTOMER_SUPPORT.value,
        "support",
        "staff",
        "customer_support",
        "CUSTOMER_SUPPORT",
    ]:
        return True

    # ADMIN can access their ASSIGNED stations (multiple possible)
    if user_role_str in [UserRole.ADMIN.value, "admin", "ADMIN"]:
        # Check if station_id is in their assigned stations
        return station_id in assigned_station_ids

    # STATION_MANAGER can only access their single assigned station (view-only)
    if user_role_str in [
        UserRole.STATION_MANAGER.value,
        "manager",
        "station_manager",
        "STATION_MANAGER",
    ]:
        return station_id in assigned_station_ids

    return False


def can_modify_booking(user: dict, action: str = "update") -> tuple[bool, bool]:
    """
    Check if user can modify (update/delete) a booking.

    Args:
        user: User dictionary with role info
        action: "update" or "delete"

    Returns:
        Tuple of (can_perform_action: bool, needs_approval: bool)

    Business Rules (CORRECTED):
    - SUPER_ADMIN: Can update/delete directly (no approval needed)
    - ADMIN: Can update/delete for assigned stations directly (no approval needed)
    - CUSTOMER_SUPPORT:
        * UPDATE: Can update directly (no approval needed) - full customer support capabilities
        * DELETE: Requires approval from ADMIN or SUPER_ADMIN
    - STATION_MANAGER: Cannot modify bookings (view-only)
    """
    user_role_str = user.get("role")

    # SUPER_ADMIN can do everything directly
    if user_role_str in [
        UserRole.SUPER_ADMIN.value,
        "superadmin",
        "SUPER_ADMIN",
        "super_admin",
    ]:
        return (True, False)  # Can perform action, no approval needed

    # ADMIN can modify for assigned stations directly
    if user_role_str in [UserRole.ADMIN.value, "admin", "ADMIN"]:
        return (True, False)  # Can perform action, no approval needed

    # CUSTOMER_SUPPORT - update is direct, delete needs approval
    if user_role_str in [
        UserRole.CUSTOMER_SUPPORT.value,
        "support",
        "staff",
        "customer_support",
        "CUSTOMER_SUPPORT",
    ]:
        if action == "update":
            return (
                True,
                False,
            )  # Can update directly - full customer support capability
        elif action == "delete":
            return (True, True)  # Can delete, but needs approval
        else:
            return (True, False)  # Default to direct access for other actions

    # STATION_MANAGER cannot modify bookings
    return (False, False)


def can_manage_user_account(
    current_user: dict, target_role: str, station_id: str | None = None
) -> tuple[bool, str]:
    """
    Check if current user can create/delete a user account of the target role.

    Args:
        current_user: The user performing the action
        target_role: The role of the account being created/deleted
        station_id: The station the new account will be assigned to

    Returns:
        Tuple of (can_manage: bool, reason: str)

    Business Rules:
    - SUPER_ADMIN: Can create/delete ALL account types
    - ADMIN: Can create/delete STATION_MANAGER and CHEF for their ASSIGNED stations only
    - STATION_MANAGER: Can create/delete CHEF for their station only
    - CUSTOMER_SUPPORT: Cannot create/delete any accounts
    """
    user_role_str = current_user.get("role")

    # Normalize target role
    target_role_upper = target_role.upper() if target_role else ""

    # SUPER_ADMIN can manage all accounts
    if user_role_str in [
        UserRole.SUPER_ADMIN.value,
        "superadmin",
        "SUPER_ADMIN",
        "super_admin",
    ]:
        return (True, "SUPER_ADMIN has full account management access")

    # ADMIN can create STATION_MANAGER and CHEF for assigned stations
    if user_role_str in [UserRole.ADMIN.value, "admin", "ADMIN"]:
        # Check if target role is allowed
        allowed_roles = ["STATION_MANAGER", "CHEF"]
        if target_role_upper not in allowed_roles:
            return (
                False,
                f"ADMIN cannot manage {target_role_upper} accounts. Only STATION_MANAGER and CHEF allowed.",
            )

        # Check if admin has access to the station
        if station_id and not can_access_station(current_user, station_id):
            return (
                False,
                f"ADMIN does not have access to station {station_id}",
            )

        return (
            True,
            f"ADMIN can manage {target_role_upper} accounts for assigned stations",
        )

    # STATION_MANAGER can create CHEF accounts for their station only
    if user_role_str in [
        UserRole.STATION_MANAGER.value,
        "manager",
        "station_manager",
        "STATION_MANAGER",
    ]:
        # Only CHEF accounts allowed
        if target_role_upper != "CHEF":
            return (
                False,
                f"STATION_MANAGER can only manage CHEF accounts, not {target_role_upper}",
            )

        # Check if station_manager has access to the station
        if station_id and not can_access_station(current_user, station_id):
            return (
                False,
                f"STATION_MANAGER does not have access to station {station_id}",
            )

        return (
            True,
            "STATION_MANAGER can manage CHEF accounts for their station",
        )

    # CUSTOMER_SUPPORT cannot manage accounts
    if user_role_str in [
        UserRole.CUSTOMER_SUPPORT.value,
        "support",
        "staff",
        "customer_support",
        "CUSTOMER_SUPPORT",
    ]:
        return (False, "CUSTOMER_SUPPORT cannot manage user accounts")

    return (False, "Unknown role - cannot manage accounts")
