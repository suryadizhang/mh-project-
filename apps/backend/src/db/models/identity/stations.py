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
from datetime import datetime, timezone
from typing import List, Optional
from uuid import UUID, uuid4

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
    text,
)
from sqlalchemy import Enum as SQLEnum
from sqlalchemy import func
from sqlalchemy.dialects.postgresql import JSONB, JSON, UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from db.base_class import Base


# ==================== ENUMS ====================


class StationStatus(str, enum.Enum):
    """Station operational status."""

    ACTIVE = "active"
    INACTIVE = "inactive"
    SUSPENDED = "suspended"
    MAINTENANCE = "maintenance"


class StationRole(str, enum.Enum):
    """Station-specific user roles with hierarchical permissions."""

    SUPER_ADMIN = "super_admin"  # Global access across all stations
    ADMIN = "admin"  # Full access within specific stations
    STATION_ADMIN = "station_admin"  # Admin access within single station
    CUSTOMER_SUPPORT = "customer_support"  # Support access within station


class StationPermission(str, enum.Enum):
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

    ⚠️ SCHEMA UPDATED (Nov 2025): Now matches actual database schema
    - Added required fields: code, display_name, country, timezone, status
    - Renamed zip_code → postal_code
    - Added business fields: settings, max_concurrent_bookings, booking_lead_time_hours
    - Added optional fields: business_hours, service_area_radius, branding_config
    - Removed deprecated fields: description, is_active, station_metadata
    - Added check constraints for validation

    Business Requirements:
    - Multi-tenant architecture (each station independent)
    - Unique station code (for API/integration use)
    - Complete location and contact information
    - Status management (active/inactive/suspended/maintenance)
    - Business hours configuration
    - Booking capacity limits
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
    - Delete: super_admin only (status change to 'inactive')
    - View: super_admin, station admin, station users

    Station Lifecycle:
    - Created by super_admin
    - Assigned admin users (via StationUser)
    - Admin invites staff (via AdminInvitation)
    - Staff manages bookings and customers
    - Station can be deactivated (status='inactive')
    """

    __tablename__ = "stations"
    __table_args__ = (
        CheckConstraint("booking_lead_time_hours >= 0", name="station_lead_time_non_negative"),
        CheckConstraint("max_concurrent_bookings > 0", name="station_max_bookings_positive"),
        CheckConstraint(
            "status IN ('active', 'inactive', 'suspended', 'maintenance')",
            name="station_status_valid",
        ),
        UniqueConstraint("code", name="unique_station_code"),
        Index("idx_station_code", "code"),
        Index("idx_station_status", "status"),
        {"schema": "identity", "extend_existing": True},
    )

    # Primary Key
    id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid()
    )

    # Station Identity (REQUIRED FIELDS)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    code: Mapped[str] = mapped_column(
        String(20), nullable=False
    )  # NEW: Unique code for API/integration
    display_name: Mapped[str] = mapped_column(
        String(200), nullable=False
    )  # NEW: Public-facing name

    # Geographic and Contact (REQUIRED FIELDS)
    country: Mapped[str] = mapped_column(String(100), nullable=False, server_default=text("'US'"))
    timezone: Mapped[str] = mapped_column(
        String(50), nullable=False, server_default=text("'America/New_York'")
    )

    # Status (REQUIRED FIELD)
    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        server_default=text("'active'"),  # active, inactive, suspended, maintenance
    )

    # Business Configuration (REQUIRED FIELDS)
    settings: Mapped[dict] = mapped_column(JSON, nullable=False, server_default=text("'{}'"))
    max_concurrent_bookings: Mapped[int] = mapped_column(
        Integer, nullable=False, server_default=text("10")
    )
    booking_lead_time_hours: Mapped[int] = mapped_column(
        Integer, nullable=False, server_default=text("24")
    )

    # Contact (OPTIONAL FIELDS)
    email: Mapped[Optional[str]] = mapped_column(String(255))
    phone: Mapped[Optional[str]] = mapped_column(String(50))

    # Location (OPTIONAL FIELDS)
    address: Mapped[Optional[str]] = mapped_column(Text)
    city: Mapped[Optional[str]] = mapped_column(String(100))
    state: Mapped[Optional[str]] = mapped_column(String(50))
    postal_code: Mapped[Optional[str]] = mapped_column(String(20))  # RENAMED: was zip_code

    # Geocoding (for distance-based service area calculations)
    lat: Mapped[Optional[float]] = mapped_column(Numeric(10, 8), nullable=True)
    lng: Mapped[Optional[float]] = mapped_column(Numeric(11, 8), nullable=True)
    geocoded_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    geocode_status: Mapped[Optional[str]] = mapped_column(
        String(20), server_default=text("'pending'")
    )

    # Business Operations (OPTIONAL FIELDS)
    business_hours: Mapped[Optional[dict]] = mapped_column(JSON)  # NEW: Operating hours config
    service_area_radius: Mapped[Optional[int]] = mapped_column(
        Integer, server_default=text("150")
    )  # Service radius in miles (default 150)
    escalation_radius_miles: Mapped[Optional[int]] = mapped_column(
        Integer, server_default=text("150")
    )  # Miles beyond which bookings require human escalation
    branding_config: Mapped[Optional[dict]] = mapped_column(JSON)  # NEW: Custom branding settings

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    # Relationships
    station_users: Mapped[List["StationUser"]] = relationship(
        "StationUser", back_populates="station", cascade="all, delete-orphan"
    )
    access_tokens: Mapped[List["StationAccessToken"]] = relationship(
        "StationAccessToken", back_populates="station", cascade="all, delete-orphan"
    )
    audit_logs: Mapped[List["StationAuditLog"]] = relationship(
        "StationAuditLog", back_populates="station", cascade="all, delete-orphan"
    )

    # ==================== BACKWARD COMPATIBILITY ====================
    # Legacy code may reference is_active - map to status field
    @property
    def is_active(self) -> bool:
        """Backward compatibility for is_active checks"""
        return self.status == "active"

    @property
    def zip_code(self) -> Optional[str]:
        """Backward compatibility for zip_code access"""
        return self.postal_code

    @zip_code.setter
    def zip_code(self, value: Optional[str]):
        """Backward compatibility for zip_code setting"""
        self.postal_code = value

    def __repr__(self) -> str:
        return f"<Station(id={self.id}, name={self.name}, code={self.code}, status={self.status})>"

    # ==================== GEOCODING HELPERS ====================

    @property
    def is_geocoded(self) -> bool:
        """Check if station has been successfully geocoded."""
        return self.geocode_status == "success" and self.lat is not None and self.lng is not None

    @property
    def coordinates(self) -> tuple[float, float] | None:
        """Get lat/lng tuple if geocoded."""
        if self.lat is not None and self.lng is not None:
            return (float(self.lat), float(self.lng))
        return None

    @property
    def full_address(self) -> str:
        """Get full formatted address."""
        parts = []
        if self.address:
            parts.append(self.address)
        if self.city:
            parts.append(self.city)
        if self.state:
            parts.append(self.state)
        if self.postal_code:
            parts.append(self.postal_code)
        return ", ".join(parts) if parts else ""

    def distance_to_km(self, lat: float, lng: float) -> float | None:
        """
        Calculate distance from this station to given coordinates.
        Uses Haversine formula. Returns distance in kilometers.
        Returns None if station is not geocoded.
        """
        import math

        if not self.is_geocoded:
            return None

        R = 6371  # Earth radius in km

        lat1_rad = math.radians(float(self.lat))
        lat2_rad = math.radians(lat)
        dlat = math.radians(lat - float(self.lat))
        dlng = math.radians(lng - float(self.lng))

        a = (
            math.sin(dlat / 2) ** 2
            + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(dlng / 2) ** 2
        )
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

        return R * c

    def distance_to_miles(self, lat: float, lng: float) -> float | None:
        """Calculate distance in miles."""
        km = self.distance_to_km(lat, lng)
        return km * 0.621371 if km is not None else None

    def is_within_service_area(self, lat: float, lng: float) -> bool:
        """Check if coordinates are within this station's service area."""
        miles = self.distance_to_miles(lat, lng)
        if miles is None:
            return False
        radius = self.service_area_radius or 150
        return miles <= radius

    def requires_escalation(self, lat: float, lng: float) -> bool:
        """
        Check if distance requires human escalation.
        Returns True if distance > escalation_radius_miles (default 150).
        """
        miles = self.distance_to_miles(lat, lng)
        if miles is None:
            return True  # Unknown = escalate
        threshold = self.escalation_radius_miles or 150
        return miles > threshold


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
        {"schema": "identity"},
    )

    # Primary Key
    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)

    # Foreign Keys
    station_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("identity.stations.id"), nullable=False
    )
    user_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("identity.users.id"), nullable=False
    )

    # Access Details
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now()
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
        {"schema": "identity"},
    )

    # Primary Key
    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)

    # Foreign Keys
    station_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("identity.stations.id"), nullable=False
    )

    # Token Details
    token: Mapped[str] = mapped_column(
        String(255), nullable=False, unique=True, index=True
    )  # Stored hashed in production
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
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now()
    )

    # Relationships
    station: Mapped["Station"] = relationship("Station", back_populates="access_tokens")

    def __repr__(self) -> str:
        return f"<StationAccessToken(id={self.id}, station_id={self.station_id}, active={self.is_active})>"

    def is_valid(self) -> bool:
        """Check if token is valid (active and not expired)."""
        if not self.is_active:
            return False
        if self.expires_at and datetime.now(timezone.utc) > self.expires_at:
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
        {"schema": "identity"},
    )

    # Primary Key
    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)

    # Foreign Keys
    station_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("identity.stations.id"), nullable=False
    )
    user_id: Mapped[Optional[UUID]] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("identity.users.id"), nullable=True
    )  # NULL for system actions

    # Action Details
    action: Mapped[AuditAction] = mapped_column(
        SQLEnum(AuditAction, name="audit_action", schema="public", create_type=False),
        nullable=False,
        index=True,
    )
    resource_type: Mapped[str] = mapped_column(
        String(100), nullable=False
    )  # e.g., "booking", "customer", "user"
    resource_id: Mapped[Optional[str]] = mapped_column(
        String(255), nullable=True
    )  # Resource identifier (UUID, ID, etc.)

    # Details
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    ip_address: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    user_agent: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)

    # Metadata (additional context as JSON)
    audit_metadata: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)

    # Timestamp (immutable - no updated_at)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), index=True
    )

    # Relationships
    station: Mapped["Station"] = relationship("Station", back_populates="audit_logs")

    def __repr__(self) -> str:
        return f"<StationAuditLog(id={self.id}, action={self.action}, resource_type={self.resource_type})>"
