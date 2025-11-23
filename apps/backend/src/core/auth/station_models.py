"""
Multi-Tenant Station Models for RBAC System
Implements station-scoped authentication and authorization with proper isolation.
"""

from enum import Enum
from uuid import UUID, uuid4

# Import unified Base (avoid circular import)
from models.legacy_declarative_base import (
    Base,
)  # Phase 2C: Updated from api.app.models.declarative_base
from sqlalchemy import (
    JSON,
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy.dialects.postgresql import UUID as PostgresUUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func


class StationStatus(str, Enum):
    """Station operational status."""

    ACTIVE = "active"
    INACTIVE = "inactive"
    SUSPENDED = "suspended"
    MAINTENANCE = "maintenance"


class StationRole(str, Enum):
    """Station-specific user roles with hierarchical permissions."""

    SUPER_ADMIN = "super_admin"  # Global access across all stations
    ADMIN = "admin"  # Full access within specific stations
    STATION_ADMIN = "station_admin"  # Admin access within single station
    CUSTOMER_SUPPORT = "customer_support"  # Support access within station


class StationPermission(str, Enum):
    """Station-scoped permissions for granular access control."""

    # Station Management (Super Admin only)
    STATION_CREATE = "station.create"
    STATION_READ = "station.read"
    STATION_UPDATE = "station.update"
    STATION_DELETE = "station.delete"
    STATION_MANAGE_USERS = "station.manage_users"

    # Cross-Station Access (Admin+ only)
    CROSS_STATION_READ = "cross_station.read"
    CROSS_STATION_ANALYTICS = "cross_station.analytics"

    # Booking Management (Station Admin+)
    BOOKING_CREATE = "booking.create"
    BOOKING_READ = "booking.read"
    BOOKING_UPDATE = "booking.update"
    BOOKING_CANCEL = "booking.cancel"
    BOOKING_REPORTS = "booking.reports"

    # Customer Management (Station Admin+)
    CUSTOMER_CREATE = "customer.create"
    CUSTOMER_READ = "customer.read"
    CUSTOMER_UPDATE = "customer.update"
    CUSTOMER_DELETE = "customer.delete"
    CUSTOMER_EXPORT = "customer.export"

    # Payment Operations (Station Admin+)
    PAYMENT_RECORD = "payment.record"
    PAYMENT_READ = "payment.read"
    PAYMENT_REFUND = "payment.refund"
    PAYMENT_REPORTS = "payment.reports"

    # Communication (Customer Support+)
    MESSAGE_READ = "message.read"
    MESSAGE_SEND = "message.send"
    MESSAGE_DELETE = "message.delete"
    SMS_SEND = "sms.send"
    EMAIL_SEND = "email.send"

    # Lead Management (Customer Support+)
    LEAD_CREATE = "lead.create"
    LEAD_READ = "lead.read"
    LEAD_UPDATE = "lead.update"
    LEAD_CONVERT = "lead.convert"

    # AI Agent Access (Customer Support+)
    AI_CHAT = "ai.chat"
    AI_BOOKING_ASSIST = "ai.booking_assist"
    AI_ANALYTICS = "ai.analytics"

    # Reports & Analytics (varies by role)
    REPORTS_BASIC = "reports.basic"
    REPORTS_ADVANCED = "reports.advanced"
    REPORTS_EXPORT = "reports.export"

    # System & Audit (Admin+ only)
    AUDIT_READ = "audit.read"
    SYSTEM_CONFIG = "system.config"
    USER_MANAGE = "user.manage"


# Role-Permission Mapping with Station Context
STATION_ROLE_PERMISSIONS: dict[StationRole, set[StationPermission]] = {
    StationRole.SUPER_ADMIN: set(StationPermission),  # All permissions across all stations
    StationRole.ADMIN: {
        # Station management within assigned stations
        StationPermission.STATION_READ,
        StationPermission.STATION_UPDATE,
        StationPermission.STATION_MANAGE_USERS,
        StationPermission.CROSS_STATION_READ,
        StationPermission.CROSS_STATION_ANALYTICS,
        # Full CRM access within stations
        StationPermission.BOOKING_CREATE,
        StationPermission.BOOKING_READ,
        StationPermission.BOOKING_UPDATE,
        StationPermission.BOOKING_CANCEL,
        StationPermission.BOOKING_REPORTS,
        StationPermission.CUSTOMER_CREATE,
        StationPermission.CUSTOMER_READ,
        StationPermission.CUSTOMER_UPDATE,
        StationPermission.CUSTOMER_DELETE,
        StationPermission.CUSTOMER_EXPORT,
        StationPermission.PAYMENT_RECORD,
        StationPermission.PAYMENT_READ,
        StationPermission.PAYMENT_REFUND,
        StationPermission.PAYMENT_REPORTS,
        StationPermission.MESSAGE_READ,
        StationPermission.MESSAGE_SEND,
        StationPermission.MESSAGE_DELETE,
        StationPermission.SMS_SEND,
        StationPermission.EMAIL_SEND,
        StationPermission.LEAD_CREATE,
        StationPermission.LEAD_READ,
        StationPermission.LEAD_UPDATE,
        StationPermission.LEAD_CONVERT,
        StationPermission.AI_CHAT,
        StationPermission.AI_BOOKING_ASSIST,
        StationPermission.AI_ANALYTICS,
        StationPermission.REPORTS_BASIC,
        StationPermission.REPORTS_ADVANCED,
        StationPermission.REPORTS_EXPORT,
        StationPermission.AUDIT_READ,
        StationPermission.SYSTEM_CONFIG,
        StationPermission.USER_MANAGE,
    },
    StationRole.STATION_ADMIN: {
        # Station operations within single station
        StationPermission.STATION_READ,
        StationPermission.STATION_UPDATE,
        # Full CRM access within assigned station
        StationPermission.BOOKING_CREATE,
        StationPermission.BOOKING_READ,
        StationPermission.BOOKING_UPDATE,
        StationPermission.BOOKING_CANCEL,
        StationPermission.BOOKING_REPORTS,
        StationPermission.CUSTOMER_CREATE,
        StationPermission.CUSTOMER_READ,
        StationPermission.CUSTOMER_UPDATE,
        StationPermission.CUSTOMER_EXPORT,
        StationPermission.PAYMENT_RECORD,
        StationPermission.PAYMENT_READ,
        StationPermission.PAYMENT_REFUND,
        StationPermission.PAYMENT_REPORTS,
        StationPermission.MESSAGE_READ,
        StationPermission.MESSAGE_SEND,
        StationPermission.SMS_SEND,
        StationPermission.EMAIL_SEND,
        StationPermission.LEAD_CREATE,
        StationPermission.LEAD_READ,
        StationPermission.LEAD_UPDATE,
        StationPermission.LEAD_CONVERT,
        StationPermission.AI_CHAT,
        StationPermission.AI_BOOKING_ASSIST,
        StationPermission.AI_ANALYTICS,
        StationPermission.REPORTS_BASIC,
        StationPermission.REPORTS_ADVANCED,
        StationPermission.REPORTS_EXPORT,
        StationPermission.AUDIT_READ,
    },
    StationRole.CUSTOMER_SUPPORT: {
        # Customer service operations
        StationPermission.STATION_READ,
        StationPermission.BOOKING_READ,
        StationPermission.BOOKING_UPDATE,
        StationPermission.CUSTOMER_READ,
        StationPermission.CUSTOMER_UPDATE,
        StationPermission.PAYMENT_READ,
        StationPermission.MESSAGE_READ,
        StationPermission.MESSAGE_SEND,
        StationPermission.SMS_SEND,
        StationPermission.EMAIL_SEND,
        StationPermission.LEAD_CREATE,
        StationPermission.LEAD_READ,
        StationPermission.LEAD_UPDATE,
        StationPermission.AI_CHAT,
        StationPermission.AI_BOOKING_ASSIST,
        StationPermission.REPORTS_BASIC,
    },
}


class Station(Base):
    """Multi-tenant station model with comprehensive metadata."""

    __tablename__ = "stations"
    __table_args__ = {"schema": "identity"}

    id = Column(PostgresUUID(as_uuid=True), primary_key=True, default=uuid4)

    # Station identification
    name = Column(String(100), nullable=False)
    code = Column(String(20), nullable=False, unique=True)  # e.g., "NYC001", "LA001"
    display_name = Column(String(200), nullable=False)

    # Contact & Location
    email = Column(String(255), nullable=True)
    phone = Column(String(50), nullable=True)
    address = Column(Text, nullable=True)
    city = Column(String(100), nullable=True)
    state = Column(String(50), nullable=True)  # US State code (e.g., "NY", "CA")
    postal_code = Column(String(20), nullable=True)
    country = Column(
        String(100), nullable=True, default="US"
    )  # Optional, auto-detect from location
    timezone = Column(String(50), nullable=False, default="America/New_York")

    # Operational settings
    status = Column(String(20), nullable=False, default=StationStatus.ACTIVE.value)
    settings = Column(JSON, nullable=False, default=dict)  # Station-specific configuration

    # Business metadata
    business_hours = Column(JSON, nullable=True)  # Operating hours per day
    service_area_radius = Column(Integer, nullable=True)  # Service radius in miles
    max_concurrent_bookings = Column(Integer, nullable=False, default=10)
    booking_lead_time_hours = Column(Integer, nullable=False, default=24)

    # Branding & customization
    branding_config = Column(JSON, nullable=True)  # Logo, colors, custom text

    # Timestamps
    created_at = Column(DateTime(timezone=True), nullable=False, default=func.now())
    updated_at = Column(
        DateTime(timezone=True), nullable=False, default=func.now(), onupdate=func.now()
    )

    # Relationships
    station_users = relationship("UserStationAssignment", back_populates="station")
    # Note: Booking and Customer relationships are defined in their respective models
    # to avoid circular import issues. They will use back_populates="station"


class UserStationAssignment(Base):
    """Junction table for user-station assignments with role-based permissions."""

    __tablename__ = "user_station_assignments"
    __table_args__ = {"schema": "identity", "extend_existing": True}

    id = Column(PostgresUUID(as_uuid=True), primary_key=True, default=uuid4)

    # Relationships
    user_id = Column(
        PostgresUUID(as_uuid=True), ForeignKey("identity.users.id"), nullable=False, index=True
    )
    station_id = Column(
        PostgresUUID(as_uuid=True), ForeignKey("identity.stations.id"), nullable=False, index=True
    )

    # Role & permissions within this station
    role = Column(String(30), nullable=False, default=StationRole.CUSTOMER_SUPPORT.value)
    additional_permissions = Column(
        JSON, nullable=False, default=list
    )  # Extra permissions beyond role

    # Assignment metadata
    assigned_by = Column(PostgresUUID(as_uuid=True), ForeignKey("identity.users.id"), nullable=True)
    assigned_at = Column(DateTime(timezone=True), nullable=False, default=func.now())
    expires_at = Column(DateTime(timezone=True), nullable=True)  # Optional expiration

    # Status
    is_active = Column(Boolean, nullable=False, default=True)
    is_primary_station = Column(Boolean, nullable=False, default=False)  # User's default station

    # Timestamps
    created_at = Column(DateTime(timezone=True), nullable=False, default=func.now())
    updated_at = Column(
        DateTime(timezone=True), nullable=False, default=func.now(), onupdate=func.now()
    )

    # Relationships
    user = relationship("User", foreign_keys=[user_id])
    station = relationship("Station", back_populates="station_users")
    assigned_by_user = relationship("User", foreign_keys=[assigned_by])


class StationAuditLog(Base):
    """Station-scoped audit logging for compliance and security."""

    __tablename__ = "station_audit_logs"
    __table_args__ = {"schema": "identity"}

    id = Column(PostgresUUID(as_uuid=True), primary_key=True, default=uuid4)

    # Context
    station_id = Column(
        PostgresUUID(as_uuid=True), ForeignKey("identity.stations.id"), nullable=False, index=True
    )
    user_id = Column(
        PostgresUUID(as_uuid=True), ForeignKey("identity.users.id"), nullable=True, index=True
    )
    session_id = Column(
        PostgresUUID(as_uuid=True), ForeignKey("identity.user_sessions.id"), nullable=True
    )

    # Action details
    action = Column(String(50), nullable=False, index=True)  # STATION_ACCESS, BOOKING_CREATE, etc.
    resource_type = Column(String(50), nullable=True)  # booking, customer, payment, etc.
    resource_id = Column(String(50), nullable=True)  # ID of affected resource

    # Permission context
    user_role = Column(String(30), nullable=True)  # Role used for action
    permissions_used = Column(JSON, nullable=True)  # Specific permissions checked

    # Request context
    details = Column(JSON, nullable=False, default=dict)  # Action-specific details
    ip_address = Column(String(45), nullable=True)
    user_agent = Column(Text, nullable=True)

    # Result
    success = Column(Boolean, nullable=False)
    error_message = Column(Text, nullable=True)

    # Timestamp
    created_at = Column(DateTime(timezone=True), nullable=False, default=func.now())

    # Relationships
    station = relationship("Station")
    user = relationship("User")
    session = relationship("UserSession")


class StationAccessToken(Base):
    """Station-specific access tokens for enhanced security."""

    __tablename__ = "station_access_tokens"
    __table_args__ = {"schema": "identity"}

    id = Column(PostgresUUID(as_uuid=True), primary_key=True, default=uuid4)

    # Token context
    user_id = Column(
        PostgresUUID(as_uuid=True), ForeignKey("identity.users.id"), nullable=False, index=True
    )
    station_id = Column(
        PostgresUUID(as_uuid=True), ForeignKey("identity.stations.id"), nullable=False, index=True
    )
    session_id = Column(
        PostgresUUID(as_uuid=True), ForeignKey("identity.user_sessions.id"), nullable=False
    )

    # Token details
    token_hash = Column(String(100), nullable=False, unique=True)
    jwt_id = Column(String(36), nullable=False, unique=True)  # JWT jti claim

    # Permissions & scope
    role = Column(String(30), nullable=False)
    permissions = Column(JSON, nullable=False, default=list)
    scope = Column(String(500), nullable=True)  # Additional scope restrictions

    # Token lifecycle
    issued_at = Column(DateTime(timezone=True), nullable=False, default=func.now())
    expires_at = Column(DateTime(timezone=True), nullable=False)
    revoked_at = Column(DateTime(timezone=True), nullable=True)
    is_revoked = Column(Boolean, nullable=False, default=False)

    # Relationships
    user = relationship("User")
    station = relationship("Station")
    session = relationship("UserSession")


# Helper functions for permission management
def get_station_permissions(
    role: StationRole, additional_permissions: list[str] | None = None
) -> set[str]:
    """Get all permissions for a station role."""
    permissions = STATION_ROLE_PERMISSIONS.get(role, set())

    if additional_permissions:
        for perm in additional_permissions:
            try:
                permissions.add(StationPermission(perm))
            except ValueError:
                pass  # Invalid permission, skip

    return {p.value for p in permissions}


def can_access_station(
    user_role: StationRole, target_station_id: UUID, user_station_ids: list[UUID]
) -> bool:
    """Check if user can access target station based on role and assignments."""
    # Super admins can access any station
    if user_role == StationRole.SUPER_ADMIN:
        return True

    # Admins can access stations they're assigned to
    if user_role == StationRole.ADMIN:
        return target_station_id in user_station_ids

    # Station admins and customer support only access assigned stations
    return target_station_id in user_station_ids


def can_perform_cross_station_action(user_role: StationRole, permission: StationPermission) -> bool:
    """Check if user can perform cross-station actions."""
    user_permissions = STATION_ROLE_PERMISSIONS.get(user_role, set())

    # Check for specific cross-station permissions
    cross_station_permissions = {
        StationPermission.CROSS_STATION_READ,
        StationPermission.CROSS_STATION_ANALYTICS,
    }

    return permission in user_permissions and any(
        perm in user_permissions for perm in cross_station_permissions
    )


__all__ = [
    "STATION_ROLE_PERMISSIONS",
    "Station",
    "StationAccessToken",
    "StationAuditLog",
    "StationPermission",
    "StationRole",
    "StationStatus",
    "UserStationAssignment",
    "can_access_station",
    "can_perform_cross_station_action",
    "get_station_permissions",
]
