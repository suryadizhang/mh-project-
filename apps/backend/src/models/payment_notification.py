"""
Payment Notification Models - Production Ready

Database models for automatic payment detection and matching system.
Handles payment notifications from Stripe, Venmo, Zelle, and Bank of America.
"""

from datetime import datetime
from enum import Enum

from sqlalchemy import (
    JSON,
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    Text,
)
from sqlalchemy import Enum as SQLEnum
from sqlalchemy.orm import relationship

from .base import BaseModel


class PaymentProvider(str, Enum):
    """Payment provider enumeration"""

    STRIPE = "stripe"
    VENMO = "venmo"
    ZELLE = "zelle"
    BANK_OF_AMERICA = "bank_of_america"
    PLAID = "plaid"
    CASH = "cash"
    CHECK = "check"
    OTHER = "other"


class PaymentNotificationStatus(str, Enum):
    """Payment notification processing status"""

    DETECTED = "detected"  # Email detected, parsed successfully
    PENDING_MATCH = "pending_match"  # Waiting for match attempt
    MATCHED = "matched"  # Matched to booking/payment
    CONFIRMED = "confirmed"  # Payment confirmed by system
    MANUAL_REVIEW = "manual_review"  # Needs manual review
    IGNORED = "ignored"  # Marked as ignore
    ERROR = "error"  # Processing error


class CateringBooking(BaseModel):
    """
    Catering/Hibachi booking model for payment tracking

    This is the main booking entity that customers create when requesting
    hibachi catering services. Each booking can have multiple payments.
    """

    __tablename__ = "catering_bookings"

    # Customer Information
    customer_name = Column(String(255), nullable=False, index=True)
    customer_email = Column(String(255), nullable=False, index=True)
    customer_phone = Column(String(20), nullable=False, index=True)

    # Alternative payer (for friend/family payments)
    alternative_payer_name = Column(String(255), nullable=True)
    alternative_payer_email = Column(String(255), nullable=True)
    alternative_payer_phone = Column(String(20), nullable=True)
    alternative_payer_venmo = Column(String(100), nullable=True)

    # Event Details
    event_date = Column(DateTime, nullable=False, index=True)
    event_location = Column(Text, nullable=False)
    guest_count = Column(Integer, nullable=False)
    service_type = Column(String(100))  # hibachi, sushi, full_service

    # Pricing
    base_amount = Column(Numeric(10, 2), nullable=False)
    tip_amount = Column(Numeric(10, 2), default=0)
    tax_amount = Column(Numeric(10, 2), default=0)
    total_amount = Column(Numeric(10, 2), nullable=False)

    # Booking Status
    status = Column(
        String(50), default="pending", index=True
    )  # pending, confirmed, completed, cancelled

    # Special Requests
    special_requests = Column(Text)
    dietary_restrictions = Column(Text)
    internal_notes = Column(Text)

    # Timestamps
    confirmed_at = Column(DateTime)
    completed_at = Column(DateTime)
    cancelled_at = Column(DateTime)

    # Relationships
    payments = relationship(
        "CateringPayment", back_populates="booking", cascade="all, delete-orphan"
    )
    notifications = relationship(
        "PaymentNotification", back_populates="booking", cascade="all, delete-orphan"
    )

    def __repr__(self):
        return f"<CateringBooking(id={self.id}, customer={self.customer_name}, date={self.event_date}, total=${self.total_amount})>"

    @property
    def total_paid(self) -> float:
        """Calculate total amount paid across all confirmed payments"""
        return sum(p.amount for p in self.payments if p.status == "confirmed")

    @property
    def balance_due(self) -> float:
        """Calculate remaining balance"""
        return float(self.total_amount) - self.total_paid

    @property
    def is_fully_paid(self) -> bool:
        """Check if booking is fully paid"""
        return self.balance_due <= 0


class CateringPayment(BaseModel):
    """
    Payment record for catering bookings

    Tracks individual payment transactions. A booking can have multiple payments
    (deposit, balance, friend/family split payments).
    """

    __tablename__ = "catering_payments"

    # Foreign Keys
    booking_id = Column(
        Integer, ForeignKey("catering_bookings.id", ondelete="CASCADE"), nullable=False, index=True
    )
    notification_id = Column(
        Integer,
        ForeignKey("payment_notifications.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    # Payment Details
    amount = Column(Numeric(10, 2), nullable=False)
    payment_method = Column(SQLEnum(PaymentProvider), nullable=False, index=True)
    status = Column(
        String(50), default="pending", index=True
    )  # pending, confirmed, refunded, failed

    # Transaction Information
    transaction_id = Column(String(255), unique=True, index=True)  # Stripe, Venmo, Zelle ID
    sender_name = Column(String(255))
    sender_email = Column(String(255))
    sender_phone = Column(String(20))
    sender_username = Column(String(100))  # Venmo username

    # Payment Type
    payment_type = Column(String(50), default="full")  # deposit, balance, full, partial

    # Processing
    processed_at = Column(DateTime)
    confirmed_at = Column(DateTime)
    confirmation_sent = Column(Boolean, default=False)

    # Notes
    payment_note = Column(Text)  # Customer's payment note/memo
    admin_note = Column(Text)

    # Relationships
    booking = relationship("CateringBooking", back_populates="payments")
    notification = relationship("PaymentNotification", back_populates="payment", uselist=False)

    # Indexes for performance
    __table_args__ = (
        Index("idx_payment_booking_status", booking_id, status),
        Index("idx_payment_method_status", payment_method, status),
    )

    def __repr__(self):
        return f"<CateringPayment(id={self.id}, booking_id={self.booking_id}, amount=${self.amount}, method={self.payment_method}, status={self.status})>"


class PaymentNotification(BaseModel):
    """
    Payment notification from email monitoring

    Stores detected payment emails from Gmail (Stripe, Venmo, Zelle, BofA).
    Tracks matching process and links to payments.
    """

    __tablename__ = "payment_notifications"

    # Email Details
    email_id = Column(String(255), unique=True, nullable=False, index=True)  # Gmail message ID
    email_subject = Column(String(500), nullable=False)
    email_from = Column(String(255), nullable=False, index=True)
    email_body = Column(Text)
    received_at = Column(DateTime, nullable=False, index=True)

    # Parsed Payment Information
    provider = Column(SQLEnum(PaymentProvider), nullable=False, index=True)
    amount = Column(Numeric(10, 2), nullable=False)
    transaction_id = Column(String(255), index=True)

    # Sender Information (from email)
    sender_name = Column(String(255), index=True)
    sender_email = Column(String(255))
    sender_phone = Column(String(20), index=True)  # Customer's phone from payment note
    sender_username = Column(String(100))  # Venmo username

    # Matching Information
    status = Column(
        SQLEnum(PaymentNotificationStatus),
        default=PaymentNotificationStatus.DETECTED,
        nullable=False,
        index=True,
    )
    match_score = Column(Integer, default=0)  # Confidence score (0-225)
    match_details = Column(JSON)  # Details about why/how it matched

    # Foreign Keys
    booking_id = Column(
        Integer, ForeignKey("catering_bookings.id", ondelete="SET NULL"), nullable=True, index=True
    )
    payment_id = Column(
        Integer, ForeignKey("catering_payments.id", ondelete="SET NULL"), nullable=True, index=True
    )

    # Processing
    parsed_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    matched_at = Column(DateTime)
    confirmed_at = Column(DateTime)
    reviewed_by = Column(Integer, ForeignKey("users.id"), nullable=True)  # Admin who reviewed

    # Flags
    is_read = Column(Boolean, default=False)
    is_processed = Column(Boolean, default=False, index=True)
    requires_manual_review = Column(Boolean, default=False, index=True)
    is_duplicate = Column(Boolean, default=False)

    # Notes
    admin_notes = Column(Text)
    error_message = Column(Text)

    # Relationships
    booking = relationship("CateringBooking", back_populates="notifications")
    payment = relationship("CateringPayment", back_populates="notification", uselist=False)

    # Indexes for performance
    __table_args__ = (
        Index("idx_notification_status_processed", status, is_processed),
        Index("idx_notification_provider_date", provider, received_at),
        Index("idx_notification_manual_review", requires_manual_review, is_processed),
    )

    def __repr__(self):
        return f"<PaymentNotification(id={self.id}, provider={self.provider}, amount=${self.amount}, status={self.status})>"

    @property
    def is_matched(self) -> bool:
        """Check if notification has been matched"""
        return self.status in [
            PaymentNotificationStatus.MATCHED,
            PaymentNotificationStatus.CONFIRMED,
        ]

    @property
    def needs_action(self) -> bool:
        """Check if notification needs admin action"""
        return (
            self.requires_manual_review
            and not self.is_processed
            and self.status != PaymentNotificationStatus.IGNORED
        )
