"""
SQLAlchemy Models - Lead Schema
================================

Lead management and social media integration:
- Leads (main lead tracking)
- LeadContact (multi-channel contact info)
- LeadContext (event/booking context)
- LeadEvent (event sourcing for lead actions)
- SocialAccount (connected business pages)
- SocialIdentity (customer social handles)
- SocialThread (social media conversations)

Business Logic:
- Lead scoring and qualification
- Multi-channel contact management
- Social media account integration
- Customer identity resolution
- Event sourcing for audit trail

All models use:
- UUID primary keys
- Timezone-aware datetime fields
- Schema qualification (__table_args__ = {"schema": "lead"})
- Proper foreign key relationships
- Type hints for IDE support
"""

from datetime import datetime, date
from typing import Optional, List
from uuid import UUID, uuid4
from decimal import Decimal

from sqlalchemy import (
    Column, String, Text, Integer, Float, Boolean, DateTime, Date, Numeric,
    ForeignKey, Index, CheckConstraint, UniqueConstraint, Enum as SQLEnum, ARRAY
)
from sqlalchemy.dialects.postgresql import UUID as PGUUID, JSONB
from sqlalchemy.orm import relationship, Mapped, mapped_column
from sqlalchemy.sql import func

from ..base_class import Base


# ==================== ENUMS ====================

import enum

class LeadSource(str, enum.Enum):
    """Where the lead came from"""
    WEB_QUOTE = "web_quote"
    CHAT = "chat"
    INSTAGRAM = "instagram"
    FACEBOOK = "facebook"
    GOOGLE = "google"
    YELP = "yelp"
    SMS = "sms"
    PHONE = "phone"
    REFERRAL = "referral"
    EVENT = "event"


class LeadStatus(str, enum.Enum):
    """Lead workflow status"""
    NEW = "new"
    WORKING = "working"
    QUALIFIED = "qualified"
    DISQUALIFIED = "disqualified"
    CONVERTED = "converted"
    NURTURING = "nurturing"


class LeadQuality(str, enum.Enum):
    """Lead temperature/quality"""
    HOT = "hot"
    WARM = "warm"
    COLD = "cold"


class ContactChannel(str, enum.Enum):
    """Contact method channels"""
    EMAIL = "email"
    SMS = "sms"
    INSTAGRAM = "instagram"
    FACEBOOK = "facebook"
    GOOGLE = "google"
    YELP = "yelp"
    WEB = "web"


class SocialPlatform(str, enum.Enum):
    """Social media platforms"""
    INSTAGRAM = "instagram"
    FACEBOOK = "facebook"
    GOOGLE = "google"
    YELP = "yelp"


class SocialThreadStatus(str, enum.Enum):
    """Social conversation status"""
    OPEN = "open"
    PENDING = "pending"
    RESOLVED = "resolved"


# ==================== MODELS ====================

class Lead(Base):
    """
    Lead tracking entity

    Represents a potential customer with scoring, qualification, and conversion tracking.
    Supports multi-channel attribution (UTM tracking).
    """
    __tablename__ = "leads"
    __table_args__ = (
        Index("ix_lead_leads_status", "status"),
        Index("ix_lead_leads_source", "source"),
        Index("ix_lead_leads_score", "score"),
        Index("ix_lead_leads_followup", "follow_up_date"),
        Index("ix_lead_leads_customer", "customer_id"),
        CheckConstraint("score >= 0 AND score <= 100", name="check_lead_score_range"),
        {"schema": "lead"}
    )

    # Primary Key
    id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        primary_key=True,
        server_default=func.gen_random_uuid()
    )

    # Source & Attribution
    source: Mapped[LeadSource] = mapped_column(
        SQLEnum(LeadSource, name="lead_source", schema="public", create_type=False),
        nullable=False
    )
    utm_source: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    utm_medium: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    utm_campaign: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)

    # Status & Quality
    status: Mapped[LeadStatus] = mapped_column(
        SQLEnum(LeadStatus, name="lead_status", schema="public", create_type=False),
        nullable=False,
        default=LeadStatus.NEW
    )
    quality: Mapped[Optional[LeadQuality]] = mapped_column(
        SQLEnum(LeadQuality, name="lead_quality", schema="public", create_type=False),
        nullable=True
    )
    score: Mapped[Decimal] = mapped_column(
        Numeric(5, 2),
        nullable=False,
        default=Decimal("0")
    )

    # Assignment
    assigned_to: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)

    # Customer Link (when converted)
    customer_id: Mapped[Optional[UUID]] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("core.customers.id", ondelete="SET NULL"),
        nullable=True
    )

    # Follow-up & Conversion
    last_contact_date: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True
    )
    follow_up_date: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True
    )
    conversion_date: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True
    )

    # Loss Tracking
    lost_reason: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

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
    deleted_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True
    )

    # Relationships
    contacts: Mapped[List["LeadContact"]] = relationship(
        "LeadContact",
        back_populates="lead",
        cascade="all, delete-orphan"
    )
    context: Mapped[Optional["LeadContext"]] = relationship(
        "LeadContext",
        back_populates="lead",
        uselist=False,
        cascade="all, delete-orphan"
    )
    events: Mapped[List["LeadEvent"]] = relationship(
        "LeadEvent",
        back_populates="lead",
        cascade="all, delete-orphan"
    )
    social_threads: Mapped[List["LeadSocialThread"]] = relationship(
        "LeadSocialThread",
        back_populates="lead"
    )


class LeadContact(Base):
    """
    Lead contact information

    Multi-channel contact methods for a lead (email, SMS, social, etc.).
    Supports verification status.
    """
    __tablename__ = "lead_contacts"
    __table_args__ = (
        Index("ix_lead_contacts_lead", "lead_id"),
        Index("ix_lead_contacts_channel", "channel", "handle_or_address"),
        {"schema": "lead"}
    )

    # Primary Key
    id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        primary_key=True,
        server_default=func.gen_random_uuid()
    )

    # Foreign Keys
    lead_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("lead.leads.id", ondelete="CASCADE"),
        nullable=False
    )

    # Contact Info
    channel: Mapped[ContactChannel] = mapped_column(
        SQLEnum(ContactChannel, name="contact_channel", schema="public", create_type=False),
        nullable=False
    )
    handle_or_address: Mapped[str] = mapped_column(Text, nullable=False)
    verified: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now()
    )

    # Relationships
    lead: Mapped["Lead"] = relationship("Lead", back_populates="contacts")


class LeadContext(Base):
    """
    Lead context and preferences

    Stores event details, budget, and preferences collected during lead capture.
    One-to-one with Lead.
    """
    __tablename__ = "lead_context"
    __table_args__ = (
        {"schema": "lead"}
    )

    # Primary Key (also FK to Lead)
    lead_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("lead.leads.id", ondelete="CASCADE"),
        primary_key=True
    )

    # Party Size
    party_size_adults: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    party_size_kids: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    # Budget
    estimated_budget_cents: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    # Event Date Preferences
    event_date_pref: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    event_date_range_start: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    event_date_range_end: Mapped[Optional[date]] = mapped_column(Date, nullable=True)

    # Location
    zip_code: Mapped[Optional[str]] = mapped_column(String(10), nullable=True)

    # Service Type
    service_type: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)

    # Notes
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Timestamps
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now()
    )

    # Relationships
    lead: Mapped["Lead"] = relationship("Lead", back_populates="context")


class LeadEvent(Base):
    """
    Lead event sourcing

    Tracks all actions/events related to a lead for audit trail and analytics.
    Event sourcing pattern for lead lifecycle.
    """
    __tablename__ = "lead_events"
    __table_args__ = (
        Index("ix_lead_events_lead", "lead_id", "occurred_at"),
        {"schema": "lead"}
    )

    # Primary Key
    id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        primary_key=True,
        server_default=func.gen_random_uuid()
    )

    # Foreign Keys
    lead_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("lead.leads.id", ondelete="CASCADE"),
        nullable=False
    )

    # Event Details
    type: Mapped[str] = mapped_column(String(50), nullable=False)
    payload: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)

    # Timestamp
    occurred_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now()
    )

    # Relationships
    lead: Mapped["Lead"] = relationship("Lead", back_populates="events")


class BusinessSocialAccount(Base):
    """
    Connected social media business account

    Represents a business's social media page/account (Instagram, Facebook, etc.).
    Used for admin panel social media management and lead generation.
    Different from identity.OAuthAccount (user authentication).
    """
    __tablename__ = "social_accounts"
    __table_args__ = (
        Index("ix_social_accounts_platform_page_id", "platform", "page_id", unique=True),
        Index("ix_social_accounts_platform", "platform"),
        Index("ix_social_accounts_is_active", "is_active"),
        {"schema": "lead"}
    )

    # Primary Key
    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)

    # Platform Info
    platform: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        comment="Social media platform (instagram, facebook, etc.)"
    )
    page_id: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        comment="Platform-specific page/business ID"
    )
    page_name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        comment="Display name of the business page"
    )
    handle: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
        comment="@username or handle if applicable"
    )

    # Profile
    profile_url: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    avatar_url: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Connection
    connected_by: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        nullable=False,
        comment="User ID who connected this account"
    )
    connected_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now()
    )

    # Security
    token_ref: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="Encrypted reference to access tokens (do not store plaintext tokens)"
    )
    webhook_verified: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        comment="Whether webhook subscription is verified"
    )

    # Sync
    last_sync_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment="Last successful sync with platform API"
    )

    # Status
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
        comment="Whether account is currently active"
    )

    # Metadata
    platform_metadata: Mapped[Optional[dict]] = mapped_column(
        JSONB,
        nullable=True,
        comment="Platform-specific settings, capabilities, and metadata"
    )

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
    deleted_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment="Soft delete timestamp"
    )


class SocialIdentity(Base):
    """
    Customer social media identity

    Maps social media handles to customers for identity resolution.
    Supports confidence scoring and verification workflow.
    """
    __tablename__ = "social_identities"
    __table_args__ = (
        Index("ix_social_identities_platform_handle", "platform", "handle", unique=True),
        Index("ix_social_identities_platform", "platform"),
        Index("ix_social_identities_customer_id", "customer_id"),
        {"schema": "lead"}
    )

    # Primary Key
    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)

    # Platform Info
    platform: Mapped[str] = mapped_column(String(50), nullable=False)
    handle: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        comment="Social handle without @ prefix"
    )
    display_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    # Profile
    profile_url: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    avatar_url: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Customer Mapping
    customer_id: Mapped[Optional[UUID]] = mapped_column(
        PGUUID(as_uuid=True),
        nullable=True,
        comment="Link to known customer (soft reference)"
    )
    confidence_score: Mapped[float] = mapped_column(
        Float,
        nullable=False,
        default=1.0,
        comment="Confidence in customer mapping (0.0 to 1.0)"
    )
    verification_status: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="unverified",
        comment="Verification status: unverified, pending, verified, rejected"
    )

    # Activity
    first_seen_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        comment="When this identity was first detected"
    )
    last_active_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment="Last interaction timestamp"
    )

    # Metadata
    platform_metadata: Mapped[Optional[dict]] = mapped_column(
        JSONB,
        nullable=True,
        comment="Platform-specific profile data"
    )

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


class LeadSocialThread(Base):
    """
    Social media conversation thread (Lead schema)

    Tracks conversations from social platforms, linked to leads or customers.
    Separate from core.social_threads to maintain lead-specific context.
    """
    __tablename__ = "social_threads"
    __table_args__ = (
        Index("ix_social_threads_platform", "platform", "thread_ref", unique=True),
        Index("ix_social_threads_lead", "lead_id"),
        Index("ix_social_threads_customer", "customer_id"),
        {"schema": "lead"}
    )

    # Primary Key
    id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        primary_key=True,
        server_default=func.gen_random_uuid()
    )

    # Platform Info
    platform: Mapped[SocialPlatform] = mapped_column(
        SQLEnum(SocialPlatform, name="social_platform", schema="public", create_type=False),
        nullable=False
    )
    account_id: Mapped[str] = mapped_column(String(100), nullable=False)
    thread_ref: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        comment="Platform-specific thread/conversation ID"
    )

    # Entity Links
    lead_id: Mapped[Optional[UUID]] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("lead.leads.id", ondelete="SET NULL"),
        nullable=True
    )
    customer_id: Mapped[Optional[UUID]] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("core.customers.id", ondelete="SET NULL"),
        nullable=True
    )

    # Status
    status: Mapped[SocialThreadStatus] = mapped_column(
        SQLEnum(SocialThreadStatus, name="thread_status", schema="public", create_type=False),
        nullable=False,
        default=SocialThreadStatus.OPEN
    )

    # Activity
    last_message_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True
    )

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now()
    )

    # Relationships
    lead: Mapped[Optional["Lead"]] = relationship("Lead", back_populates="social_threads")
