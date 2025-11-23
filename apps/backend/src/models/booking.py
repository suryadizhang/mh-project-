"""
Booking model and related enums
"""

from datetime import date, datetime, timezone
from enum import Enum

from sqlalchemy import (
    Boolean,
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

    # Optimistic locking: Prevents race conditions on concurrent updates
    # Increment on each update, UPDATE ... WHERE version = old_version
    version = Column(Integer, default=1, nullable=False)

    # Contact information (may be different from customer profile)
    contact_phone = Column(String(20))
    contact_email = Column(String(255))

    # TCPA Compliance - SMS Consent
    sms_consent = Column(Boolean, default=False, nullable=False)
    sms_consent_timestamp = Column(DateTime)  # When consent was given

    # Special requests and notes
    special_requests = Column(Text)
    internal_notes = Column(Text)

    # Status timestamps
    confirmed_at = Column(DateTime)
    seated_at = Column(DateTime)
    completed_at = Column(DateTime)
    cancelled_at = Column(DateTime)
    cancellation_reason = Column(Text)

    # Dual deadline system: Tell customer 2h (urgency), give them 24h (grace)
    customer_deposit_deadline = Column(DateTime, index=True)  # 2 hours - shown to customer
    internal_deadline = Column(DateTime, index=True)  # 24 hours - actual enforcement
    deposit_deadline = Column(DateTime)  # DEPRECATED - kept for backward compatibility

    # Manual deposit confirmation by admin
    deposit_confirmed_at = Column(DateTime)  # When admin clicked "Deposit Received"
    deposit_confirmed_by = Column(String(255))  # Admin email who confirmed

    # Admin hold system to prevent auto-cancellation
    hold_on_request = Column(Boolean, default=False)  # Admin/CS can hold booking
    held_by = Column(String(255))  # Staff member who placed the hold
    held_at = Column(DateTime)  # When the hold was placed
    hold_reason = Column(Text)  # Reason for holding (e.g., "Customer requested extension", "VIP client")

    # Table assignment
    table_number = Column(String(10))

    # Relationships
    # Use fully-qualified module path to avoid "Multiple classes found for path 'Customer'" error
    # This explicitly references models.customer.Customer, not legacy_core.Customer or api.ai.endpoints.models.Customer
    customer = relationship("models.customer.Customer", back_populates="bookings", lazy="select")
    payments = relationship("models.booking.Payment", back_populates="booking", lazy="select")
    message_threads = relationship("Thread", back_populates="booking", lazy="select", foreign_keys="[Thread.booking_id]")
    terms_acknowledgments = relationship("TermsAcknowledgment", back_populates="booking", lazy="select")

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

    @property
    def event_time(self) -> str:
        """Get event time in HH:MM format extracted from booking_datetime"""
        if self.booking_datetime:
            return self.booking_datetime.strftime("%H:%M")
        return "00:00"

    @property
    def event_date(self) -> "date":
        """Get event date extracted from booking_datetime

        Raises:
            ValueError: If booking_datetime is None
        """
        if not self.booking_datetime:
            raise ValueError(f"Booking {self.id} has no booking_datetime set")
        return self.booking_datetime.date()

    def get_time_until_booking(self) -> int | None:
        """Get hours until booking (None if past)"""
        if self.booking_datetime <= datetime.now(timezone.utc):
            return None

        time_diff = self.booking_datetime - datetime.now(timezone.utc)
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
    # Use fully-qualified module path to avoid "Multiple classes found for path 'Booking'" error
    booking = relationship("models.booking.Booking", back_populates="payments", lazy="select")

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
