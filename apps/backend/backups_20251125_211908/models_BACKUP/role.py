"""
Role and Permission Models
Defines user roles and permissions for RBAC (Role-Based Access Control)
"""

from datetime import datetime, timezone
from enum import Enum
import uuid

from models.base import Base
from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    String,
    Table,
    Text,
)
from sqlalchemy import Enum as SQLEnum
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import relationship


class RoleType(str, Enum):
    """Predefined role types"""

    SUPER_ADMIN = "super_admin"
    ADMIN = "admin"
    MANAGER = "manager"
    STAFF = "staff"
    VIEWER = "viewer"


class PermissionType(str, Enum):
    """Permission types for granular access control"""

    # User Management
    USER_CREATE = "user:create"
    USER_READ = "user:read"
    USER_UPDATE = "user:update"
    USER_DELETE = "user:delete"
    USER_APPROVE = "user:approve"

    # Station Management
    STATION_CREATE = "station:create"
    STATION_READ = "station:read"
    STATION_UPDATE = "station:update"
    STATION_DELETE = "station:delete"
    STATION_ASSIGN = "station:assign"

    # Booking Management
    BOOKING_CREATE = "booking:create"
    BOOKING_READ = "booking:read"
    BOOKING_UPDATE = "booking:update"
    BOOKING_DELETE = "booking:delete"
    BOOKING_CANCEL = "booking:cancel"

    # Customer Management
    CUSTOMER_CREATE = "customer:create"
    CUSTOMER_READ = "customer:read"
    CUSTOMER_UPDATE = "customer:update"
    CUSTOMER_DELETE = "customer:delete"

    # Payment Management
    PAYMENT_CREATE = "payment:create"
    PAYMENT_READ = "payment:read"
    PAYMENT_REFUND = "payment:refund"
    PAYMENT_VOID = "payment:void"

    # Review Management
    REVIEW_READ = "review:read"
    REVIEW_MODERATE = "review:moderate"
    REVIEW_RESPOND = "review:respond"

    # Analytics
    ANALYTICS_VIEW = "analytics:view"
    ANALYTICS_EXPORT = "analytics:export"
    ANALYTICS_FORECAST = "analytics:forecast"

    # System Settings
    SETTINGS_READ = "settings:read"
    SETTINGS_UPDATE = "settings:update"
    SETTINGS_SYSTEM = "settings:system"  # Critical system configurations

    # Newsletter & Campaign Management
    NEWSLETTER_CREATE = "newsletter:create"
    NEWSLETTER_READ = "newsletter:read"
    NEWSLETTER_UPDATE = "newsletter:update"
    NEWSLETTER_DELETE = "newsletter:delete"
    NEWSLETTER_SEND = "newsletter:send"
    CAMPAIGN_CREATE = "campaign:create"
    CAMPAIGN_READ = "campaign:read"
    CAMPAIGN_UPDATE = "campaign:update"
    CAMPAIGN_DELETE = "campaign:delete"

    # SMS Management
    SMS_SEND = "sms:send"
    SMS_READ = "sms:read"
    SMS_CAMPAIGN_CREATE = "sms:campaign:create"
    SMS_CAMPAIGN_SEND = "sms:campaign:send"

    # AI Controls
    AI_CONFIG_READ = "ai:config:read"
    AI_CONFIG_UPDATE = "ai:config:update"
    AI_FAQ_MANAGE = "ai:faq:manage"
    AI_LEARNING_VIEW = "ai:learning:view"
    AI_LEARNING_TRAIN = "ai:learning:train"

    # Inbox & Escalation (Customer Support)
    INBOX_READ = "inbox:read"
    INBOX_REPLY = "inbox:reply"
    INBOX_ASSIGN = "inbox:assign"
    ESCALATION_CREATE = "escalation:create"
    ESCALATION_READ = "escalation:read"
    ESCALATION_HANDLE = "escalation:handle"
    ESCALATION_RESOLVE = "escalation:resolve"

    # Call Recording
    RECORDING_READ = "recording:read"
    RECORDING_DOWNLOAD = "recording:download"
    RECORDING_DELETE = "recording:delete"


# Association table for many-to-many relationship between roles and permissions
role_permissions = Table(
    "role_permissions",
    Base.metadata,
    Column(
        "role_id",
        UUID(as_uuid=True),
        ForeignKey("roles.id", ondelete="CASCADE"),  # Removed identity schema
        primary_key=True,
    ),
    Column(
        "permission_id",
        UUID(as_uuid=True),
        ForeignKey("permissions.id", ondelete="CASCADE"),  # Removed identity schema
        primary_key=True,
    ),
    Column("created_at", DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)),
    # Removed identity schema - doesn't exist
)


# Association table for many-to-many relationship between users and roles
# DISABLED - no User model exists in our system
# user_roles = Table(
#     "user_roles",
#     Base.metadata,
#     Column(
#         "user_id",
#         UUID(as_uuid=True),
#         ForeignKey("identity.users.id", ondelete="CASCADE"),
#         primary_key=True,
#     ),
#     Column(
#         "role_id",
#         UUID(as_uuid=True),
#         ForeignKey("identity.roles.id", ondelete="CASCADE"),
#         primary_key=True,
#     ),
#     Column("assigned_at", DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)),
#     Column(
#         "assigned_by",
#         UUID(as_uuid=True),
#         ForeignKey("identity.users.id", ondelete="SET NULL"),
#         nullable=True,
#     ),
#     schema="identity",
# )


class Role(Base):
    """Role model for RBAC"""

    __tablename__ = "roles"
    __table_args__ = {"extend_existing": True}  # Removed identity schema - doesn't exist

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(
        SQLEnum(RoleType, values_callable=lambda x: [e.value for e in x]),
        unique=True,
        nullable=False,
        index=True,
    )
    display_name = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    is_system_role = Column(Boolean, default=False, nullable=False)  # Cannot be deleted
    is_active = Column(Boolean, default=True, nullable=False)

    # Metadata
    created_at = Column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False, index=True
    )
    updated_at = Column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False
    )
    # created_by removed - no User model exists
    # created_by = Column(
    #     UUID(as_uuid=True), ForeignKey("identity.users.id", ondelete="SET NULL"), nullable=True
    # )

    # Additional settings
    settings = Column(JSONB, default={}, nullable=False)

    # Relationships
    permissions = relationship(
        "Permission", secondary=role_permissions, back_populates="roles", lazy="selectin"
    )
    # users removed - no User model exists
    # users = relationship(
    #     "User",
    #     secondary=user_roles,
    #     lazy="selectin"
    # )

    def __repr__(self):
        return f"<Role {self.name}: {self.display_name}>"

    def to_dict(self):
        return {
            "id": str(self.id),
            "name": self.name,
            "display_name": self.display_name,
            "description": self.description,
            "is_system_role": self.is_system_role,
            "is_active": self.is_active,
            "permissions": [p.to_dict() for p in self.permissions],
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class Permission(Base):
    """Permission model for granular access control"""

    __tablename__ = "permissions"
    __table_args__ = {"extend_existing": True}  # Removed identity schema - doesn't exist

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(
        SQLEnum(PermissionType, values_callable=lambda x: [e.value for e in x]),
        unique=True,
        nullable=False,
        index=True,
    )
    display_name = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    resource = Column(String(50), nullable=False, index=True)  # user, booking, payment, etc.
    action = Column(String(50), nullable=False, index=True)  # create, read, update, delete

    # Metadata
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)

    # Relationships
    roles = relationship("Role", secondary=role_permissions, back_populates="permissions")

    def __repr__(self):
        return f"<Permission {self.name}>"

    def to_dict(self):
        return {
            "id": str(self.id),
            "name": self.name,
            "display_name": self.display_name,
            "description": self.description,
            "resource": self.resource,
            "action": self.action,
        }


# Default role configurations
DEFAULT_ROLES = {
    RoleType.SUPER_ADMIN: {
        "display_name": "Super Administrator",
        "description": "Full system access with all permissions including system-critical changes",
        "permissions": list(PermissionType),  # All permissions
        "is_system_role": True,
    },
    RoleType.ADMIN: {
        "display_name": "Administrator",
        "description": "Administrative access to manage operations but cannot change system-critical settings",
        "permissions": [
            # User Management (cannot approve or delete users)
            PermissionType.USER_READ,
            PermissionType.USER_UPDATE,
            # Station Management
            PermissionType.STATION_CREATE,
            PermissionType.STATION_READ,
            PermissionType.STATION_UPDATE,
            PermissionType.STATION_DELETE,
            PermissionType.STATION_ASSIGN,
            # Booking Management
            PermissionType.BOOKING_CREATE,
            PermissionType.BOOKING_READ,
            PermissionType.BOOKING_UPDATE,
            PermissionType.BOOKING_CANCEL,
            # Customer Management
            PermissionType.CUSTOMER_CREATE,
            PermissionType.CUSTOMER_READ,
            PermissionType.CUSTOMER_UPDATE,
            # Payment Management (can read and create, but refunds need approval)
            PermissionType.PAYMENT_READ,
            PermissionType.PAYMENT_CREATE,
            PermissionType.PAYMENT_REFUND,
            # Review Management
            PermissionType.REVIEW_READ,
            PermissionType.REVIEW_MODERATE,
            PermissionType.REVIEW_RESPOND,
            # Analytics (full access except system forecasting)
            PermissionType.ANALYTICS_VIEW,
            PermissionType.ANALYTICS_EXPORT,
            # Settings (read-only, no system changes)
            PermissionType.SETTINGS_READ,
            # Newsletter & Campaigns
            PermissionType.NEWSLETTER_CREATE,
            PermissionType.NEWSLETTER_READ,
            PermissionType.NEWSLETTER_UPDATE,
            PermissionType.NEWSLETTER_DELETE,
            PermissionType.NEWSLETTER_SEND,
            PermissionType.CAMPAIGN_CREATE,
            PermissionType.CAMPAIGN_READ,
            PermissionType.CAMPAIGN_UPDATE,
            PermissionType.CAMPAIGN_DELETE,
            # SMS
            PermissionType.SMS_SEND,
            PermissionType.SMS_READ,
            PermissionType.SMS_CAMPAIGN_CREATE,
            PermissionType.SMS_CAMPAIGN_SEND,
            # AI Controls (read-only)
            PermissionType.AI_CONFIG_READ,
            PermissionType.AI_FAQ_MANAGE,
            PermissionType.AI_LEARNING_VIEW,
            # Inbox (full access)
            PermissionType.INBOX_READ,
            PermissionType.INBOX_REPLY,
            PermissionType.INBOX_ASSIGN,
            PermissionType.ESCALATION_READ,
            PermissionType.ESCALATION_HANDLE,
            PermissionType.ESCALATION_RESOLVE,
            # Recordings
            PermissionType.RECORDING_READ,
            PermissionType.RECORDING_DOWNLOAD,
        ],
        "is_system_role": True,
    },
    RoleType.MANAGER: {
        "display_name": "Station Manager",
        "description": "Operational station management - cannot interfere with customer support functions",
        "permissions": [
            # Station Management (full access)
            PermissionType.STATION_READ,
            PermissionType.STATION_UPDATE,
            PermissionType.STATION_ASSIGN,
            # Booking Management (operational focus)
            PermissionType.BOOKING_CREATE,
            PermissionType.BOOKING_READ,
            PermissionType.BOOKING_UPDATE,
            PermissionType.BOOKING_CANCEL,
            # Customer (read-only)
            PermissionType.CUSTOMER_READ,
            # Payment (read-only)
            PermissionType.PAYMENT_READ,
            # Review (read and respond)
            PermissionType.REVIEW_READ,
            PermissionType.REVIEW_RESPOND,
            # Analytics (view only, no export)
            PermissionType.ANALYTICS_VIEW,
            # Settings (read-only)
            PermissionType.SETTINGS_READ,
            # NO customer support permissions (inbox, escalation)
            # NO campaign/newsletter permissions
            # NO AI control permissions
        ],
        "is_system_role": True,
    },
    RoleType.STAFF: {
        "display_name": "Customer Support",
        "description": "Customer support specialist - handle all customer-related tasks with proper logging",
        "permissions": [
            # Customer Management (full CRUD with logging)
            PermissionType.CUSTOMER_CREATE,
            PermissionType.CUSTOMER_READ,
            PermissionType.CUSTOMER_UPDATE,
            PermissionType.CUSTOMER_DELETE,  # With confirmation prompts
            # Booking Management
            PermissionType.BOOKING_CREATE,
            PermissionType.BOOKING_READ,
            PermissionType.BOOKING_UPDATE,
            PermissionType.BOOKING_CANCEL,  # With confirmation
            # Payment (read and basic operations)
            PermissionType.PAYMENT_READ,
            PermissionType.PAYMENT_CREATE,
            # Review Management
            PermissionType.REVIEW_READ,
            PermissionType.REVIEW_RESPOND,
            # Inbox & Escalation (core function)
            PermissionType.INBOX_READ,
            PermissionType.INBOX_REPLY,
            PermissionType.INBOX_ASSIGN,
            PermissionType.ESCALATION_CREATE,
            PermissionType.ESCALATION_READ,
            PermissionType.ESCALATION_HANDLE,
            PermissionType.ESCALATION_RESOLVE,
            # Recordings (read/playback for support)
            PermissionType.RECORDING_READ,
            # SMS (send individual messages)
            PermissionType.SMS_SEND,
            PermissionType.SMS_READ,
            # Limited analytics
            PermissionType.ANALYTICS_VIEW,
            # NO station management
            # NO campaign management
            # NO system settings
            # NO AI configuration
        ],
        "is_system_role": True,
    },
    RoleType.VIEWER: {
        "display_name": "Viewer",
        "description": "Read-only access to bookings, customers, and basic reports",
        "permissions": [
            PermissionType.STATION_READ,
            PermissionType.BOOKING_READ,
            PermissionType.CUSTOMER_READ,
            PermissionType.REVIEW_READ,
            PermissionType.PAYMENT_READ,
            PermissionType.ANALYTICS_VIEW,
            PermissionType.INBOX_READ,
            PermissionType.SETTINGS_READ,
        ],
        "is_system_role": True,
    },
}
