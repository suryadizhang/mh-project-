"""
Role and Permission Models
Defines user roles and permissions for RBAC (Role-Based Access Control)
"""

from datetime import datetime
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

    # Review Management
    REVIEW_READ = "review:read"
    REVIEW_MODERATE = "review:moderate"
    REVIEW_RESPOND = "review:respond"

    # Analytics
    ANALYTICS_VIEW = "analytics:view"
    ANALYTICS_EXPORT = "analytics:export"

    # System Settings
    SETTINGS_READ = "settings:read"
    SETTINGS_UPDATE = "settings:update"


# Association table for many-to-many relationship between roles and permissions
role_permissions = Table(
    "role_permissions",
    Base.metadata,
    Column(
        "role_id",
        UUID(as_uuid=True),
        ForeignKey("identity.roles.id", ondelete="CASCADE"),
        primary_key=True,
    ),
    Column(
        "permission_id",
        UUID(as_uuid=True),
        ForeignKey("identity.permissions.id", ondelete="CASCADE"),
        primary_key=True,
    ),
    Column("created_at", DateTime(timezone=True), default=datetime.utcnow),
    schema="identity",
)


# Association table for many-to-many relationship between users and roles
user_roles = Table(
    "user_roles",
    Base.metadata,
    Column(
        "user_id",
        UUID(as_uuid=True),
        ForeignKey("identity.users.id", ondelete="CASCADE"),
        primary_key=True,
    ),
    Column(
        "role_id",
        UUID(as_uuid=True),
        ForeignKey("identity.roles.id", ondelete="CASCADE"),
        primary_key=True,
    ),
    Column("assigned_at", DateTime(timezone=True), default=datetime.utcnow),
    Column(
        "assigned_by",
        UUID(as_uuid=True),
        ForeignKey("identity.users.id", ondelete="SET NULL"),
        nullable=True,
    ),
    schema="identity",
)


class Role(Base):
    """Role model for RBAC"""

    __tablename__ = "roles"
    __table_args__ = {"schema": "identity"}

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
        DateTime(timezone=True), default=datetime.utcnow, nullable=False, index=True
    )
    updated_at = Column(
        DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )
    created_by = Column(
        UUID(as_uuid=True), ForeignKey("identity.users.id", ondelete="SET NULL"), nullable=True
    )

    # Additional settings
    settings = Column(JSONB, default={}, nullable=False)

    # Relationships
    permissions = relationship(
        "Permission", secondary=role_permissions, back_populates="roles", lazy="selectin"
    )
    users = relationship("User", secondary=user_roles, back_populates="roles", lazy="selectin")

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
    __table_args__ = {"schema": "identity"}

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
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)

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
        "description": "Full system access with all permissions",
        "permissions": list(PermissionType),  # All permissions
        "is_system_role": True,
    },
    RoleType.ADMIN: {
        "display_name": "Administrator",
        "description": "Administrative access to manage users, bookings, and settings",
        "permissions": [
            PermissionType.USER_READ,
            PermissionType.USER_UPDATE,
            PermissionType.STATION_CREATE,
            PermissionType.STATION_READ,
            PermissionType.STATION_UPDATE,
            PermissionType.BOOKING_CREATE,
            PermissionType.BOOKING_READ,
            PermissionType.BOOKING_UPDATE,
            PermissionType.BOOKING_CANCEL,
            PermissionType.CUSTOMER_CREATE,
            PermissionType.CUSTOMER_READ,
            PermissionType.CUSTOMER_UPDATE,
            PermissionType.PAYMENT_READ,
            PermissionType.REVIEW_READ,
            PermissionType.REVIEW_MODERATE,
            PermissionType.REVIEW_RESPOND,
            PermissionType.ANALYTICS_VIEW,
            PermissionType.SETTINGS_READ,
        ],
        "is_system_role": True,
    },
    RoleType.MANAGER: {
        "display_name": "Manager",
        "description": "Manage bookings, customers, and view analytics",
        "permissions": [
            PermissionType.STATION_READ,
            PermissionType.BOOKING_CREATE,
            PermissionType.BOOKING_READ,
            PermissionType.BOOKING_UPDATE,
            PermissionType.BOOKING_CANCEL,
            PermissionType.CUSTOMER_CREATE,
            PermissionType.CUSTOMER_READ,
            PermissionType.CUSTOMER_UPDATE,
            PermissionType.PAYMENT_READ,
            PermissionType.REVIEW_READ,
            PermissionType.REVIEW_RESPOND,
            PermissionType.ANALYTICS_VIEW,
        ],
        "is_system_role": True,
    },
    RoleType.STAFF: {
        "display_name": "Staff",
        "description": "Basic access to bookings and customers",
        "permissions": [
            PermissionType.STATION_READ,
            PermissionType.BOOKING_READ,
            PermissionType.BOOKING_UPDATE,
            PermissionType.CUSTOMER_READ,
            PermissionType.CUSTOMER_UPDATE,
            PermissionType.REVIEW_READ,
        ],
        "is_system_role": True,
    },
    RoleType.VIEWER: {
        "display_name": "Viewer",
        "description": "Read-only access to bookings and customers",
        "permissions": [
            PermissionType.STATION_READ,
            PermissionType.BOOKING_READ,
            PermissionType.CUSTOMER_READ,
            PermissionType.REVIEW_READ,
        ],
        "is_system_role": True,
    },
}
