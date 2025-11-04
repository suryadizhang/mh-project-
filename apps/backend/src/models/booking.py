"""
Booking model and related enums
"""

from datetime import datetime
from enum import Enum

from sqlalchemy import (
    Column,
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
)
from sqlalchemy import Enum as SQLEnum
from sqlalchemy.orm import relationship

from .base import BaseModel


class BookingStatus(str, Enum):
    """Booking status enumeration"""

    PENDING = "pending"
    CONFIRMED = "confirmed"
    SEATED = "seated"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    NO_SHOW = "no_show"


class PaymentStatus(str, Enum):
    """Payment status enumeration"""

    PENDING = "pending"
    COMPLETED = "completed"
    FAILED = "failed"
    REFUNDED = "refunded"
    CANCELLED = "cancelled"


class Booking(BaseModel):
    """Booking model"""

    __tablename__ = "bookings"

    customer_id = Column(Integer, ForeignKey("customers.id"), nullable=False, index=True)
    booking_datetime = Column(DateTime, nullable=False, index=True)
    party_size = Column(Integer, nullable=False)
    status = Column(
        SQLEnum(BookingStatus), default=BookingStatus.PENDING, nullable=False, index=True
    )

    # Contact information (may be different from customer profile)
    contact_phone = Column(String(20))
    contact_email = Column(String(255))

    # Special requests and notes
    special_requests = Column(Text)
    internal_notes = Column(Text)

    # Status timestamps
    confirmed_at = Column(DateTime)
    seated_at = Column(DateTime)
    completed_at = Column(DateTime)
    cancelled_at = Column(DateTime)
    cancellation_reason = Column(Text)

    # Table assignment
    table_number = Column(String(10))

    # Relationships
    customer = relationship("Customer", back_populates="bookings", lazy="select")
    payments = relationship("Payment", back_populates="booking", lazy="select")

    def __repr__(self):
        return f"<Booking(id={self.id}, customer_id={self.customer_id}, datetime={self.booking_datetime}, status={self.status})>"

    @property
    def is_active(self) -> bool:
        """Check if booking is in an active state"""
        return self.status in [BookingStatus.PENDING, BookingStatus.CONFIRMED, BookingStatus.SEATED]

    @property
    def can_be_cancelled(self) -> bool:
        """Check if booking can be cancelled"""
        return self.status in [BookingStatus.PENDING, BookingStatus.CONFIRMED, BookingStatus.SEATED]

    @property
    def can_be_confirmed(self) -> bool:
        """Check if booking can be confirmed"""
        return self.status == BookingStatus.PENDING

    def get_time_until_booking(self) -> int | None:
        """Get hours until booking (None if past)"""
        if self.booking_datetime <= datetime.utcnow():
            return None

        time_diff = self.booking_datetime - datetime.utcnow()
        return int(time_diff.total_seconds() / 3600)


class Payment(BaseModel):
    """Payment model for tracking booking payments"""

    __tablename__ = "payments"

    booking_id = Column(Integer, ForeignKey("bookings.id"), nullable=False, index=True)

    # Payment details
    amount = Column(Numeric(10, 2), nullable=False)  # Using Decimal for money
    payment_method = Column(String(50), nullable=False)  # zelle, venmo, stripe, cash, check
    payment_reference = Column(String(255))  # Transaction ID, check number, etc.
    status = Column(
        SQLEnum(PaymentStatus), default=PaymentStatus.PENDING, nullable=False, index=True
    )

    # Payment source information (for matching)
    sender_name = Column(String(255))
    sender_phone = Column(String(20))
    sender_email = Column(String(255))

    # Notification details
    received_at = Column(DateTime, index=True)  # When payment was received
    notification_email_id = Column(String(255))  # Email message ID for tracking

    # Processing info
    processed_by = Column(String(100))  # user_id or "system"
    processed_at = Column(DateTime)
    confirmation_sent_at = Column(DateTime)

    # Notes
    notes = Column(Text)
    internal_notes = Column(Text)

    # Relationships
    booking = relationship("Booking", back_populates="payments", lazy="select")

    def __repr__(self):
        return f"<Payment(id={self.id}, booking_id={self.booking_id}, amount={self.amount}, method={self.payment_method}, status={self.status})>"

    @property
    def amount_cents(self) -> int:
        """Get amount in cents (for compatibility)"""
        if self.amount:
            return int(self.amount * 100)
        return 0

    @property
    def is_pending(self) -> bool:
        """Check if payment is pending"""
        return self.status == PaymentStatus.PENDING

    @property
    def is_completed(self) -> bool:
        """Check if payment is completed"""
        return self.status == PaymentStatus.COMPLETED
