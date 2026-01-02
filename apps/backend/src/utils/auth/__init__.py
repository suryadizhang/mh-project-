"""
Authentication and Authorization Module
=======================================

Modular package for authentication and role-based access control.

This package provides:
- Password hashing and verification (bcrypt)
- JWT token creation and validation
- FastAPI dependencies for user authentication
- 5-tier RBAC system (UserRole, Permission)
- Role checking utilities and decorators

Package Structure:
- password.py: Password hashing utilities
- tokens.py: JWT token utilities
- dependencies.py: FastAPI auth dependencies
- roles.py: UserRole enum and hierarchy
- permissions.py: Permission class with role mappings
- decorators.py: RBAC decorators for routes
- utils.py: Utility functions for permission checking

Usage:
    from utils.auth import (
        # Password functions
        hash_password,
        verify_password,
        generate_secure_password,

        # Token functions
        create_access_token,
        decode_access_token,

        # Dependencies
        get_current_user,
        get_current_user_oauth,
        get_optional_user,
        get_admin_user,

        # RBAC
        UserRole,
        Permission,
        require_role,
        require_super_admin,
        require_admin,
        require_customer_support,
        require_station_manager,
        require_any_admin,
        has_permission,
        can_access_station,
        can_modify_booking,
        can_manage_user_account,

        # Legacy decorators
        superadmin_required,
        admin_required,
    )

Modularization Notes (Batch 1 - 2025-01-30):
    Original file: utils/auth.py (1,003 lines)
    Split into 7 focused modules for maintainability.
    Each module follows single responsibility principle.
"""

# Password utilities
from .password import (
    hash_password,
    verify_password,
    generate_secure_password,
)

# Token utilities
from .tokens import (
    create_access_token,
    decode_access_token,
)

# FastAPI dependencies
from .dependencies import (
    get_current_user,
    get_current_user_oauth,
    get_optional_user,
    get_user_db,
    security,
    oauth2_scheme,
)

# Role definitions
from .roles import (
    UserRole,
    get_role_hierarchy_level,
    normalize_role,
    LEGACY_ROLE_MAPPING,
)

# Permission definitions
from .permissions import Permission

# RBAC decorators
from .decorators import (
    superadmin_required,
    admin_required,
    get_admin_user,
    require_role,
    require_super_admin,
    require_admin,
    require_customer_support,
    require_station_manager,
    require_any_admin,
)

# Utility functions
from .utils import (
    has_permission,
    can_access_station,
    can_modify_booking,
    can_manage_user_account,
)

__all__ = [
    # Password
    "hash_password",
    "verify_password",
    "generate_secure_password",
    # Tokens
    "create_access_token",
    "decode_access_token",
    # Dependencies
    "get_current_user",
    "get_current_user_oauth",
    "get_optional_user",
    "get_user_db",
    "get_admin_user",
    "security",
    "oauth2_scheme",
    # Roles
    "UserRole",
    "get_role_hierarchy_level",
    "normalize_role",
    "LEGACY_ROLE_MAPPING",
    # Permissions
    "Permission",
    # Decorators
    "superadmin_required",
    "admin_required",
    "require_role",
    "require_super_admin",
    "require_admin",
    "require_customer_support",
    "require_station_manager",
    "require_any_admin",
    # Utilities
    "has_permission",
    "can_access_station",
    "can_modify_booking",
    "can_manage_user_account",
]
