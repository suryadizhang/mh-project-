"""
Identity Models Package
=======================

Modular identity and access management models split into logical components:
- users: Core user model and authentication
- roles: Role-based access control (RBAC)
- stations: Multi-tenant station management
- oauth: OAuth and social authentication
- admin: Admin invitation and access control system
"""

# Core models
from .users import User, UserStatus, AuthProvider
from .roles import Role, Permission, UserRole, RolePermission
from .stations import (
    Station,
    StationUser,
    StationAccessToken,
    StationAuditLog,
    # Enums
    StationStatus,
    StationRole,
    StationPermission,
    AuditAction,
)
from .oauth import OAuthAccount
from .admin import (
    AdminInvitation,
    GoogleOAuthAccount,
    AdminAccessLog,
    InvitationStatus,
    generate_invitation_code,
    create_admin_invitation
)

__all__ = [
    # Users
    "User",
    "UserStatus",
    "AuthProvider",

    # Roles
    "Role",
    "Permission",
    "UserRole",
    "RolePermission",

    # Stations
    "Station",
    "StationUser",
    "StationAccessToken",
    "StationAuditLog",

    # Station Enums
    "StationStatus",
    "StationRole",
    "StationPermission",
    "AuditAction",

    # OAuth
    "OAuthAccount",

    # Admin
    "AdminInvitation",
    "GoogleOAuthAccount",
    "AdminAccessLog",
    "InvitationStatus",
    "generate_invitation_code",
    "create_admin_invitation",
]
