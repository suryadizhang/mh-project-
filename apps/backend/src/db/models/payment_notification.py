"""
Payment Notification Models
============================

SQLAlchemy models for payment notification and matching system.

Tables:
- catering_payments: Payment records linked to bookings
- payment_notifications: Incoming payment notification emails

The CateringBooking is an alias to core.Booking since we use the core.bookings table.
"""

import enum
from datetime import datetime
from decimal import Decimal
from typing import Optional
from uuid import UUID

from sqlalchemy import (
    Boolean,
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
    text,
)
from sqlalchemy import Enum as SQLEnum
from sqlalchemy.dialects.postgresql import JSON
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from db.base import Base

# Re-export Booking as CateringBooking for backward compatibility
# The migration notes: "we use core.bookings instead"
from db.models.core import Booking as CateringBooking


class PaymentProvider(str, enum.Enum):
    """Payment provider types."""

    STRIPE = "STRIPE"
    VENMO = "VENMO"
    ZELLE = "ZELLE"
    BANK_OF_AMERICA = "BANK_OF_AMERICA"
    PLAID = "PLAID"
    CASH = "CASH"
    CHECK = "CHECK"
    OTHER = "OTHER"


class PaymentNotificationStatus(str, enum.Enum):
    """Payment notification processing status."""

    DETECTED = "DETECTED"
    PENDING_MATCH = "PENDING_MATCH"
    MATCHED = "MATCHED"
    CONFIRMED = "CONFIRMED"
    MANUAL_REVIEW = "MANUAL_REVIEW"
    IGNORED = "IGNORED"
    ERROR = "ERROR"


class CateringPayment(Base):
    """
    Payment record for a catering booking.

    Links payments to bookings and notifications.
    """

    __tablename__ = "catering_payments"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        server_default=text("CURRENT_TIMESTAMP"),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        server_default=text("CURRENT_TIMESTAMP"),
    )

    # Foreign Keys
    booking_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("core.bookings.id", ondelete="CASCADE"),
        nullable=False,
    )
    notification_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    # Payment Details
    amount: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    payment_method: Mapped[PaymentProvider] = mapped_column(
        SQLEnum(PaymentProvider, name="paymentprovider"),
        nullable=False,
    )
    status: Mapped[Optional[str]] = mapped_column(
        String(50),
        nullable=True,
        server_default="pending",
    )

    # Transaction Information
    transaction_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    sender_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    sender_email: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    sender_phone: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    sender_username: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)

    # Payment Type
    payment_type: Mapped[Optional[str]] = mapped_column(
        String(50),
        nullable=True,
        server_default="full",
    )

    # Processing
    processed_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    confirmed_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    confirmation_sent: Mapped[Optional[bool]] = mapped_column(
        Boolean,
        nullable=True,
        server_default="false",
    )

    # Notes
    payment_note: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    admin_note: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    def __repr__(self) -> str:
        return f"<CateringPayment(id={self.id}, amount={self.amount}, method={self.payment_method})>"


class PaymentNotification(Base):
    """
    Payment notification from email.

    Stores parsed payment information from provider emails (Venmo, Zelle, etc.)
    and tracks the matching/confirmation workflow.
    """

    __tablename__ = "payment_notifications"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        server_default=text("CURRENT_TIMESTAMP"),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        server_default=text("CURRENT_TIMESTAMP"),
    )

    # Email Details
    email_id: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    email_subject: Mapped[str] = mapped_column(String(500), nullable=False)
    email_from: Mapped[str] = mapped_column(String(255), nullable=False)
    email_body: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    received_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)

    # Parsed Payment Information
    provider: Mapped[PaymentProvider] = mapped_column(
        SQLEnum(PaymentProvider, name="paymentprovider"),
        nullable=False,
    )
    amount: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    transaction_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    # Sender Information
    sender_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    sender_email: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    sender_phone: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    sender_username: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)

    # Matching Information
    status: Mapped[PaymentNotificationStatus] = mapped_column(
        SQLEnum(PaymentNotificationStatus, name="paymentnotificationstatus"),
        nullable=False,
        server_default="DETECTED",
    )
    match_score: Mapped[Optional[int]] = mapped_column(
        Integer,
        nullable=True,
        server_default="0",
    )
    match_details: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)

    # Foreign Keys
    booking_id: Mapped[Optional[UUID]] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("core.bookings.id", ondelete="SET NULL"),
        nullable=True,
    )
    payment_id: Mapped[Optional[int]] = mapped_column(
        Integer,
        ForeignKey("catering_payments.id", ondelete="SET NULL"),
        nullable=True,
    )
    reviewed_by: Mapped[Optional[UUID]] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("identity.users.id", ondelete="SET NULL"),
        nullable=True,
    )

    # Processing
    parsed_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        server_default=text("CURRENT_TIMESTAMP"),
    )
    matched_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    confirmed_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    # Flags
    is_read: Mapped[Optional[bool]] = mapped_column(
        Boolean,
        nullable=True,
        server_default="false",
    )
    is_processed: Mapped[Optional[bool]] = mapped_column(
        Boolean,
        nullable=True,
        server_default="false",
    )
    requires_manual_review: Mapped[Optional[bool]] = mapped_column(
        Boolean,
        nullable=True,
        server_default="false",
    )
    is_duplicate: Mapped[Optional[bool]] = mapped_column(
        Boolean,
        nullable=True,
        server_default="false",
    )

    # Notes
    admin_notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    def __repr__(self) -> str:
        return f"<PaymentNotification(id={self.id}, provider={self.provider}, amount={self.amount}, status={self.status})>"


# Export all models
__all__ = [
    "PaymentProvider",
    "PaymentNotificationStatus",
    "CateringPayment",
    "PaymentNotification",
    "CateringBooking",
]
