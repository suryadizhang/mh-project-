"""
Booking Reminder Model
Stores scheduled reminders for bookings (email/SMS).
"""

from datetime import datetime
from enum import Enum
from uuid import uuid4

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID as PostgreSQLUUID
from sqlalchemy.orm import relationship

from core.database import Base

# TYPE_CHECKING to avoid circular import
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from models.booking import Booking  # noqa: F401


class ReminderType(str, Enum):
    """Types of reminders"""

    EMAIL = "email"
    SMS = "sms"
    BOTH = "both"


class ReminderStatus(str, Enum):
    """Status of reminder delivery"""

    PENDING = "pending"
    SENT = "sent"
    FAILED = "failed"
    CANCELLED = "cancelled"


class BookingReminder(Base):
    """
    Booking reminder model.

    Stores scheduled reminders for bookings that are sent via email/SMS.
    Integrates with Celery for async sending.

    Attributes:
        id: Unique identifier
        booking_id: Reference to booking
        reminder_type: Type of reminder (email, sms, both)
        scheduled_for: When to send the reminder
        sent_at: When the reminder was actually sent
        status: Current status (pending, sent, failed, cancelled)
        message: Custom message content (optional)
        error_message: Error details if failed
        created_at: Creation timestamp
        updated_at: Last update timestamp
    """

    __tablename__ = "booking_reminders"
    __table_args__ = {"schema": "core", "extend_existing": True}  # core schema

    id = Column(PostgreSQLUUID(as_uuid=True), primary_key=True, default=uuid4)
    booking_id = Column(
        Integer,
        ForeignKey("core.bookings.id", ondelete="CASCADE"),  # Reference core.bookings
        nullable=False,
        index=True,
    )
    reminder_type = Column(String(50), nullable=False)
    scheduled_for = Column(DateTime(timezone=True), nullable=False, index=True)
    sent_at = Column(DateTime(timezone=True), nullable=True)
    status = Column(String(50), nullable=False, default=ReminderStatus.PENDING.value, index=True)
    message = Column(Text, nullable=True)
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)
    updated_at = Column(
        DateTime(timezone=True), nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    # Relationships
    booking = relationship("Booking", back_populates="reminders")

    def __repr__(self) -> str:
        return f"<BookingReminder(id={self.id}, booking_id={self.booking_id}, type={self.reminder_type}, status={self.status})>"
