"""
Station Models - Identity Schema

This module contains station-related models for multi-tenant station management.

Business Requirements:
- Multi-tenant station support
- Station-user associations (many-to-many)
- Station API access tokens
- Comprehensive audit logging for compliance
- Station metadata for custom attributes
- Active/inactive status management

Models:
- Station: Physical location/station entity
- StationUser: Many-to-many junction (stations ↔ users)
- StationAccessToken: API tokens for station-level authentication
- StationAuditLog: Audit trail for station-level actions
- AuditAction: Audit action types enum
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
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy import Enum as SQLEnum
from sqlalchemy import func
from sqlalchemy.dialects.postgresql import JSONB, UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from db.base_class import Base


# ==================== ENUMS ====================

class AuditAction(str, enum.Enum):
    """
    Audit log action types.

    Business Rules:
    - LOGIN: User authentication event
    - LOGOUT: User logout event
    - CREATE: Resource creation
    - UPDATE: Resource modification
    - DELETE: Resource deletion
    - VIEW: Resource access (sensitive data)
    - EXPORT: Data export (for compliance)
    - IMPORT: Data import (bulk operations)
    - PERMISSION_CHANGE: Permission modification
    - ROLE_CHANGE: Role assignment change

    Compliance:
    - All actions logged for audit trail
    - Required for SOC2, HIPAA, GDPR compliance
    - Immutable logs (no updates/deletes)
    - Minimum 1-year retention
    """
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

class Station(Base):
    """
    Station entity.

    Represents a physical location/station with multi-tenant support.

    Business Requirements:
    - Multi-tenant architecture (each station independent)
    - Unique station name
    - Complete location and contact information
    - Active/inactive status management
    - Extensible metadata (JSONB)
    - User associations (via StationUser)
    - API access tokens (via StationAccessToken)
    - Audit logging (via StationAuditLog)

    Multi-Tenant Model:
    - Each station operates independently
    - Data isolation between stations
    - Station-specific users and permissions
    - Station-level booking and customer data
    - Cross-station reporting for super_admin only

    Access Control:
    - Creation: super_admin only
    - Update: super_admin, station admin
    - Delete: super_admin only (soft delete via is_active)
    - View: super_admin, station admin, station users

    Station Lifecycle:
    - Created by super_admin
    - Assigned admin users (via StationUser)
    - Admin invites staff (via AdminInvitation)
    - Staff manages bookings and customers
    - Station can be deactivated (is_active=False)
    """
    __tablename__ = "stations"
    __table_args__ = (
        Index("idx_stations_name", "name"),
        Index("idx_stations_active", "is_active"),
        {"schema": "identity"}
    )

    # Primary Key
    id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        primary_key=True,
        default=uuid4
    )

    # Station Details
    name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        unique=True
    )
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
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
        index=True
    )

    # Metadata (extensible JSON for custom fields)
    station_metadata: Mapped[dict] = mapped_column(
        JSONB,
        nullable=False,
        default=dict
    )

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
    station_users: Mapped[List["StationUser"]] = relationship(
        "StationUser",
        back_populates="station",
        cascade="all, delete-orphan"
    )
    access_tokens: Mapped[List["StationAccessToken"]] = relationship(
        "StationAccessToken",
        back_populates="station",
        cascade="all, delete-orphan"
    )
    audit_logs: Mapped[List["StationAuditLog"]] = relationship(
        "StationAuditLog",
        back_populates="station",
        cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<Station(id={self.id}, name={self.name}, active={self.is_active})>"


class StationUser(Base):
    """
    Station-User junction table.

    Many-to-many relationship between stations and users.
    Allows users to access multiple stations.

    Business Requirements:
    - Users can belong to multiple stations
    - Stations can have multiple users
    - Unique (station_id, user_id) pair
    - Active/inactive status per station
    - Track assignment date

    Use Cases:
    - Multi-station staff: User works at multiple locations
    - Station transfer: User moves from one station to another
    - Temporary access: Seasonal or contract workers
    - Access revocation: Disable user at specific station

    Access Control:
    - Creation: super_admin, station admin (for their station)
    - Update: super_admin, station admin (is_active toggle)
    - Delete: super_admin, station admin
    - View: super_admin, station admin, station users

    Business Logic:
    - User roles apply per-station (via UserRole)
    - User can be admin at one station, staff at another
    - Deactivating station_user blocks station access
    - Deleting station_user removes all station access
    """
    __tablename__ = "station_users"
    __table_args__ = (
        Index("idx_station_users_station_id", "station_id"),
        Index("idx_station_users_user_id", "user_id"),
        UniqueConstraint("station_id", "user_id", name="uq_station_users"),
        {"schema": "identity"}
    )

    # Primary Key
    id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        primary_key=True,
        default=uuid4
    )

    # Foreign Keys
    station_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("identity.stations.id"),
        nullable=False
    )
    user_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("identity.users.id"),
        nullable=False
    )

    # Access Details
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True
    )

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

    def __repr__(self) -> str:
        return f"<StationUser(station_id={self.station_id}, user_id={self.user_id}, active={self.is_active})>"


class StationAccessToken(Base):
    """
    Station access token entity.

    API tokens for station-level authentication.

    Business Requirements:
    - Station-specific API access
    - Token-based authentication (alternative to OAuth)
    - Optional expiration date
    - Usage tracking (last_used_at, use_count)
    - Active/inactive status management
    - Token revocation support

    Use Cases:
    - API integrations (POS systems, booking widgets)
    - Automation scripts (report generation, data sync)
    - Third-party services (payment gateways, SMS providers)
    - Mobile apps (station-specific features)

    Security:
    - Tokens are long random strings (cryptographically secure)
    - Tokens stored hashed in production (use bcrypt/argon2)
    - Expiration date enforced
    - Can be revoked (is_active=False)
    - Usage tracked for audit

    Access Control:
    - Creation: super_admin, station admin
    - Update: super_admin, station admin (name, description, expiration)
    - Delete: super_admin, station admin
    - Revoke: super_admin, station admin (set is_active=False)
    - View: super_admin, station admin

    Token Lifecycle:
    - Created by admin with optional name/description
    - Used for API authentication (check station_id in token)
    - last_used_at and use_count updated on each use
    - Expired tokens rejected (if expires_at < now)
    - Revoked tokens rejected (if is_active=False)
    """
    __tablename__ = "station_access_tokens"
    __table_args__ = (
        Index("idx_station_access_tokens_station_id", "station_id"),
        Index("idx_station_access_tokens_token", "token"),
        Index("idx_station_access_tokens_active", "is_active"),
        {"schema": "identity"}
    )

    # Primary Key
    id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        primary_key=True,
        default=uuid4
    )

    # Foreign Keys
    station_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("identity.stations.id"),
        nullable=False
    )

    # Token Details
    token: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        unique=True,
        index=True
    )  # Stored hashed in production
    name: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Expiration
    expires_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True
    )

    # Status
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
        index=True
    )

    # Usage Tracking
    last_used_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True
    )
    use_count: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0
    )

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

    def __repr__(self) -> str:
        return f"<StationAccessToken(id={self.id}, station_id={self.station_id}, active={self.is_active})>"

    def is_valid(self) -> bool:
        """Check if token is valid (active and not expired)."""
        if not self.is_active:
            return False
        if self.expires_at and datetime.now() > self.expires_at:
            return False
        return True


class StationAuditLog(Base):
    """
    Station audit log entity.

    Tracks all actions performed at station level for compliance.

    Business Requirements:
    - Comprehensive audit trail for compliance
    - Track all station-level actions
    - Immutable logs (no updates/deletes)
    - Store user, action, resource details
    - Track IP address and user agent for security
    - Minimum 1-year retention

    Compliance:
    - Required for SOC2, HIPAA, GDPR
    - Audit logs cannot be modified or deleted
    - Must include: who, what, when, where
    - Retention: minimum 1 year, configurable per compliance needs

    Logged Actions:
    - User authentication (LOGIN, LOGOUT)
    - Data access (VIEW sensitive resources)
    - Data modification (CREATE, UPDATE, DELETE)
    - Administrative actions (PERMISSION_CHANGE, ROLE_CHANGE)
    - Data export/import (EXPORT, IMPORT)

    Access Control:
    - Creation: System (automatic via application code)
    - Update: NEVER (immutable)
    - Delete: NEVER (compliance requirement)
    - View: super_admin, station admin, auditor role

    Security:
    - Log ALL administrative actions
    - Store IP address for security investigation
    - Store user agent for device tracking
    - Metadata (JSONB) for additional context
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
    id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        primary_key=True,
        default=uuid4
    )

    # Foreign Keys
    station_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("identity.stations.id"),
        nullable=False
    )
    user_id: Mapped[Optional[UUID]] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("identity.users.id"),
        nullable=True
    )  # NULL for system actions

    # Action Details
    action: Mapped[AuditAction] = mapped_column(
        SQLEnum(AuditAction, name="audit_action", schema="public", create_type=False),
        nullable=False,
        index=True
    )
    resource_type: Mapped[str] = mapped_column(
        String(100),
        nullable=False
    )  # e.g., "booking", "customer", "user"
    resource_id: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True
    )  # Resource identifier (UUID, ID, etc.)

    # Details
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    ip_address: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    user_agent: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)

    # Metadata (additional context as JSON)
    audit_metadata: Mapped[dict] = mapped_column(
        JSONB,
        nullable=False,
        default=dict
    )

    # Timestamp (immutable - no updated_at)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        index=True
    )

    # Relationships
    station: Mapped["Station"] = relationship("Station", back_populates="audit_logs")

    def __repr__(self) -> str:
        return f"<StationAuditLog(id={self.id}, action={self.action}, resource_type={self.resource_type})>"
