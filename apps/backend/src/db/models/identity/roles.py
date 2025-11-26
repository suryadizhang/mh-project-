"""
Role-Based Access Control (RBAC) Models - Identity Schema

This module contains RBAC models for the identity schema.

Business Requirements:
- Role-based access control (RBAC)
- Granular permissions per resource and action
- System roles (super_admin, admin, manager, staff, chef, customer)
- Custom role creation (for station-specific needs)
- Permission assignment to roles
- Role assignment to users
- Audit trail for role changes

Models:
- Role: User roles with permissions
- Permission: Granular permissions for resources
- RolePermission: Many-to-many junction (roles ↔ permissions)
- UserRole: Many-to-many junction (users ↔ roles)
- RoleType: System role types enum
- PermissionType: Permission action types enum
"""

import enum
from datetime import datetime
from typing import List, Optional
from uuid import UUID, uuid4

from sqlalchemy import (
    Boolean,
    DateTime,
    ForeignKey,
    Index,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy import Enum as SQLEnum
from sqlalchemy import func
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from db.base_class import Base


# ==================== ENUMS ====================

class RoleType(str, enum.Enum):
    """
    System role types.

    Business Rules:
    - SUPER_ADMIN: Full system access, manages all stations and users
    - ADMIN: Station administrator, manages station users and bookings
    - MANAGER: Station manager, manages bookings and staff schedules
    - STAFF: Station staff, handles customer interactions
    - CHEF: Chef user, manages recipes and menu
    - CUSTOMER: End customer, books events

    Hierarchy (permissions inheritance):
    SUPER_ADMIN > ADMIN > MANAGER > STAFF > CHEF > CUSTOMER

    System Roles:
    - SUPER_ADMIN, ADMIN, MANAGER, STAFF, CHEF, CUSTOMER are system roles
    - System roles cannot be deleted
    - Custom roles can be created for station-specific needs
    """
    SUPER_ADMIN = "super_admin"
    ADMIN = "admin"
    MANAGER = "manager"
    STAFF = "staff"
    CHEF = "chef"
    CUSTOMER = "customer"


class PermissionType(str, enum.Enum):
    """
    Permission action types.

    Business Rules:
    - READ: View resource data
    - WRITE: Create or update resource data
    - DELETE: Remove resource data
    - EXECUTE: Execute special actions (e.g., approve booking, send email)
    - ADMIN: Full administrative control over resource

    Permission Model:
    - Permissions are defined per resource + action
    - Example: ("bookings", READ), ("bookings", WRITE), ("customers", ADMIN)
    - Roles are assigned multiple permissions
    - Users inherit permissions from their roles

    Granularity:
    - Fine-grained: Per-resource, per-action
    - Flexible: New resources can be added without code changes
    - Auditable: Permission changes tracked via RolePermission table
    """
    READ = "read"
    WRITE = "write"
    DELETE = "delete"
    EXECUTE = "execute"
    ADMIN = "admin"


# ==================== MODELS ====================

class Role(Base):
    """
    Role entity.

    Defines user roles with permissions (RBAC).

    Business Requirements:
    - Unique role name across system
    - System roles (super_admin, admin, etc.) cannot be deleted
    - Custom roles can be created per station
    - Roles can be activated/deactivated
    - Roles have multiple permissions (via RolePermission)
    - Users can have multiple roles (via UserRole)

    System Roles (is_system_role=True):
    - super_admin: Full system access
    - admin: Station administration
    - manager: Station management
    - staff: Station operations
    - chef: Recipe and menu management
    - customer: Booking and event access

    Custom Roles (is_system_role=False):
    - Created by super_admin or admin
    - Station-specific permissions
    - Can be deleted when no longer needed

    Access Control:
    - Creation: super_admin only
    - Update: super_admin only
    - Delete: super_admin only (custom roles only)
    - View: admin, manager
    """
    __tablename__ = "roles"
    __table_args__ = (
        Index("idx_roles_name", "name"),
        Index("idx_roles_role_type", "role_type"),
        Index("idx_roles_active", "is_active"),
        {"schema": "identity"}
    )

    # Primary Key
    id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        primary_key=True,
        default=uuid4
    )

    # Role Details
    name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        unique=True,
        index=True
    )
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    role_type: Mapped[RoleType] = mapped_column(
        SQLEnum(RoleType, name="roletype", schema="public", create_type=False),
        nullable=False,
        index=True
    )

    # Status
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
        index=True
    )
    is_system_role: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False
    )  # System roles cannot be deleted

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now()
    )

    # Relationships
    role_permissions: Mapped[List["RolePermission"]] = relationship(
        "RolePermission",
        back_populates="role",
        cascade="all, delete-orphan"
    )
    user_roles: Mapped[List["UserRole"]] = relationship(
        "UserRole",
        back_populates="role",
        cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<Role(id={self.id}, name={self.name}, type={self.role_type})>"


class Permission(Base):
    """
    Permission entity.

    Defines granular permissions for RBAC.

    Business Requirements:
    - Unique (resource, action) pair
    - Resource: Logical grouping (e.g., "bookings", "customers", "stations")
    - Action: Operation type (READ, WRITE, DELETE, EXECUTE, ADMIN)
    - Permissions assigned to roles (via RolePermission)
    - Users inherit permissions from roles

    Permission Examples:
    - ("bookings", READ): View bookings
    - ("bookings", WRITE): Create/update bookings
    - ("bookings", DELETE): Cancel bookings
    - ("bookings", ADMIN): Full booking management
    - ("customers", READ): View customer data
    - ("customers", WRITE): Update customer profiles
    - ("stations", ADMIN): Manage station configuration

    Access Control:
    - Creation: super_admin only (when adding new resources)
    - Update: super_admin only
    - Delete: super_admin only (when deprecating resources)
    - View: admin, manager

    Security:
    - Permissions are NOT user-specific (use roles instead)
    - Fine-grained: Per-resource, per-action
    - Auditable: Changes tracked via role_permissions table
    """
    __tablename__ = "permissions"
    __table_args__ = (
        Index("idx_permissions_resource_action", "resource", "action"),
        UniqueConstraint("resource", "action", name="uq_permissions_resource_action"),
        {"schema": "identity"}
    )

    # Primary Key
    id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        primary_key=True,
        default=uuid4
    )

    # Permission Details
    resource: Mapped[str] = mapped_column(
        String(100),
        nullable=False
    )  # e.g., "bookings", "customers", "stations"
    action: Mapped[PermissionType] = mapped_column(
        SQLEnum(PermissionType, name="permissiontype", schema="public", create_type=False),
        nullable=False
    )
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now()
    )

    # Relationships
    role_permissions: Mapped[List["RolePermission"]] = relationship(
        "RolePermission",
        back_populates="permission",
        cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<Permission(id={self.id}, resource={self.resource}, action={self.action})>"


class RolePermission(Base):
    """
    Role-Permission junction table.

    Many-to-many relationship between roles and permissions.

    Business Requirements:
    - Links roles to permissions (RBAC)
    - Unique (role_id, permission_id) pair
    - Cascade delete: If role or permission deleted, junction record removed
    - Audit trail: Track when permissions assigned

    Usage:
    - Assign permission to role: Insert RolePermission record
    - Remove permission from role: Delete RolePermission record
    - Get role's permissions: Query RolePermission.filter(role_id=...)
    - Get permission's roles: Query RolePermission.filter(permission_id=...)

    Access Control:
    - Creation: super_admin only
    - Delete: super_admin only
    - View: admin, manager
    """
    __tablename__ = "role_permissions"
    __table_args__ = (
        Index("idx_role_permissions_role_id", "role_id"),
        Index("idx_role_permissions_permission_id", "permission_id"),
        UniqueConstraint("role_id", "permission_id", name="uq_role_permissions"),
        {"schema": "identity"}
    )

    # Primary Key
    id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        primary_key=True,
        default=uuid4
    )

    # Foreign Keys
    role_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("identity.roles.id"),
        nullable=False
    )
    permission_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("identity.permissions.id"),
        nullable=False
    )

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now()
    )

    # Relationships
    role: Mapped["Role"] = relationship("Role", back_populates="role_permissions")
    permission: Mapped["Permission"] = relationship("Permission", back_populates="role_permissions")

    def __repr__(self) -> str:
        return f"<RolePermission(role_id={self.role_id}, permission_id={self.permission_id})>"


class UserRole(Base):
    """
    User-Role association table (many-to-many).

    Links users to roles for RBAC.
    Tracks who assigned the role and when.

    Business Requirements:
    - Users can have multiple roles
    - Roles can be assigned to multiple users
    - Unique (user_id, role_id) pair
    - Cascade delete: If user or role deleted, assignment removed
    - Audit: Track who assigned role and when

    Role Assignment Workflow:
    1. Super admin assigns role to user
    2. UserRole record created with assigned_by = super_admin.id
    3. User inherits permissions from role
    4. Role changes tracked via assigned_at timestamp

    Access Control:
    - Creation: super_admin, admin (for their station)
    - Delete: super_admin, admin (for their station)
    - View: super_admin, admin, manager

    Security:
    - Role assignments auditable via assigned_by and assigned_at
    - Cannot assign super_admin role without super_admin privileges
    - Station admins can only assign roles within their station
    """
    __tablename__ = "user_roles"
    __table_args__ = (
        {"schema": "identity"},
    )

    # Composite primary key
    user_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("identity.users.id", ondelete="CASCADE"),
        primary_key=True,
        comment="User ID"
    )

    role_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("identity.roles.id", ondelete="CASCADE"),
        primary_key=True,
        comment="Role ID"
    )

    # Audit fields
    assigned_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        comment="When role was assigned"
    )

    assigned_by: Mapped[Optional[UUID]] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("identity.users.id", ondelete="SET NULL"),
        nullable=True,
        comment="Who assigned this role"
    )

    # Relationships
    user: Mapped["User"] = relationship(
        "User",
        foreign_keys=[user_id],
        back_populates="user_roles"
    )
    role: Mapped["Role"] = relationship("Role", back_populates="user_roles")

    def __repr__(self) -> str:
        return f"<UserRole(user_id={self.user_id}, role_id={self.role_id})>"
