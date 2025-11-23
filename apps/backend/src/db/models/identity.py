"""
SQLAlchemy Models - Identity Schema
====================================

Identity and access management:
- Users (public.users - referenced from identity schema)
- Roles
- Permissions
- Role Permissions (many-to-many)
- Stations (multi-location support)
- Station Users (many-to-many)
- Station Access Tokens
- Station Audit Logs
- Social Accounts (OAuth providers)

All models use:
- UUID primary keys
- Timezone-aware datetime fields
- Schema qualification (__table_args__)
- Proper foreign key relationships
- Type hints for IDE support
"""

from datetime import datetime
from typing import Optional, List
from uuid import UUID, uuid4

from sqlalchemy import (
    Column, String, Text, Integer, Boolean, DateTime,
    ForeignKey, Index, UniqueConstraint, Enum as SQLEnum
)
from sqlalchemy.dialects.postgresql import UUID as PGUUID, JSONB
from sqlalchemy.orm import relationship, Mapped, mapped_column
from sqlalchemy.sql import func

from ..base_class import Base


# ==================== ENUMS ====================

import enum

class RoleType(str, enum.Enum):
    """System role types"""
    SUPER_ADMIN = "super_admin"
    ADMIN = "admin"
    MANAGER = "manager"
    STAFF = "staff"
    CHEF = "chef"
    CUSTOMER = "customer"


class PermissionType(str, enum.Enum):
    """Permission types"""
    READ = "read"
    WRITE = "write"
    DELETE = "delete"
    EXECUTE = "execute"
    ADMIN = "admin"


class UserStatus(str, enum.Enum):
    """User account status"""
    ACTIVE = "active"
    INACTIVE = "inactive"
    SUSPENDED = "suspended"
    PENDING = "pending"


class AuthProvider(str, enum.Enum):
    """OAuth authentication providers"""
    GOOGLE = "google"
    FACEBOOK = "facebook"
    INSTAGRAM = "instagram"
    EMAIL = "email"


class AuditAction(str, enum.Enum):
    """Audit log action types"""
    LOGIN = "login"
    LOGOUT = "logout"
    CREATE = "create"
    UPDATE = "update"
    DELETE = "delete"
    VIEW = "view"
    EXPORT = "export"
    IMPORT = "import"
    PERMISSION_CHANGE = "permission_change"
    ROLE_CHANGE = "role_change"


# ==================== MODELS ====================

class User(Base):
    """
    User entity (in identity schema)

    Core user account with authentication and profile.
    Referenced by identity.stations and other schemas.
    """
    __tablename__ = "users"
    __table_args__ = (
        Index("idx_users_email", "email"),
        Index("idx_users_status", "status"),
        Index("idx_users_created_at", "created_at"),
        {"schema": "identity"}
    )

    # Primary Key
    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)

    # Authentication
    email: Mapped[str] = mapped_column(String(255), nullable=False, unique=True, index=True)
    password_hash: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    # Profile
    first_name: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    last_name: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    phone: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    avatar_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)

    # Status
    status: Mapped[UserStatus] = mapped_column(
        SQLEnum(UserStatus, name="userstatus", schema="public", create_type=False),
        nullable=False,
        default=UserStatus.ACTIVE,
        index=True
    )
    is_verified: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    # Metadata
    user_metadata: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)

    # Timestamps
    last_login_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
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
    user_roles: Mapped[List["UserRole"]] = relationship("UserRole", foreign_keys="[UserRole.user_id]", back_populates="user")
    oauth_accounts: Mapped[List["OAuthAccount"]] = relationship("OAuthAccount", back_populates="user")
    station_users: Mapped[List["StationUser"]] = relationship("StationUser", back_populates="user")


class Role(Base):
    """
    Role entity

    Defines user roles with permissions (RBAC).
    """
    __tablename__ = "roles"
    __table_args__ = (
        Index("idx_roles_name", "name"),
        Index("idx_roles_role_type", "role_type"),
        Index("idx_roles_active", "is_active"),
        {"schema": "identity"}
    )

    # Primary Key
    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)

    # Role Details
    name: Mapped[str] = mapped_column(String(100), nullable=False, unique=True, index=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    role_type: Mapped[RoleType] = mapped_column(
        SQLEnum(RoleType, name="roletype", schema="public", create_type=False),
        nullable=False,
        index=True
    )

    # Status
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True, index=True)
    is_system_role: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

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
    role_permissions: Mapped[List["RolePermission"]] = relationship("RolePermission", back_populates="role", cascade="all, delete-orphan")
    user_roles: Mapped[List["UserRole"]] = relationship("UserRole", back_populates="role", cascade="all, delete-orphan")


class Permission(Base):
    """
    Permission entity

    Defines granular permissions for RBAC.
    """
    __tablename__ = "permissions"
    __table_args__ = (
        Index("idx_permissions_resource_action", "resource", "action"),
        UniqueConstraint("resource", "action", name="uq_permissions_resource_action"),
        {"schema": "identity"}
    )

    # Primary Key
    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)

    # Permission Details
    resource: Mapped[str] = mapped_column(String(100), nullable=False)  # e.g., "bookings", "customers"
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
    role_permissions: Mapped[List["RolePermission"]] = relationship("RolePermission", back_populates="permission", cascade="all, delete-orphan")


class RolePermission(Base):
    """
    Role-Permission junction table

    Many-to-many relationship between roles and permissions.
    """
    __tablename__ = "role_permissions"
    __table_args__ = (
        Index("idx_role_permissions_role_id", "role_id"),
        Index("idx_role_permissions_permission_id", "permission_id"),
        UniqueConstraint("role_id", "permission_id", name="uq_role_permissions"),
        {"schema": "identity"}
    )

    # Primary Key
    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)

    # Foreign Keys
    role_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("identity.roles.id"), nullable=False)
    permission_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("identity.permissions.id"), nullable=False)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now()
    )

    # Relationships
    role: Mapped["Role"] = relationship("Role", back_populates="role_permissions")
    permission: Mapped["Permission"] = relationship("Permission", back_populates="role_permissions")


class UserRole(Base):
    """
    User-Role association table (many-to-many)

    Links users to roles for RBAC.
    Tracks who assigned the role and when.

    Business Rules:
    - user_id + role_id = composite primary key (one role assignment per user-role pair)
    - CASCADE delete (if user or role deleted, assignment removed)
    - assigned_by: Optional tracking (who granted this role)
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
    user: Mapped["User"] = relationship("User", foreign_keys=[user_id], back_populates="user_roles")
    role: Mapped["Role"] = relationship("Role", back_populates="user_roles")


class Station(Base):
    """
    Station entity

    Represents a physical location/station with multi-tenant support.
    """
    __tablename__ = "stations"
    __table_args__ = (
        Index("idx_stations_name", "name"),
        Index("idx_stations_active", "is_active"),
        {"schema": "identity"}
    )

    # Primary Key
    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)

    # Station Details
    name: Mapped[str] = mapped_column(String(100), nullable=False, unique=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Location
    address: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    city: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    state: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    zip_code: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)

    # Contact
    phone: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    email: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    # Status
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True, index=True)

    # Metadata
    station_metadata: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)

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
    station_users: Mapped[List["StationUser"]] = relationship("StationUser", back_populates="station", cascade="all, delete-orphan")
    access_tokens: Mapped[List["StationAccessToken"]] = relationship("StationAccessToken", back_populates="station", cascade="all, delete-orphan")
    audit_logs: Mapped[List["StationAuditLog"]] = relationship("StationAuditLog", back_populates="station", cascade="all, delete-orphan")


class StationUser(Base):
    """
    Station-User junction table

    Many-to-many relationship between stations and users.
    Allows users to access multiple stations.
    """
    __tablename__ = "station_users"
    __table_args__ = (
        Index("idx_station_users_station_id", "station_id"),
        Index("idx_station_users_user_id", "user_id"),
        UniqueConstraint("station_id", "user_id", name="uq_station_users"),
        {"schema": "identity"}
    )

    # Primary Key
    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)

    # Foreign Keys
    station_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("identity.stations.id"), nullable=False)
    user_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("identity.users.id"), nullable=False)

    # Access Details
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

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
    station: Mapped["Station"] = relationship("Station", back_populates="station_users")
    user: Mapped["User"] = relationship("User", back_populates="station_users")


class StationAccessToken(Base):
    """
    Station access token entity

    API tokens for station-level authentication.
    """
    __tablename__ = "station_access_tokens"
    __table_args__ = (
        Index("idx_station_access_tokens_station_id", "station_id"),
        Index("idx_station_access_tokens_token", "token"),
        Index("idx_station_access_tokens_active", "is_active"),
        {"schema": "identity"}
    )

    # Primary Key
    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)

    # Foreign Keys
    station_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("identity.stations.id"), nullable=False)

    # Token Details
    token: Mapped[str] = mapped_column(String(255), nullable=False, unique=True, index=True)
    name: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Expiration
    expires_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    # Status
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True, index=True)

    # Usage Tracking
    last_used_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    use_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

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
    station: Mapped["Station"] = relationship("Station", back_populates="access_tokens")


class StationAuditLog(Base):
    """
    Station audit log entity

    Tracks all actions performed at station level for compliance.
    """
    __tablename__ = "station_audit_logs"
    __table_args__ = (
        Index("idx_station_audit_logs_station_id", "station_id"),
        Index("idx_station_audit_logs_user_id", "user_id"),
        Index("idx_station_audit_logs_action", "action"),
        Index("idx_station_audit_logs_created_at", "created_at"),
        {"schema": "identity"}
    )

    # Primary Key
    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)

    # Foreign Keys
    station_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("identity.stations.id"), nullable=False)
    user_id: Mapped[Optional[UUID]] = mapped_column(PGUUID(as_uuid=True), ForeignKey("identity.users.id"), nullable=True)

    # Action Details
    action: Mapped[AuditAction] = mapped_column(
        SQLEnum(AuditAction, name="audit_action", schema="public", create_type=False),
        nullable=False,
        index=True
    )
    resource_type: Mapped[str] = mapped_column(String(100), nullable=False)  # e.g., "booking", "customer"
    resource_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    # Details
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    ip_address: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    user_agent: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)

    # Metadata
    audit_metadata: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)

    # Timestamp
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        index=True
    )

    # Relationships
    station: Mapped["Station"] = relationship("Station", back_populates="audit_logs")


class OAuthAccount(Base):
    """
    OAuth-linked social account for user authentication

    Stores OAuth tokens for third-party login (Google, Facebook, etc.).
    Different from lead.SocialAccount (business social media pages).
    """
    __tablename__ = "social_accounts"
    __table_args__ = (
        Index("idx_social_accounts_user_id", "user_id"),
        Index("idx_social_accounts_provider", "provider"),
        UniqueConstraint("provider", "provider_account_id", name="uq_social_accounts_provider"),
        {"schema": "identity"}
    )

    # Primary Key
    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)

    # Foreign Keys
    user_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("identity.users.id"), nullable=False)

    # Provider Details
    provider: Mapped[AuthProvider] = mapped_column(
        SQLEnum(AuthProvider, name="authprovider", schema="public", create_type=False),
        nullable=False,
        index=True
    )
    provider_account_id: Mapped[str] = mapped_column(String(255), nullable=False)

    # OAuth Tokens
    access_token: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    refresh_token: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    expires_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    # Profile Data
    profile_data: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)

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
    user: Mapped["User"] = relationship("User", back_populates="oauth_accounts")
