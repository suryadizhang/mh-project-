"""
Booking model and related enums

Architecture: Uses mixin composition (enterprise pattern) instead of BaseModel inheritance.
This enables flexible schema evolution for multi-tenant, white-label, and sharding.
"""

from datetime import date, datetime, timezone
from enum import Enum

import sqlalchemy as sa
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
from sqlalchemy.dialects.postgresql import UUID

from .base import Base, BaseModel
from .mixins import UUIDPKMixin, TimestampMixin, SoftDeleteTimestampMixin, OptimisticLockMixin


class BookingStatus(str, Enum):
    """Booking status enumeration - matches PostgreSQL booking_status enum"""

    NEW = "new"
    DEPOSIT_PENDING = "deposit_pending"
    CONFIRMED = "confirmed"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    NO_SHOW = "no_show"

    # Legacy aliases for backward compatibility
    PENDING = "deposit_pending"  # Maps to DEPOSIT_PENDING
    SEATED = "confirmed"  # Maps to CONFIRMED (seated is part of confirmed flow)


class PaymentStatus(str, Enum):
    """Payment status enumeration"""

    PENDING = "pending"
    COMPLETED = "completed"
    FAILED = "failed"
    REFUNDED = "refunded"
    CANCELLED = "cancelled"


class Booking(Base, UUIDPKMixin, TimestampMixin, SoftDeleteTimestampMixin, OptimisticLockMixin):
    """Booking model - Production schema with enterprise mixin composition

    Schema: core.bookings
    Source of truth: PostgreSQL information_schema.columns

    Mixins provide:
    - UUIDPKMixin: id (UUID) - distributed system ready
    - TimestampMixin: created_at, updated_at - audit trail
    - SoftDeleteTimestampMixin: deleted_at - compliance-friendly deletion
    - OptimisticLockMixin: version - race condition protection (Bug #13)

    Architecture benefits:
    - Clean composition (no override hacks)
    - Ready for multi-tenant (add StationTenantMixin when needed)
    - Ready for white-label (add BusinessTenantMixin when needed)
    - Ready for sharding (UUID PKs + station_id as shard key)
    """

    __tablename__ = "bookings"
    __table_args__ = {"schema": "core", "extend_existing": True}

    # ═══════════════════════════════════════════════════════════════════
    # CORE IDENTIFICATION (UUID in production!)
    # ═══════════════════════════════════════════════════════════════════
    customer_id = Column(
        UUID(as_uuid=True), ForeignKey("core.customers.id"), nullable=False, index=True
    )  # Fixed: customers table is in core schema

    # ═══════════════════════════════════════════════════════════════════
    # EVENT DETAILS
    # ═══════════════════════════════════════════════════════════════════
    date = Column(sa.Date, nullable=False, index=True)
    slot = Column(sa.Time, nullable=False, index=True)

    # ═══════════════════════════════════════════════════════════════════
    # LOCATION & ASSIGNMENT (Production columns)
    # ═══════════════════════════════════════════════════════════════════
    address_encrypted = Column(Text, nullable=False)  # Encrypted customer address
    zone = Column(String, nullable=False)  # Service zone (e.g., "Zone A", "Zone B")
    chef_id = Column(UUID(as_uuid=True), nullable=True)  # Assigned chef
    station_id = Column(
        UUID(as_uuid=True), nullable=False
    )  # Multi-station support (CRITICAL - 50+ usages)

    # ═══════════════════════════════════════════════════════════════════
    # PARTY COMPOSITION
    # ═══════════════════════════════════════════════════════════════════
    party_adults = Column(Integer, nullable=False, default=0)
    party_kids = Column(Integer, nullable=False, default=0)

    # ═══════════════════════════════════════════════════════════════════
    # STATUS (PostgreSQL ENUM type - native database enum for type safety)
    # ═══════════════════════════════════════════════════════════════════
    status = Column(
        SQLEnum(
            BookingStatus,
            name="booking_status",
            native_enum=True,
            create_constraint=True,
            values_callable=lambda x: [e.value for e in x],
        ),
        default=BookingStatus.DEPOSIT_PENDING,
        nullable=False,
        index=True,
    )

    # ═══════════════════════════════════════════════════════════════════
    # PRICING (Production columns - cents to avoid float precision issues)
    # ═══════════════════════════════════════════════════════════════════
    deposit_due_cents = Column(Integer, nullable=False)  # Deposit amount in cents
    total_due_cents = Column(Integer, nullable=False)  # Total amount in cents

    # ═══════════════════════════════════════════════════════════════════
    # MENU & TRACKING (Production JSONB columns)
    # ═══════════════════════════════════════════════════════════════════
    menu_items = Column(sa.JSON, nullable=True)  # Selected menu items (JSONB in production)
    source = Column(
        String, nullable=False
    )  # Booking source tracking (e.g., "website", "phone", "ai_agent")
    booking_metadata = Column(
        "metadata", sa.JSON, nullable=True
    )  # Extensibility field (JSONB in production) - Column name "metadata" mapped to attribute "booking_metadata"

    # ═══════════════════════════════════════════════════════════════════
    # NOTES
    # ═══════════════════════════════════════════════════════════════════
    special_requests = Column(Text, nullable=True)
    notes = Column(Text, nullable=True)  # Admin/internal notes (NOT internal_notes!)

    # ═══════════════════════════════════════════════════════════════════
    # DUAL DEADLINE SYSTEM
    # ═══════════════════════════════════════════════════════════════════
    customer_deposit_deadline = Column(DateTime, index=True)  # 2h - shown to customer
    internal_deadline = Column(DateTime, index=True)  # 24h - actual enforcement
    deposit_deadline = Column(DateTime)  # Legacy compatibility

    # ═══════════════════════════════════════════════════════════════════
    # MANUAL DEPOSIT CONFIRMATION
    # ═══════════════════════════════════════════════════════════════════
    deposit_confirmed_at = Column(DateTime)
    deposit_confirmed_by = Column(String(255))

    # ═══════════════════════════════════════════════════════════════════
    # ADMIN HOLD SYSTEM
    # ═══════════════════════════════════════════════════════════════════
    hold_on_request = Column(Boolean, default=False, nullable=False)
    held_by = Column(String(255))
    held_at = Column(DateTime)
    hold_reason = Column(Text)

    # ═══════════════════════════════════════════════════════════════════
    # TCPA COMPLIANCE
    # ═══════════════════════════════════════════════════════════════════
    sms_consent = Column(Boolean, default=False, nullable=False)
    sms_consent_timestamp = Column(DateTime(timezone=True))

    # ═══════════════════════════════════════════════════════════════════
    # BUG #13 FIX - OPTIMISTIC LOCKING (Added by migration fe61eb9d1264)
    # ═══════════════════════════════════════════════════════════════════
    version = Column(Integer, default=1, nullable=False)

    # ═══════════════════════════════════════════════════════════════════
    # RELATIONSHIPS
    # ═══════════════════════════════════════════════════════════════════
    # customer = relationship("models.customer.Customer", back_populates="bookings", lazy="select")
    # payments = relationship("models.booking.Payment", back_populates="booking", lazy="select")
    reminders = relationship(
        "BookingReminder", back_populates="booking", lazy="select", cascade="all, delete-orphan"
    )
    # message_threads = relationship("Thread", back_populates="booking", lazy="select", foreign_keys="[Thread.booking_id]")
    # terms_acknowledgments = relationship("TermsAcknowledgment", back_populates="booking", lazy="select")

    def __repr__(self):
        return f"<Booking(id={self.id}, customer_id={self.customer_id}, date={self.date}, slot={self.slot}, status={self.status})>"

    @property
    def is_active(self) -> bool:
        """Check if booking is in an active state"""
        return self.status not in ["cancelled", "completed", "no_show"]

    @property
    def can_be_cancelled(self) -> bool:
        """Check if booking can be cancelled"""
        return self.status in ["pending", "confirmed", "seated"]

    @property
    def can_be_confirmed(self) -> bool:
        """Check if booking can be confirmed"""
        return self.status == "pending"

    @property
    def event_time(self) -> str:
        """Get event time in HH:MM format from slot"""
        if self.slot:
            return self.slot.strftime("%H:%M")
        return "00:00"

    @property
    def event_date(self) -> "date":
        """Get event date

        Raises:
            ValueError: If date is None
        """
        if not self.date:
            raise ValueError(f"Booking {self.id} has no date set")
        return self.date

    @property
    def party_size(self) -> int:
        """Total party size (adults + kids) for backward compatibility"""
        return (self.party_adults or 0) + (self.party_kids or 0)

    def get_time_until_booking(self) -> int | None:
        """Get hours until booking (None if past)"""
        if not self.date or not self.slot:
            return None

        # Combine date and slot to get booking datetime
        booking_datetime = datetime.combine(self.date, self.slot).replace(tzinfo=timezone.utc)

        if booking_datetime <= datetime.now(timezone.utc):
            return None

        time_diff = booking_datetime - datetime.now(timezone.utc)
        return int(time_diff.total_seconds() / 3600)


class Payment(BaseModel):
    """Payment model for tracking booking payments"""

    __tablename__ = "payments"
    __table_args__ = {"schema": "core", "extend_existing": True}  # core schema

    booking_id = Column(
        Integer, ForeignKey("core.bookings.id"), nullable=False, index=True
    )  # Reference core.bookings

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

    # Relationships (temporarily commented for Bug #13 schema fixes)
    # Use fully-qualified module path to avoid "Multiple classes found for path 'Booking'" error
    # booking = relationship("models.booking.Booking", back_populates="payments", lazy="select")

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
