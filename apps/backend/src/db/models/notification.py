"""
Admin Notification Group Management System (Modern SQLAlchemy 2.0)

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

import enum
from datetime import datetime
from typing import TYPE_CHECKING
from uuid import UUID, uuid4

from sqlalchemy import Boolean, DateTime, ForeignKey, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..base_class import Base

if TYPE_CHECKING:
    pass  # Add imports if relationships need typing


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
    __table_args__ = {"extend_existing": True}

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)

    # Group Information
    name: Mapped[str] = mapped_column(String(100), unique=True, index=True)
    description: Mapped[str | None] = mapped_column(Text)

    # Station Filtering (NULL = all stations, specific UUID = only that station)
    station_id: Mapped[UUID | None] = mapped_column(index=True)

    # WhatsApp Configuration
    whatsapp_group_id: Mapped[str | None] = mapped_column(String(100))

    # Status
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    # Metadata
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
    created_by: Mapped[UUID]  # User who created group

    # Relationships
    members: Mapped[list["NotificationGroupMember"]] = relationship(
        back_populates="group", cascade="all, delete-orphan"
    )
    event_subscriptions: Mapped[list["NotificationGroupEvent"]] = relationship(
        back_populates="group", cascade="all, delete-orphan"
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
    __table_args__ = {"extend_existing": True}

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)

    # Group Relationship
    group_id: Mapped[UUID] = mapped_column(
        ForeignKey("notification_groups.id", ondelete="CASCADE"), index=True
    )

    # Member Information
    phone_number: Mapped[str] = mapped_column(String(20), index=True)
    name: Mapped[str] = mapped_column(String(100))
    email: Mapped[str | None] = mapped_column(String(255))

    # Notification Preferences
    receive_whatsapp: Mapped[bool] = mapped_column(Boolean, default=True)
    receive_sms: Mapped[bool] = mapped_column(Boolean, default=False)
    receive_email: Mapped[bool] = mapped_column(Boolean, default=False)

    # Priority level
    priority: Mapped[str] = mapped_column(String(20), default="medium")

    # Status
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    # Metadata
    added_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    added_by: Mapped[UUID | None]  # User who added member

    # Relationships
    group: Mapped["NotificationGroup"] = relationship(back_populates="members")

    def __repr__(self):
        return f"<NotificationGroupMember {self.name} ({self.phone_number})>"


class NotificationGroupEvent(Base):
    """
    Event subscriptions for notification groups.

    Defines which notification events each group should receive.
    """

    __tablename__ = "notification_group_events"
    __table_args__ = {"extend_existing": True}

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)

    # Group Relationship
    group_id: Mapped[UUID] = mapped_column(
        ForeignKey("notification_groups.id", ondelete="CASCADE"), index=True
    )

    # Event Configuration
    event_type: Mapped[str] = mapped_column(String(50), index=True)

    # Status
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    # Metadata
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    created_by: Mapped[UUID]

    # Relationships
    group: Mapped["NotificationGroup"] = relationship(back_populates="event_subscriptions")

    def __repr__(self):
        return f"<NotificationGroupEvent {self.event_type}>"


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
