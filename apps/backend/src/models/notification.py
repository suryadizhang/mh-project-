"""
Admin Notification Group Management System

Database models for managing notification groups and memberships.

Features:
- Create custom notification groups
- Add/remove team members
- Configure which events each group receives
- Station-based filtering (station managers only get their station's notifications)
- Role-based access (customer service gets all, station managers get filtered)

Tables:
1. notification_groups - Group definitions
2. notification_group_members - Group memberships
3. notification_group_events - Event subscriptions per group
"""

from datetime import datetime, timezone
import enum
import uuid

from models.base import Base
from sqlalchemy import Boolean, Column, DateTime, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID as PostgresUUID
from sqlalchemy.orm import relationship


class NotificationEventType(str, enum.Enum):
    """Types of notification events"""

    NEW_BOOKING = "new_booking"
    BOOKING_EDIT = "booking_edit"
    BOOKING_CANCELLATION = "booking_cancellation"
    PAYMENT_RECEIVED = "payment_received"
    REVIEW_RECEIVED = "review_received"
    COMPLAINT_RECEIVED = "complaint_received"
    ALL = "all"  # Special: receives all event types


class NotificationGroup(Base):
    """
    Notification groups for organizing team members.

    Examples:
    - "All Admins" - Receives all notifications
    - "Customer Service Team" - Receives all notifications
    - "Station CA-BAY-001 Managers" - Only receives notifications for their station
    - "Booking Team" - Only receives booking-related notifications
    - "Payment Team" - Only receives payment notifications
    """

    __tablename__ = "notification_groups"

    id = Column(PostgresUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Group Information
    name = Column(String(100), nullable=False, unique=True, index=True)
    description = Column(Text, nullable=True)

    # Station Filtering (NULL = all stations, specific UUID = only that station)
    station_id = Column(PostgresUUID(as_uuid=True), nullable=True, index=True)

    # WhatsApp Configuration
    whatsapp_group_id = Column(String(100), nullable=True)  # Future: WhatsApp group ID

    # Status
    is_active = Column(Boolean, default=True, nullable=False)

    # Metadata
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)
    created_by = Column(PostgresUUID(as_uuid=True), nullable=False)  # User who created group

    # Relationships
    members = relationship(
        "NotificationGroupMember", back_populates="group", cascade="all, delete-orphan"
    )
    event_subscriptions = relationship(
        "NotificationGroupEvent", back_populates="group", cascade="all, delete-orphan"
    )

    def __repr__(self):
        station_info = f" (Station {self.station_id})" if self.station_id else " (All Stations)"
        return f"<NotificationGroup {self.name}{station_info}>"


class NotificationGroupMember(Base):
    """
    Members of notification groups.

    Each member receives notifications for events the group is subscribed to,
    filtered by station if applicable.
    """

    __tablename__ = "notification_group_members"

    id = Column(PostgresUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Group Relationship
    group_id = Column(
        PostgresUUID(as_uuid=True),
        ForeignKey("notification_groups.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Member Information
    phone_number = Column(String(20), nullable=False, index=True)  # WhatsApp phone number
    name = Column(String(100), nullable=False)
    email = Column(String(255), nullable=True)

    # Notification Preferences
    receive_whatsapp = Column(Boolean, default=True, nullable=False)
    receive_sms = Column(Boolean, default=False, nullable=False)
    receive_email = Column(Boolean, default=False, nullable=False)

    # Priority level (low, medium, high)
    priority = Column(String(20), default="medium", nullable=False)

    # Status
    is_active = Column(Boolean, default=True, nullable=False)

    # Metadata
    added_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    added_by = Column(PostgresUUID(as_uuid=True), nullable=True)  # User who added member

    # Relationships
    group = relationship("NotificationGroup", back_populates="members")

    def __repr__(self):
        return f"<NotificationGroupMember {self.name} ({self.phone_number}) in {self.group.name}>"


class NotificationGroupEvent(Base):
    """
    Event subscriptions for notification groups.

    Defines which notification events each group should receive.
    """

    __tablename__ = "notification_group_events"

    id = Column(PostgresUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Group Relationship
    group_id = Column(
        PostgresUUID(as_uuid=True),
        ForeignKey("notification_groups.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Event Configuration
    event_type = Column(String(50), nullable=False, index=True)

    # Status
    is_active = Column(Boolean, default=True, nullable=False)

    # Metadata
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    created_by = Column(PostgresUUID(as_uuid=True), nullable=False)

    # Relationships
    group = relationship("NotificationGroup", back_populates="event_subscriptions")

    def __repr__(self):
        return f"<NotificationGroupEvent {self.group.name} -> {self.event_type}>"


# ============================================================================
# DEFAULT GROUPS CONFIGURATION
# ============================================================================

DEFAULT_GROUPS = [
    {
        "name": "All Admins",
        "description": "Super admins and administrators - receive all notifications from all stations",
        "station_id": None,  # All stations
        "events": ["all"],
    },
    {
        "name": "Customer Service Team",
        "description": "Customer service representatives - receive all customer-facing notifications",
        "station_id": None,  # All stations
        "events": ["all"],
    },
    {
        "name": "Booking Management Team",
        "description": "Booking coordinators - receive booking-related notifications only",
        "station_id": None,
        "events": ["new_booking", "booking_edit", "booking_cancellation"],
    },
    {
        "name": "Payment Team",
        "description": "Payment processors - receive payment-related notifications only",
        "station_id": None,
        "events": ["payment_received"],
    },
]
