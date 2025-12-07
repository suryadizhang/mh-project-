from datetime import UTC, datetime, timedelta
import logging
import secrets
import sqlite3
import string
from typing import Any

import bcrypt
from core.config import get_settings
from fastapi import Depends, HTTPException, status
from fastapi.security import (
    HTTPAuthorizationCredentials,
    HTTPBearer,
    OAuth2PasswordBearer,
)
from jose import jwt

settings = get_settings()

logger = logging.getLogger(__name__)
security = HTTPBearer()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")

# Bcrypt rounds for hashing (12 is standard, balancing security and performance)
BCRYPT_ROUNDS = getattr(settings, "bcrypt_rounds", 12)


def hash_password(password: str) -> str:
    """Hash password using bcrypt directly (bypassing passlib version issues)."""
    if not password:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Password cannot be empty",
        )

    # Check password strength
    if len(password) < 8:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Password must be at least 8 characters long",
        )

    # Use bcrypt directly
    salt = bcrypt.gensalt(rounds=BCRYPT_ROUNDS)
    return bcrypt.hashpw(password.encode("utf-8"), salt).decode("utf-8")


def verify_password(plain: str, hashed: str) -> bool:
    """Verify password against hash using bcrypt directly (bypassing passlib version issues)."""
    try:
        return bcrypt.checkpw(plain.encode("utf-8"), hashed.encode("utf-8"))
    except Exception as e:
        logger.warning(f"Password verification error: {e}")
        return False


def generate_secure_password(length: int = 16) -> str:
    """Generate a cryptographically secure password."""
    length = max(length, 8)

    # Ensure complexity requirements
    characters = string.ascii_letters + string.digits + "!@#$%^&*"
    password = "".join(secrets.choice(characters) for _ in range(length))

    # Ensure at least one of each type
    if not any(c.islower() for c in password):
        password = password[:-1] + secrets.choice(string.ascii_lowercase)
    if not any(c.isupper() for c in password):
        password = password[:-1] + secrets.choice(string.ascii_uppercase)
    if not any(c.isdigit() for c in password):
        password = password[:-1] + secrets.choice(string.digits)
    if not any(c in "!@#$%^&*" for c in password):
        password = password[:-1] + secrets.choice("!@#$%^&*")

    return password


def create_access_token(data: dict, expires_delta: timedelta | None = None):
    """Create JWT access token with enhanced security."""
    to_encode = data.copy()

    # Add timestamp and jti for token tracking
    now = datetime.now(UTC)
    to_encode.update(
        {"iat": now, "jti": secrets.token_urlsafe(16)}
    )  # Unique token ID

    if expires_delta:
        expire = now + expires_delta
    else:
        expire = now + timedelta(minutes=settings.access_token_expire_minutes)

    to_encode.update({"exp": expire})

    try:
        encoded_jwt = jwt.encode(
            to_encode, settings.secret_key, algorithm=settings.jwt_algorithm
        )
        return encoded_jwt
    except Exception as e:
        logger.exception(f"Token creation error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Token creation failed",
        )


def decode_access_token(token: str) -> dict | None:
    """Decode JWT access token with enhanced validation."""
    try:
        payload = jwt.decode(
            token,
            settings.secret_key,
            algorithms=[settings.jwt_algorithm],
            options={"verify_exp": True, "verify_iat": True},
        )

        # Additional security checks
        if "jti" not in payload:
            logger.warning("Token missing JTI claim")
            return None

        return payload
    except jwt.ExpiredSignatureError:
        logger.warning("Token expired")
        return None
    except jwt.InvalidTokenError as e:
        logger.warning(f"Invalid token: {e}")
        return None
    except Exception as e:
        logger.exception(f"Token decode error: {e}")
        return None


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
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token"
        )

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

    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found"
    )


def superadmin_required(user=Depends(get_current_user_oauth)):
    """Dependency to require superadmin privileges."""
    if user.get("role") != "superadmin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Superadmin privileges required",
        )
    return user


def admin_required(user=Depends(get_current_user_oauth)):
    """Dependency to require admin privileges."""
    if user.get("role") not in ("admin", "superadmin"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin privileges required",
        )
    return user


async def get_admin_user(
    current_user: dict[str, Any] = Depends(get_current_user),
) -> dict[str, Any]:
    """Ensure current user is admin (legacy compatibility)."""
    if current_user.get("role") not in ("admin", "superadmin"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required",
        )
    return current_user


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


# ============================================================================
# 4-TIER RBAC SYSTEM (New Implementation)
# ============================================================================

from collections.abc import Callable
from enum import Enum


class UserRole(str, Enum):
    """
    4-tier role hierarchy for admin access control.

    Roles (highest to lowest):
    - SUPER_ADMIN: Full system access, can manage admins
    - ADMIN: Most operations, cannot manage admin accounts
    - CUSTOMER_SUPPORT: Customer-facing operations only
    - STATION_MANAGER: Station-specific operations
    """

    SUPER_ADMIN = "SUPER_ADMIN"
    ADMIN = "ADMIN"
    CUSTOMER_SUPPORT = "CUSTOMER_SUPPORT"
    STATION_MANAGER = "STATION_MANAGER"


class Permission:
    """
    Granular permission definitions for each role aligned with My Hibachi business model.

    Role Hierarchy (My Hibachi Business Model - CORRECTED):

    SUPER_ADMIN (Platform Owner):
        - Full system access across ALL stations
        - Manage all admin accounts and their station assignments
        - Create/delete stations and system settings
        - Only role that can create ADMIN, CUSTOMER_SUPPORT accounts

    ADMIN (Station Admin - Multi-Station via Assignment):
        - Access stations ASSIGNED by SUPER_ADMIN (can be multiple or all)
        - Full CRUD for bookings, customers, chefs in assigned stations
        - Can CREATE/DELETE: STATION_MANAGER and CHEF accounts for assigned stations
        - CANNOT manage other ADMIN or SUPER_ADMIN accounts
        - CANNOT create/delete stations (only SUPER_ADMIN)

    CUSTOMER_SUPPORT:
        - ALL customer-related operations (bookings, reviews, complaints, inquiries)
        - Can VIEW and EDIT bookings directly (no approval needed for edits)
        - DELETE bookings requires approval from ADMIN or SUPER_ADMIN
        - Full access to customer, lead, review features
        - No access to financial, system settings, or user account management

    STATION_MANAGER:
        - View-only access to their assigned station
        - Schedule internal chefs for their station
        - Can CREATE/DELETE: CHEF accounts for their station ONLY
        - NO booking adjustments (handled by customer support + admin)

    CHEF (Future - Backend ready, UI pending):
        - View their own schedule
        - Update their availability
        - Dedicated chef portal page (future admin panel improvement)
    """

    # ========== BOOKING PERMISSIONS ==========
    # SUPER_ADMIN: All bookings across all stations
    # ADMIN: Full CRUD for assigned station(s) bookings
    # CUSTOMER_SUPPORT: View all, Edit directly, Delete WITH approval
    # STATION_MANAGER: View their station's bookings ONLY (read-only)
    BOOKING_VIEW_ALL = [UserRole.SUPER_ADMIN]  # Platform-wide view
    BOOKING_VIEW_ASSIGNED = [UserRole.ADMIN]  # Assigned stations only
    BOOKING_VIEW_STATION = [
        UserRole.CUSTOMER_SUPPORT,
        UserRole.STATION_MANAGER,
    ]  # Station-scoped
    BOOKING_CREATE = [
        UserRole.SUPER_ADMIN,
        UserRole.ADMIN,
        UserRole.CUSTOMER_SUPPORT,
    ]
    BOOKING_UPDATE = [
        UserRole.SUPER_ADMIN,
        UserRole.ADMIN,
        UserRole.CUSTOMER_SUPPORT,
    ]  # CS can edit directly
    BOOKING_DELETE = [
        UserRole.SUPER_ADMIN,
        UserRole.ADMIN,
    ]  # Direct delete (no approval)
    BOOKING_DELETE_WITH_APPROVAL = [
        UserRole.CUSTOMER_SUPPORT
    ]  # CS needs approval for delete only

    # ========== CUSTOMER PERMISSIONS ==========
    # CUSTOMER_SUPPORT has FULL access to all customer-related features
    CUSTOMER_VIEW = [
        UserRole.SUPER_ADMIN,
        UserRole.ADMIN,
        UserRole.CUSTOMER_SUPPORT,
    ]
    CUSTOMER_CREATE = [
        UserRole.SUPER_ADMIN,
        UserRole.ADMIN,
        UserRole.CUSTOMER_SUPPORT,
    ]
    CUSTOMER_UPDATE = [
        UserRole.SUPER_ADMIN,
        UserRole.ADMIN,
        UserRole.CUSTOMER_SUPPORT,
    ]
    CUSTOMER_DELETE = [
        UserRole.SUPER_ADMIN,
        UserRole.ADMIN,
        UserRole.CUSTOMER_SUPPORT,
    ]  # CS can delete customers

    # ========== LEAD PERMISSIONS ==========
    # CUSTOMER_SUPPORT handles all leads
    LEAD_VIEW = [
        UserRole.SUPER_ADMIN,
        UserRole.ADMIN,
        UserRole.CUSTOMER_SUPPORT,
    ]
    LEAD_MANAGE = [
        UserRole.SUPER_ADMIN,
        UserRole.ADMIN,
        UserRole.CUSTOMER_SUPPORT,
    ]
    LEAD_DELETE = [
        UserRole.SUPER_ADMIN,
        UserRole.ADMIN,
        UserRole.CUSTOMER_SUPPORT,
    ]  # CS can delete leads

    # ========== REVIEW PERMISSIONS ==========
    # CUSTOMER_SUPPORT handles all reviews and complaints
    REVIEW_VIEW = [
        UserRole.SUPER_ADMIN,
        UserRole.ADMIN,
        UserRole.CUSTOMER_SUPPORT,
    ]
    REVIEW_MANAGE = [
        UserRole.SUPER_ADMIN,
        UserRole.ADMIN,
        UserRole.CUSTOMER_SUPPORT,
    ]  # Respond to reviews
    REVIEW_MODERATE = [
        UserRole.SUPER_ADMIN,
        UserRole.ADMIN,
        UserRole.CUSTOMER_SUPPORT,
    ]  # Approve/flag reviews
    REVIEW_DELETE = [
        UserRole.SUPER_ADMIN,
        UserRole.ADMIN,
        UserRole.CUSTOMER_SUPPORT,
    ]  # CS can delete reviews

    # ========== COMPLAINT PERMISSIONS (Customer Support specialty) ==========
    COMPLAINT_VIEW = [
        UserRole.SUPER_ADMIN,
        UserRole.ADMIN,
        UserRole.CUSTOMER_SUPPORT,
    ]
    COMPLAINT_MANAGE = [
        UserRole.SUPER_ADMIN,
        UserRole.ADMIN,
        UserRole.CUSTOMER_SUPPORT,
    ]
    COMPLAINT_RESOLVE = [
        UserRole.SUPER_ADMIN,
        UserRole.ADMIN,
        UserRole.CUSTOMER_SUPPORT,
    ]

    # ========== CHEF PERMISSIONS ==========
    # ADMIN: Manage chefs for assigned stations
    # STATION_MANAGER: View + schedule chefs, CREATE/DELETE chef accounts for their station
    CHEF_VIEW_ALL = [UserRole.SUPER_ADMIN]  # Platform-wide chef view
    CHEF_VIEW_ASSIGNED = [UserRole.ADMIN]  # Chefs in assigned stations
    CHEF_VIEW_STATION = [UserRole.STATION_MANAGER]  # Own station's chefs only
    CHEF_MANAGE = [
        UserRole.SUPER_ADMIN,
        UserRole.ADMIN,
    ]  # CRUD operations on chefs
    CHEF_ASSIGN = [
        UserRole.SUPER_ADMIN,
        UserRole.ADMIN,
    ]  # Assign chefs to bookings
    CHEF_SCHEDULE = [
        UserRole.SUPER_ADMIN,
        UserRole.ADMIN,
        UserRole.STATION_MANAGER,
    ]  # Schedule chefs
    CHEF_ACCOUNT_CREATE = [
        UserRole.SUPER_ADMIN,
        UserRole.ADMIN,
        UserRole.STATION_MANAGER,
    ]  # Create chef accounts
    CHEF_ACCOUNT_DELETE = [
        UserRole.SUPER_ADMIN,
        UserRole.ADMIN,
        UserRole.STATION_MANAGER,
    ]  # Delete chef accounts

    # ========== STATION MANAGER ACCOUNT PERMISSIONS ==========
    # ADMIN can create/delete STATION_MANAGER accounts for their assigned stations
    STATION_MANAGER_VIEW = [UserRole.SUPER_ADMIN, UserRole.ADMIN]
    STATION_MANAGER_CREATE = [
        UserRole.SUPER_ADMIN,
        UserRole.ADMIN,
    ]  # ADMIN can create for assigned stations
    STATION_MANAGER_DELETE = [
        UserRole.SUPER_ADMIN,
        UserRole.ADMIN,
    ]  # ADMIN can delete for assigned stations

    # ========== STATION PERMISSIONS ==========
    # SUPER_ADMIN: All stations
    # ADMIN: Only their assigned stations (can be multiple)
    # STATION_MANAGER: View only their station (no edits)
    STATION_VIEW_ALL = [UserRole.SUPER_ADMIN]
    STATION_VIEW_ASSIGNED = [UserRole.ADMIN]  # Multiple assigned stations
    STATION_VIEW_OWN = [UserRole.STATION_MANAGER]  # Single assigned station
    STATION_CREATE = [UserRole.SUPER_ADMIN]  # Only SUPER_ADMIN
    STATION_MANAGE = [UserRole.SUPER_ADMIN]  # Create/delete stations
    STATION_MANAGE_ASSIGNED = [
        UserRole.ADMIN
    ]  # Edit assigned station settings
    STATION_DELETE = [UserRole.SUPER_ADMIN]  # Only SUPER_ADMIN

    # ========== USER ACCOUNT PERMISSIONS ==========
    # SUPER_ADMIN: Can manage all account types
    # ADMIN: Can create STATION_MANAGER and CHEF for assigned stations
    # STATION_MANAGER: Can create CHEF for their station only

    # Super Admin account management (SUPER_ADMIN only)
    SUPER_ADMIN_VIEW = [UserRole.SUPER_ADMIN]
    SUPER_ADMIN_CREATE = [UserRole.SUPER_ADMIN]
    SUPER_ADMIN_DELETE = [UserRole.SUPER_ADMIN]

    # Admin account management (SUPER_ADMIN only)
    ADMIN_VIEW = [UserRole.SUPER_ADMIN]
    ADMIN_CREATE = [UserRole.SUPER_ADMIN]
    ADMIN_UPDATE = [UserRole.SUPER_ADMIN]
    ADMIN_DELETE = [UserRole.SUPER_ADMIN]
    ADMIN_ASSIGN_STATIONS = [UserRole.SUPER_ADMIN]  # Assign stations to admins

    # Customer Support account management (SUPER_ADMIN only)
    CUSTOMER_SUPPORT_VIEW = [UserRole.SUPER_ADMIN]
    CUSTOMER_SUPPORT_CREATE = [UserRole.SUPER_ADMIN]
    CUSTOMER_SUPPORT_DELETE = [UserRole.SUPER_ADMIN]

    # ========== FINANCIAL PERMISSIONS ==========
    # ADMIN: Financial reports for their assigned stations
    FINANCIAL_VIEW_ALL = [UserRole.SUPER_ADMIN]
    FINANCIAL_VIEW_ASSIGNED = [UserRole.ADMIN]  # Assigned stations only
    FINANCIAL_REFUND = [UserRole.SUPER_ADMIN, UserRole.ADMIN]
    FINANCIAL_REPORTS = [UserRole.SUPER_ADMIN, UserRole.ADMIN]

    # ========== AUDIT PERMISSIONS ==========
    AUDIT_VIEW_ALL = [UserRole.SUPER_ADMIN]
    AUDIT_VIEW_ASSIGNED = [UserRole.ADMIN]  # Assigned stations audit
    AUDIT_VIEW_OWN = [UserRole.CUSTOMER_SUPPORT, UserRole.STATION_MANAGER]
    AUDIT_EXPORT = [UserRole.SUPER_ADMIN, UserRole.ADMIN]

    # ========== SYSTEM PERMISSIONS ==========
    SYSTEM_SETTINGS = [
        UserRole.SUPER_ADMIN
    ]  # Only SUPER_ADMIN for system settings
    SYSTEM_ANALYTICS_ALL = [UserRole.SUPER_ADMIN]
    SYSTEM_ANALYTICS_ASSIGNED = [UserRole.ADMIN]  # Assigned stations analytics
    SYSTEM_ANALYTICS_STATION = [
        UserRole.STATION_MANAGER
    ]  # Single station analytics

    # ========== APPROVAL WORKFLOW PERMISSIONS ==========
    # For customer_support booking DELETE requiring approval
    APPROVAL_GRANT = [
        UserRole.SUPER_ADMIN,
        UserRole.ADMIN,
    ]  # Can approve/reject delete requests
    APPROVAL_REQUEST = [
        UserRole.CUSTOMER_SUPPORT
    ]  # Can request approval for delete


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

        # Handle legacy roles (convert to new format)
        role_mapping = {
            "superadmin": UserRole.SUPER_ADMIN,
            "admin": UserRole.ADMIN,
            "staff": UserRole.CUSTOMER_SUPPORT,
            "support": UserRole.CUSTOMER_SUPPORT,
            "manager": UserRole.STATION_MANAGER,
        }

        # Try to get role from enum or mapping
        try:
            if user_role_str in [r.value for r in UserRole]:
                user_role = UserRole(user_role_str)
            else:
                user_role = role_mapping.get(user_role_str.lower(), None)
        except (ValueError, AttributeError):
            user_role = None

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


# ========== UTILITY FUNCTIONS ==========


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

    # Handle legacy roles
    role_mapping = {
        "superadmin": UserRole.SUPER_ADMIN,
        "admin": UserRole.ADMIN,
        "staff": UserRole.CUSTOMER_SUPPORT,
        "support": UserRole.CUSTOMER_SUPPORT,
        "manager": UserRole.STATION_MANAGER,
    }

    try:
        if user_role_str in [r.value for r in UserRole]:
            user_role = UserRole(user_role_str)
        else:
            user_role = role_mapping.get(user_role_str.lower(), None)
    except (ValueError, AttributeError):
        return False

    return user_role in allowed_roles


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
    assigned_station_ids = user.get(
        "assigned_station_ids", []
    )  # List of assigned stations
    assigned_station_id = user.get(
        "assigned_station_id"
    )  # Single station (legacy/station_manager)

    # Ensure assigned_station_ids is a list
    if not isinstance(assigned_station_ids, list):
        assigned_station_ids = (
            [assigned_station_ids] if assigned_station_ids else []
        )

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


def can_modify_booking(
    user: dict, action: str = "update"
) -> tuple[bool, bool]:
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
