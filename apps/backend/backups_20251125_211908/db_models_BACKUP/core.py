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

from datetime import datetime
from typing import Optional, List
from uuid import UUID, uuid4

from sqlalchemy import (
    Column, String, Text, Integer, BigInteger, Boolean, DateTime,
    ForeignKey, Index, CheckConstraint, UniqueConstraint, Enum as SQLEnum
)
from sqlalchemy.dialects.postgresql import UUID as PGUUID, JSONB
from sqlalchemy.orm import relationship, Mapped, mapped_column
from sqlalchemy.sql import func

from ..base_class import Base


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

    Represents a catering booking with customer, chef, pricing, and status.
    Uses deposit workflow with dual deadlines.
    """
    __tablename__ = "bookings"
    __table_args__ = (
        Index("idx_bookings_customer_id", "customer_id"),
        Index("idx_bookings_chef_id", "chef_id"),
        Index("idx_bookings_station_id", "station_id"),
        Index("idx_bookings_status", "status"),
        Index("idx_bookings_event_date", "event_date"),
        Index("idx_bookings_created_at", "created_at"),
        CheckConstraint("total_amount >= 0", name="check_total_amount_positive"),
        CheckConstraint("deposit_amount >= 0", name="check_deposit_amount_positive"),
        CheckConstraint("guest_count > 0", name="check_guest_count_positive"),
        {"schema": "core"}
    )

    # Primary Key
    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)

    # Foreign Keys
    customer_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("core.customers.id"), nullable=False)
    chef_id: Mapped[Optional[UUID]] = mapped_column(PGUUID(as_uuid=True), ForeignKey("core.chefs.id"), nullable=True)
    station_id: Mapped[Optional[UUID]] = mapped_column(PGUUID(as_uuid=True), ForeignKey("identity.stations.id"), nullable=True)
    pricing_tier_id: Mapped[Optional[UUID]] = mapped_column(PGUUID(as_uuid=True), ForeignKey("core.pricing_tiers.id"), nullable=True)

    # Booking Details
    event_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    event_start_time: Mapped[str] = mapped_column(String(10), nullable=False)  # HH:MM format
    event_end_time: Mapped[Optional[str]] = mapped_column(String(10), nullable=True)
    guest_count: Mapped[int] = mapped_column(Integer, nullable=False)
    event_type: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    special_requests: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Location
    location_address: Mapped[str] = mapped_column(String(255), nullable=False)
    location_city: Mapped[str] = mapped_column(String(100), nullable=False)
    location_state: Mapped[str] = mapped_column(String(50), nullable=False)
    location_zip: Mapped[str] = mapped_column(String(20), nullable=False)
    travel_fee: Mapped[Optional[float]] = mapped_column(Integer, nullable=True, default=0)  # cents

    # Pricing
    total_amount: Mapped[int] = mapped_column(Integer, nullable=False)  # cents
    deposit_amount: Mapped[int] = mapped_column(Integer, nullable=False)  # cents
    remaining_amount: Mapped[int] = mapped_column(Integer, nullable=False)  # cents

    # Status & Workflow
    status: Mapped[BookingStatus] = mapped_column(
        SQLEnum(BookingStatus, name="booking_status", schema="public", create_type=False),
        nullable=False,
        default=BookingStatus.PENDING,
        index=True
    )

    # Deposit Deadlines (Dual Deadline System)
    deposit_deadline: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    deposit_reminder_sent: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    deposit_paid_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    # Confirmation
    confirmed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    confirmation_sent_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    # Cancellation
    cancelled_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    cancellation_reason: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Metadata
    booking_metadata: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now()
    )

    # Relationships
    customer: Mapped["Customer"] = relationship("Customer", back_populates="bookings")
    chef: Mapped[Optional["Chef"]] = relationship("Chef", back_populates="bookings")
    pricing_tier: Mapped[Optional["PricingTier"]] = relationship("PricingTier", back_populates="bookings")


class Customer(Base):
    """
    Customer entity

    Represents a customer with contact info, preferences, and booking history.
    """
    __tablename__ = "customers"
    __table_args__ = (
        Index("idx_customers_email", "email"),
        Index("idx_customers_phone", "phone"),
        Index("idx_customers_station_id", "station_id"),
        Index("idx_customers_created_at", "created_at"),
        {"schema": "core"}
    )

    # Primary Key
    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)

    # Foreign Keys
    station_id: Mapped[Optional[UUID]] = mapped_column(PGUUID(as_uuid=True), ForeignKey("identity.stations.id"), nullable=True)

    # Contact Info
    first_name: Mapped[str] = mapped_column(String(100), nullable=False)
    last_name: Mapped[str] = mapped_column(String(100), nullable=False)
    email: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    phone: Mapped[str] = mapped_column(String(20), nullable=False, index=True)

    # Preferences
    preferred_contact_method: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    dietary_restrictions: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Marketing
    marketing_consent: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    # Metadata
    customer_metadata: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now()
    )

    # Relationships
    bookings: Mapped[List["Booking"]] = relationship("Booking", back_populates="customer")
    message_threads: Mapped[List["MessageThread"]] = relationship("MessageThread", back_populates="customer")


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
        {"schema": "core"}
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
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now()
    )

    # Relationships
    bookings: Mapped[List["Booking"]] = relationship("Booking", back_populates="chef")


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
        {"schema": "core"}
    )

    # Primary Key
    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)

    # Foreign Keys
    customer_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("core.customers.id"), nullable=False)
    station_id: Mapped[Optional[UUID]] = mapped_column(PGUUID(as_uuid=True), ForeignKey("identity.stations.id"), nullable=True)

    # Thread Details
    subject: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    channel: Mapped[MessageChannel] = mapped_column(
        SQLEnum(MessageChannel, name="message_channel", schema="public", create_type=False),
        nullable=False,
        default=MessageChannel.WEB_CHAT
    )
    status: Mapped[ThreadStatus] = mapped_column(
        SQLEnum(ThreadStatus, name="thread_status", schema="public", create_type=False),
        nullable=False,
        default=ThreadStatus.ACTIVE,
        index=True
    )

    # Metadata
    thread_metadata: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now()
    )
    last_message_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    # Relationships
    customer: Mapped["Customer"] = relationship("Customer", back_populates="message_threads")
    messages: Mapped[List["CoreMessage"]] = relationship("CoreMessage", back_populates="thread", cascade="all, delete-orphan")


class CoreMessage(Base):
    """
    Individual message entity

    Represents a single message in a thread.
    """
    __tablename__ = "messages"
    __table_args__ = (
        Index("idx_messages_thread_id", "thread_id"),
        Index("idx_messages_created_at", "created_at"),
        {"schema": "core"}
    )

    # Primary Key
    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)

    # Foreign Keys
    thread_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("core.message_threads.id"), nullable=False)

    # Message Details
    sender_type: Mapped[str] = mapped_column(String(50), nullable=False)  # 'customer', 'staff', 'system', 'ai'
    sender_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    is_read: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    # Metadata
    message_metadata: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now()
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
        {"schema": "core"}
    )

    # Primary Key
    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)

    # Tier Details
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    level: Mapped[PricingTierLevel] = mapped_column(
        SQLEnum(PricingTierLevel, name="pricing_tier_level", schema="public", create_type=False),
        nullable=False,
        index=True
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
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now()
    )

    # Relationships
    bookings: Mapped[List["Booking"]] = relationship("Booking", back_populates="pricing_tier")


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
        {"schema": "core"}
    )

    # Primary Key
    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)

    # Platform Info
    platform: Mapped[SocialPlatform] = mapped_column(
        SQLEnum(SocialPlatform, name="social_platform", schema="public", create_type=False),
        nullable=False,
        index=True
    )
    platform_thread_id: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)

    # Customer Info
    customer_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    customer_handle: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    # Thread Status
    status: Mapped[SocialThreadStatus] = mapped_column(
        SQLEnum(SocialThreadStatus, name="social_thread_status", schema="public", create_type=False),
        nullable=False,
        default=SocialThreadStatus.OPEN,
        index=True
    )

    # Metadata
    thread_metadata: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now()
    )
    last_message_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

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
        {"schema": "core"}
    )

    # Primary Key
    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)

    # Foreign Keys
    thread_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("core.social_threads.id"), nullable=False)

    # Review Details
    rating: Mapped[int] = mapped_column(Integer, nullable=False)  # 1-5 stars
    review_text: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Moderation
    status: Mapped[ReviewStatus] = mapped_column(
        SQLEnum(ReviewStatus, name="review_status", schema="public", create_type=False),
        nullable=False,
        default=ReviewStatus.PENDING,
        index=True
    )
    moderation_notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now()
    )
    moderated_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    # Relationships
    thread: Mapped["SocialThread"] = relationship("SocialThread", back_populates="reviews")
