"""
SQLAlchemy Models - Core Schema
================================

Core business entities:
- Bookings
- Customers
- Chefs
- Message Threads
- Messages
- Social Threads
- Reviews
- Pricing Tiers
- Stations (reference from identity schema)
- Users (reference from public schema)

All models use:
- UUID primary keys
- Timezone-aware datetime fields
- Schema qualification (__table_args__)
- Proper foreign key relationships
- Type hints for IDE support
"""

from datetime import datetime, date, time
from typing import Optional, List
from uuid import UUID, uuid4

from sqlalchemy import (
    String,
    Text,
    Integer,
    Boolean,
    DateTime,
    Date,
    Time,
    ForeignKey,
    ForeignKeyConstraint,
    Index,
    CheckConstraint,
    Enum as SQLEnum,
    text,
)
from sqlalchemy.dialects.postgresql import UUID as PGUUID, JSONB, ARRAY
from sqlalchemy.orm import relationship, Mapped, mapped_column
from sqlalchemy.sql import func

# CRITICAL: Must use unified Base from core.database (same as models.base.Base)
# This ensures all models share the same metadata registry (enterprise single-source-of-truth)
from core.database import Base


# ==================== ENUMS ====================

import enum


class BookingStatus(str, enum.Enum):
    """Booking status workflow"""

    PENDING = "pending"
    DEPOSIT_PENDING = "deposit_pending"
    DEPOSIT_PAID = "deposit_paid"
    CONFIRMED = "confirmed"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    NO_SHOW = "no_show"


class MenuCategory(str, enum.Enum):
    """Menu categories for catering"""

    APPETIZER = "appetizer"
    ENTREE = "entree"
    DESSERT = "dessert"
    DRINK = "drink"
    SPECIAL = "special"


class MessageChannel(str, enum.Enum):
    """Communication channels"""

    SMS = "sms"
    EMAIL = "email"
    PHONE = "phone"
    WEB_CHAT = "web_chat"
    SOCIAL_MEDIA = "social_media"


class ThreadStatus(str, enum.Enum):
    """Message thread status"""

    ACTIVE = "active"
    ARCHIVED = "archived"
    CLOSED = "closed"
    SPAM = "spam"


class SocialPlatform(str, enum.Enum):
    """Social media platforms"""

    INSTAGRAM = "instagram"
    FACEBOOK = "facebook"
    TWITTER = "twitter"
    TIKTOK = "tiktok"
    LINKEDIN = "linkedin"


class SocialThreadStatus(str, enum.Enum):
    """Social thread status"""

    OPEN = "open"
    PENDING = "pending"
    REPLIED = "replied"
    CLOSED = "closed"


class ReviewStatus(str, enum.Enum):
    """Review moderation status"""

    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    FLAGGED = "flagged"


class PricingTierLevel(str, enum.Enum):
    """Pricing tier levels"""

    STANDARD = "standard"
    PREMIUM = "premium"
    DELUXE = "deluxe"
    CUSTOM = "custom"


# ==================== MODELS ====================


class Booking(Base):
    """
    Core booking entity

    ⚠️ SCHEMA UPDATED (Nov 2025): Now matches actual database schema
    - Uses date/slot (not event_date/event_start_time)
    - Uses party_adults/party_kids (not guest_count)
    - Uses deposit_due_cents/total_due_cents (not deposit_amount/total_amount)
    - Uses address_encrypted/zone (not location fields)
    - Added: sms_consent, sms_consent_timestamp, version, hold_on_request
    - Added: customer_deposit_deadline, internal_deadline, deposit_confirmed_at
    """

    __tablename__ = "bookings"
    __table_args__ = (
        CheckConstraint("deposit_due_cents >= 0", name="check_deposit_non_negative"),
        CheckConstraint("party_adults > 0", name="check_party_adults_positive"),
        CheckConstraint("party_kids >= 0", name="check_party_kids_non_negative"),
        CheckConstraint("total_due_cents >= deposit_due_cents", name="check_total_gte_deposit"),
        ForeignKeyConstraint(
            ["chef_id"], ["core.chefs.id"], ondelete="SET NULL", name="bookings_chef_id_fkey"
        ),
        ForeignKeyConstraint(
            ["customer_id"],
            ["core.customers.id"],
            ondelete="RESTRICT",
            name="bookings_customer_id_fkey",
        ),
        ForeignKeyConstraint(
            ["station_id"],
            ["identity.stations.id"],
            ondelete="RESTRICT",
            name="fk_bookings_station",
        ),
        Index("idx_booking_date_slot_active", "date", "slot", "status", unique=True),
        Index("idx_booking_station_customer", "station_id", "customer_id"),
        Index("idx_booking_station_date", "station_id", "date", "slot"),
        Index("ix_bookings_customer_deposit_deadline", "customer_deposit_deadline", "status"),
        Index(
            "ix_bookings_internal_deadline",
            "internal_deadline",
            "status",
            "hold_on_request",
            "deposit_confirmed_at",
        ),
        Index("ix_bookings_sms_consent", "sms_consent"),
        Index("ix_core_bookings_chef_slot_unique", "chef_id", "date", "slot", unique=True),
        Index("ix_core_bookings_customer_id", "customer_id"),
        Index("ix_core_bookings_date_slot", "date", "slot"),
        Index("ix_core_bookings_status", "status"),
        {
            "schema": "core",
            "extend_existing": True,
        },  # Allow coexistence with legacy models.booking.Booking
    )

    # Primary Key
    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)

    # Foreign Keys (UPDATED - match database)
    customer_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), nullable=False)
    chef_id: Mapped[Optional[UUID]] = mapped_column(PGUUID(as_uuid=True), nullable=True)
    station_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), nullable=False)

    # Event Details (UPDATED - match database)
    date: Mapped[date] = mapped_column(Date, nullable=False)
    slot: Mapped[time] = mapped_column(Time, nullable=False)

    # Location (UPDATED - match database)
    address_encrypted: Mapped[str] = mapped_column(Text, nullable=False)
    zone: Mapped[str] = mapped_column(String(50), nullable=False)

    # Party Composition (UPDATED - match database)
    party_adults: Mapped[int] = mapped_column(Integer, nullable=False)
    party_kids: Mapped[int] = mapped_column(Integer, nullable=False)

    # Pricing (UPDATED - match database)
    deposit_due_cents: Mapped[int] = mapped_column(Integer, nullable=False)
    total_due_cents: Mapped[int] = mapped_column(Integer, nullable=False)

    # Status
    status: Mapped[BookingStatus] = mapped_column(
        SQLEnum(
            BookingStatus,
            name="booking_status",
            schema="public",
            create_type=False,
            values_callable=lambda x: [e.value for e in x],
        ),
        nullable=False,
        index=True,
    )

    # Source tracking
    source: Mapped[str] = mapped_column(String(50), nullable=False)

    # TCPA Compliance (NEW - from database)
    sms_consent: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text("false"))
    sms_consent_timestamp: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    # Optimistic Locking (NEW - Bug #13 fix)
    version: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text("1"))

    # Dual Deadline System (UPDATED - match database)
    customer_deposit_deadline: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    internal_deadline: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    deposit_deadline: Mapped[Optional[datetime]] = mapped_column(
        DateTime, nullable=True
    )  # Legacy compatibility

    # Manual Deposit Confirmation (NEW - from database)
    deposit_confirmed_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    deposit_confirmed_by: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    # Admin Hold System (NEW - from database)
    hold_on_request: Mapped[bool] = mapped_column(
        Boolean, nullable=False, server_default=text("false")
    )
    held_by: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    held_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    hold_reason: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Menu & Notes (UPDATED - match database)
    menu_items: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)
    special_requests: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Metadata
    booking_metadata: Mapped[Optional[dict]] = mapped_column("metadata", JSONB, nullable=True)

    # Soft Delete
    deleted_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now()
    )

    # Relationships
    customer: Mapped["Customer"] = relationship("Customer", back_populates="bookings")
    chef: Mapped[Optional["Chef"]] = relationship("Chef", back_populates="bookings")
    reminders: Mapped[List["BookingReminder"]] = relationship(
        "BookingReminder", back_populates="booking", lazy="select", cascade="all, delete-orphan"
    )
    payments: Mapped[List["Payment"]] = relationship(
        "Payment", back_populates="booking", lazy="select", cascade="all, delete-orphan"
    )
    # reminders: Mapped[list["BookingReminder"]] = relationship("BookingReminder", back_populates="booking", lazy="select", cascade="all, delete-orphan")  # Commented: BookingReminder not in db.models yet


class Customer(Base):
    """
    Customer entity

    Represents a customer with contact info, preferences, and booking history.

    ⚠️ SCHEMA UPDATED (Nov 2025): Now matches actual database schema
    - Uses email_encrypted/phone_encrypted (with @property helpers for backward compatibility)
    - Uses consent_sms/consent_email (not marketing_consent)
    - station_id is NOT NULL (required)
    - Added: timezone, tags, notes, deleted_at, consent_updated_at
    """

    __tablename__ = "customers"
    __table_args__ = (
        ForeignKeyConstraint(
            ["station_id"],
            ["identity.stations.id"],
            ondelete="RESTRICT",
            name="fk_customers_station",
        ),
        Index("idx_customer_station_email", "station_id", "email_encrypted", unique=True),
        Index("idx_customer_station_created", "station_id", "created_at"),
        Index("ix_core_customers_email_active", "email_encrypted", unique=True),
        {"schema": "core"},
    )

    # Primary Key
    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)

    # Foreign Keys (REQUIRED - NOT NULL)
    station_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), nullable=False)

    # Contact Info (ENCRYPTED FIELDS - match database schema)
    first_name: Mapped[str] = mapped_column(String(100), nullable=False)
    last_name: Mapped[str] = mapped_column(String(100), nullable=False)
    email_encrypted: Mapped[str] = mapped_column(Text, nullable=False)
    phone_encrypted: Mapped[str] = mapped_column(Text, nullable=False)

    # Consent fields (match database schema)
    consent_sms: Mapped[bool] = mapped_column(Boolean, nullable=False)
    consent_email: Mapped[bool] = mapped_column(Boolean, nullable=False)
    consent_updated_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))

    # Customer metadata
    timezone: Mapped[str] = mapped_column(String(50), nullable=False)
    tags: Mapped[Optional[List[str]]] = mapped_column(ARRAY(String(50)))
    notes: Mapped[Optional[str]] = mapped_column(Text)

    # Soft delete
    deleted_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now()
    )

    # Relationships
    bookings: Mapped[List["Booking"]] = relationship("Booking", back_populates="customer")
    message_threads: Mapped[List["MessageThread"]] = relationship(
        "MessageThread", back_populates="customer"
    )

    # ==================== BACKWARD COMPATIBILITY HELPERS ====================
    # These @property decorators allow existing code to use customer.email/customer.phone
    # while the database stores encrypted values

    @property
    def email(self) -> str:
        """
        Decrypt and return email (backward compatibility)

        Uses core/encryption.py with passthrough mode for gradual migration.
        If FIELD_ENCRYPTION_KEY not set, returns plaintext (safe for migration).
        """
        from core.encryption import decrypt_email

        return decrypt_email(self.email_encrypted)

    @email.setter
    def email(self, value: str):
        """
        Encrypt and store email (backward compatibility)

        Uses core/encryption.py with passthrough mode for gradual migration.
        If FIELD_ENCRYPTION_KEY not set, stores plaintext (safe for migration).
        """
        from core.encryption import encrypt_email

        self.email_encrypted = encrypt_email(value)

    @property
    def phone(self) -> str:
        """
        Decrypt and return phone (backward compatibility)

        Uses core/encryption.py with passthrough mode for gradual migration.
        """
        from core.encryption import decrypt_phone

        return decrypt_phone(self.phone_encrypted)

    @phone.setter
    def phone(self, value: str):
        """
        Encrypt and store phone (backward compatibility)

        Uses core/encryption.py with passthrough mode for gradual migration.
        """
        from core.encryption import encrypt_phone

        self.phone_encrypted = encrypt_phone(value)


class Chef(Base):
    """
    Chef entity

    Represents a hibachi chef with skills, availability, and assignments.
    """

    __tablename__ = "chefs"
    __table_args__ = (
        Index("idx_chefs_email", "email"),
        Index("idx_chefs_phone", "phone"),
        Index("idx_chefs_active", "is_active"),
        {"schema": "core"},
    )

    # Primary Key
    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)

    # Personal Info
    first_name: Mapped[str] = mapped_column(String(100), nullable=False)
    last_name: Mapped[str] = mapped_column(String(100), nullable=False)
    email: Mapped[str] = mapped_column(String(255), nullable=False, unique=True, index=True)
    phone: Mapped[str] = mapped_column(String(20), nullable=False, index=True)

    # Professional Info
    bio: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    specialties: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    years_experience: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    # Status
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True, index=True)

    # Metadata
    chef_metadata: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now()
    )

    # Relationships
    bookings: Mapped[List["Booking"]] = relationship("Booking", back_populates="chef")


# ==================== BOOKING REMINDERS ====================


class ReminderType(str, enum.Enum):
    """Types of booking reminders"""

    EMAIL = "email"
    SMS = "sms"
    BOTH = "both"


class ReminderStatus(str, enum.Enum):
    """Status of reminder delivery"""

    PENDING = "pending"
    SENT = "sent"
    FAILED = "failed"
    CANCELLED = "cancelled"


class BookingReminder(Base):
    """
    Booking reminder entity

    Stores scheduled reminders for bookings (email/SMS).
    Integrates with Celery for async sending.
    """

    __tablename__ = "booking_reminders"
    __table_args__ = (
        Index("idx_booking_reminders_booking_id", "booking_id"),
        Index("idx_booking_reminders_status", "status"),
        Index("idx_booking_reminders_scheduled_for", "scheduled_for"),
        {"schema": "core", "extend_existing": True},
    )

    # Primary Key
    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)

    # Foreign Keys
    booking_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("core.bookings.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Reminder Details
    reminder_type: Mapped[ReminderType] = mapped_column(
        SQLEnum(ReminderType, name="reminder_type", schema="public", create_type=False),
        nullable=False,
    )
    scheduled_for: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, index=True
    )
    sent_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    # Status
    status: Mapped[ReminderStatus] = mapped_column(
        SQLEnum(ReminderStatus, name="reminder_status", schema="public", create_type=False),
        nullable=False,
        default=ReminderStatus.PENDING,
        index=True,
    )

    # Content
    message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now()
    )

    # Relationships
    booking: Mapped["Booking"] = relationship("Booking", back_populates="reminders")


# ==================== PAYMENTS ====================


class PaymentStatus(str, enum.Enum):
    """Payment status workflow"""

    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    REFUNDED = "refunded"
    PARTIALLY_REFUNDED = "partially_refunded"


class PaymentType(str, enum.Enum):
    """Payment types"""

    DEPOSIT = "deposit"
    FULL_PAYMENT = "full_payment"
    PARTIAL_PAYMENT = "partial_payment"
    REFUND = "refund"


class Payment(Base):
    """
    Payment entity

    Tracks all payments and refunds for bookings.
    Integrates with Stripe for payment processing.
    """

    __tablename__ = "payments"
    __table_args__ = (
        Index("idx_payments_booking_id", "booking_id"),
        Index("idx_payments_status", "status"),
        Index("idx_payments_stripe_payment_intent_id", "stripe_payment_intent_id"),
        Index("idx_payments_created_at", "created_at"),
        {"schema": "core", "extend_existing": True},
    )

    # Primary Key
    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)

    # Foreign Keys
    booking_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("core.bookings.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Stripe Integration
    stripe_payment_intent_id: Mapped[Optional[str]] = mapped_column(
        String(255), nullable=True, unique=True, index=True
    )
    stripe_customer_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    stripe_charge_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    # Payment Details
    amount: Mapped[int] = mapped_column(Integer, nullable=False)  # Amount in cents
    currency: Mapped[str] = mapped_column(String(3), nullable=False, default="usd")
    payment_type: Mapped[PaymentType] = mapped_column(
        SQLEnum(PaymentType, name="payment_type", schema="public", create_type=False),
        nullable=False,
    )

    # Status
    status: Mapped[PaymentStatus] = mapped_column(
        SQLEnum(PaymentStatus, name="payment_status", schema="public", create_type=False),
        nullable=False,
        default=PaymentStatus.PENDING,
        index=True,
    )

    # Metadata
    payment_method: Mapped[Optional[str]] = mapped_column(
        String(50), nullable=True
    )  # card, bank_transfer, etc.
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Refund Details (if applicable)
    refunded_amount: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    refund_reason: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), index=True
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now()
    )
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    # Relationships
    booking: Mapped["Booking"] = relationship("Booking", back_populates="payments")


class MessageThread(Base):
    """
    Message thread entity

    Groups messages by customer and context (booking, support, etc.).
    """

    __tablename__ = "message_threads"
    __table_args__ = (
        Index("idx_message_threads_customer_id", "customer_id"),
        Index("idx_message_threads_station_id", "station_id"),
        Index("idx_message_threads_status", "status"),
        Index("idx_message_threads_created_at", "created_at"),
        {"schema": "core"},
    )

    # Primary Key
    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)

    # Foreign Keys
    customer_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("core.customers.id"), nullable=False
    )
    station_id: Mapped[Optional[UUID]] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("identity.stations.id"), nullable=True
    )

    # Thread Details
    subject: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    channel: Mapped[MessageChannel] = mapped_column(
        SQLEnum(MessageChannel, name="message_channel", schema="public", create_type=False),
        nullable=False,
        default=MessageChannel.WEB_CHAT,
    )
    status: Mapped[ThreadStatus] = mapped_column(
        SQLEnum(ThreadStatus, name="thread_status", schema="public", create_type=False),
        nullable=False,
        default=ThreadStatus.ACTIVE,
        index=True,
    )

    # Metadata
    thread_metadata: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now()
    )
    last_message_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    # Relationships
    customer: Mapped["Customer"] = relationship("Customer", back_populates="message_threads")
    messages: Mapped[List["CoreMessage"]] = relationship(
        "CoreMessage", back_populates="thread", cascade="all, delete-orphan"
    )


class CoreMessage(Base):
    """
    Individual message entity

    Represents a single message in a thread.
    """

    __tablename__ = "messages"
    __table_args__ = (
        Index("idx_messages_thread_id", "thread_id"),
        Index("idx_messages_created_at", "created_at"),
        {"schema": "core"},
    )

    # Primary Key
    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)

    # Foreign Keys
    thread_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("core.message_threads.id"), nullable=False
    )

    # Message Details
    sender_type: Mapped[str] = mapped_column(
        String(50), nullable=False
    )  # 'customer', 'staff', 'system', 'ai'
    sender_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    is_read: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    # Metadata
    message_metadata: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    # Relationships
    thread: Mapped["MessageThread"] = relationship("MessageThread", back_populates="messages")


class PricingTier(Base):
    """
    Pricing tier entity

    Defines pricing levels (standard, premium, deluxe, custom).
    """

    __tablename__ = "pricing_tiers"
    __table_args__ = (
        Index("idx_pricing_tiers_level", "level"),
        Index("idx_pricing_tiers_active", "is_active"),
        CheckConstraint("base_price >= 0", name="check_base_price_positive"),
        CheckConstraint("min_guests > 0", name="check_min_guests_positive"),
        CheckConstraint("max_guests >= min_guests", name="check_max_guests_valid"),
        {"schema": "core"},
    )

    # Primary Key
    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)

    # Tier Details
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    level: Mapped[PricingTierLevel] = mapped_column(
        SQLEnum(PricingTierLevel, name="pricing_tier_level", schema="public", create_type=False),
        nullable=False,
        index=True,
    )
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Pricing
    base_price: Mapped[int] = mapped_column(Integer, nullable=False)  # cents
    price_per_guest: Mapped[int] = mapped_column(Integer, nullable=False)  # cents

    # Guest Limits
    min_guests: Mapped[int] = mapped_column(Integer, nullable=False)
    max_guests: Mapped[int] = mapped_column(Integer, nullable=False)

    # Status
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True, index=True)

    # Metadata
    tier_metadata: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now()
    )

    # Relationships
    # NOTE: Removed broken relationship - Booking model doesn't have pricing_tier_id FK
    # bookings: Mapped[List["Booking"]] = relationship("Booking", back_populates="pricing_tier")


class SocialThread(Base):
    """
    Social media thread entity

    Tracks conversations from social media platforms.
    """

    __tablename__ = "social_threads"
    __table_args__ = (
        Index("idx_social_threads_platform", "platform"),
        Index("idx_social_threads_status", "status"),
        Index("idx_social_threads_created_at", "created_at"),
        {"schema": "core"},
    )

    # Primary Key
    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)

    # Platform Info
    platform: Mapped[SocialPlatform] = mapped_column(
        SQLEnum(SocialPlatform, name="social_platform", schema="public", create_type=False),
        nullable=False,
        index=True,
    )
    platform_thread_id: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)

    # Customer Info
    customer_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    customer_handle: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    # Thread Status
    status: Mapped[SocialThreadStatus] = mapped_column(
        SQLEnum(
            SocialThreadStatus, name="social_thread_status", schema="public", create_type=False
        ),
        nullable=False,
        default=SocialThreadStatus.OPEN,
        index=True,
    )

    # Metadata
    thread_metadata: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now()
    )
    last_message_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    # Relationships
    reviews: Mapped[List["Review"]] = relationship("Review", back_populates="thread")


class Review(Base):
    """
    Customer review entity

    Tracks reviews with moderation workflow.
    """

    __tablename__ = "reviews"
    __table_args__ = (
        Index("idx_reviews_thread_id", "thread_id"),
        Index("idx_reviews_status", "status"),
        Index("idx_reviews_rating", "rating"),
        CheckConstraint("rating >= 1 AND rating <= 5", name="check_rating_range"),
        {"schema": "core"},
    )

    # Primary Key
    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)

    # Foreign Keys
    thread_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("core.social_threads.id"), nullable=False
    )

    # Review Details
    rating: Mapped[int] = mapped_column(Integer, nullable=False)  # 1-5 stars
    review_text: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Moderation
    status: Mapped[ReviewStatus] = mapped_column(
        SQLEnum(ReviewStatus, name="review_status", schema="public", create_type=False),
        nullable=False,
        default=ReviewStatus.PENDING,
        index=True,
    )
    moderation_notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    moderated_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    # Relationships
    thread: Mapped["SocialThread"] = relationship("SocialThread", back_populates="reviews")
