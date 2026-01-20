"""
Integration Schema Models - External Service Integration

This module contains SQLAlchemy models for the 'integra' schema, which handles
integration with external services:
- Payment providers (Stripe, Plaid)
- Communication platforms (RingCentral)
- Social media webhooks (Instagram, Facebook, etc.)

All models use SQLAlchemy 2.0 declarative mapping with type hints.
"""

from datetime import datetime
from decimal import Decimal
from enum import Enum as PyEnum
from typing import Optional
from uuid import UUID, uuid4

from sqlalchemy import (
    ARRAY,
    TIMESTAMP,
    Boolean,
    CheckConstraint,
    Enum,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    Text,
    text,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..base_class import Base

# ==========================================
# ENUMS (Type-Safe Constants)
# ==========================================


class PaymentProvider(str, PyEnum):
    """Payment provider sources.

    - stripe: Stripe payments (credit card)
    - manual: Manual entry (Venmo, Zelle)
    """

    STRIPE = "stripe"
    MANUAL = "manual"


class PaymentMethod(str, PyEnum):
    """Payment methods.

    - card: Credit/debit card (via Stripe)
    - venmo: Venmo payment
    - zelle: Zelle payment (FREE - no fees!)
    """

    CARD = "card"
    VENMO = "venmo"
    ZELLE = "zelle"


class MatchStatus(str, PyEnum):
    """Payment match status.

    - auto: Automatically matched by system
    - manual: Manually matched by admin
    - ignored: Marked as irrelevant/duplicate
    """

    AUTO = "auto"
    MANUAL = "manual"
    IGNORED = "ignored"


class CallDirection(str, PyEnum):
    """Call direction.

    - inbound: Customer called us
    - outbound: We called customer
    """

    INBOUND = "inbound"
    OUTBOUND = "outbound"


class SocialPlatform(str, PyEnum):
    """Social media platforms.

    - instagram: Instagram
    - facebook: Facebook
    - google_business: Google Business Profile
    - yelp: Yelp
    - tiktok: TikTok
    - twitter: Twitter/X
    """

    INSTAGRAM = "instagram"
    FACEBOOK = "facebook"
    GOOGLE_BUSINESS = "google_business"
    YELP = "yelp"
    TIKTOK = "tiktok"
    TWITTER = "twitter"


# ==========================================
# MODELS
# ==========================================


class PaymentEvent(Base):
    """Payment events from external providers (Stripe, Plaid, manual entry).

    Stores raw webhook data from payment providers. Used for:
    - Audit trail of all payment transactions
    - Reconciliation with bookings (via PaymentMatch)
    - Financial reporting
    - Duplicate detection (provider + provider_id unique)

    Business Rules:
    - amount_cents must be positive (CheckConstraint)
    - provider + provider_id must be unique (prevents duplicate webhooks)
    - currency defaults to USD
    - raw_data stores complete webhook payload (JSONB)

    Related Models:
    - PaymentMatch: Links this event to a Booking
    """

    __tablename__ = "payment_events"
    __table_args__ = (
        CheckConstraint("amount_cents > 0", name="check_payment_amount_positive"),
        Index(
            "ix_integra_payment_events_provider_id",
            "provider",
            "provider_id",
            unique=True,
        ),
        Index("ix_integra_payment_events_occurred", "occurred_at"),
        {"schema": "integra"},
    )

    # Primary key
    id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()"),
        comment="UUID primary key",
    )

    # Payment metadata
    provider: Mapped[PaymentProvider] = mapped_column(
        Enum(PaymentProvider, schema="integra", create_type=False),
        nullable=False,
        comment="Payment provider (stripe, plaid, manual)",
    )

    provider_id: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        comment="Provider's unique ID (e.g., Stripe charge ID, Plaid transaction ID)",
    )

    method: Mapped[PaymentMethod] = mapped_column(
        Enum(PaymentMethod, schema="integra", create_type=False),
        nullable=False,
        comment="Payment method (card, ach, venmo, zelle, cash, check)",
    )

    # Amount
    amount_cents: Mapped[int] = mapped_column(
        Integer, nullable=False, comment="Payment amount in cents (e.g., 5000 = $50.00)"
    )

    currency: Mapped[str] = mapped_column(
        String(3), nullable=False, default="USD", comment="Currency code (ISO 4217)"
    )

    # Timing
    occurred_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True),
        nullable=False,
        comment="When the payment occurred (provider timestamp)",
    )

    # Optional fields
    memo: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="Optional notes (e.g., check number, Venmo reference)",
    )

    # Raw webhook data
    raw_data: Mapped[dict] = mapped_column(
        JSONB, nullable=False, comment="Complete webhook payload from provider (JSON)"
    )

    # Audit
    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True),
        nullable=False,
        server_default="NOW()",
        comment="When this record was created in our system",
    )

    # Relationships
    matches: Mapped[list["PaymentMatch"]] = relationship(
        "PaymentMatch",
        back_populates="payment_event",
        cascade="all, delete-orphan",
        doc="Payment-to-booking matches (can match multiple bookings if split payment)",
    )


class PaymentMatch(Base):
    """Links PaymentEvents to Bookings with confidence scoring.

    Automated payment reconciliation system. Matches payments to bookings based on:
    - Amount matching
    - Customer email/phone matching
    - Timing (payment near booking date)
    - Reference numbers in memo field

    Business Rules:
    - confidence: 0.0 (no match) to 1.0 (perfect match)
    - status: auto (system matched), manual (admin confirmed), ignored (false positive)
    - High confidence matches (>0.9) auto-approve
    - Low confidence matches (<0.7) require manual review

    Related Models:
    - PaymentEvent: Source payment transaction
    - Booking: Target booking (core.bookings)
    """

    __tablename__ = "payment_matches"
    __table_args__ = (
        CheckConstraint(
            "confidence >= 0 AND confidence <= 1", name="check_confidence_range"
        ),
        CheckConstraint(
            "status IN ('auto', 'manual', 'ignored')", name="check_match_status"
        ),
        {"schema": "integra"},
    )

    # Primary key
    id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()"),
        comment="UUID primary key",
    )

    # Foreign keys
    payment_event_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("integra.payment_events.id", ondelete="CASCADE"),
        nullable=False,
        comment="Reference to payment_events table",
    )

    booking_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("core.bookings.id", ondelete="CASCADE"),
        nullable=False,
        comment="Reference to core.bookings table",
    )

    # Match quality
    confidence: Mapped[Decimal] = mapped_column(
        Numeric(3, 2),
        nullable=False,
        comment="Match confidence (0.00 to 1.00, e.g., 0.95 = 95% confident)",
    )

    match_method: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        comment="How the match was found (e.g., 'amount+email', 'amount+phone', 'memo_reference')",
    )

    status: Mapped[MatchStatus] = mapped_column(
        String(20),
        nullable=False,
        default="auto",
        comment="Match status (auto, manual, ignored)",
    )

    # Manual review
    reviewed_by: Mapped[Optional[UUID]] = mapped_column(
        PG_UUID(as_uuid=True),
        nullable=True,
        comment="User ID who reviewed this match (if status=manual)",
    )

    notes: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True, comment="Admin notes about this match"
    )

    # Audit
    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True),
        nullable=False,
        server_default="NOW()",
        comment="When this match was created",
    )

    # Relationships
    payment_event: Mapped["PaymentEvent"] = relationship(
        "PaymentEvent", back_populates="matches", doc="Source payment transaction"
    )

    # Note: Booking relationship defined in core.py (avoids circular import)


class CallSession(Base):
    """RingCentral call sessions with transcripts and outcomes.

    Tracks all phone calls (inbound/outbound) via RingCentral integration:
    - Customer service calls
    - Sales calls
    - Booking confirmations
    - Follow-ups

    Business Rules:
    - direction: inbound (customer called us) or outbound (we called customer)
    - duration_seconds: null if call not answered
    - transcript: AI-generated from recording (optional)
    - outcome: free-text summary (e.g., "booked", "rescheduled", "no_answer")
    - recording_url: S3/RingCentral link to call recording

    Related Models:
    - Booking: Associated booking (if call related to specific booking)
    - Customer: Who we talked to (core.customers)
    """

    __tablename__ = "call_sessions"
    __table_args__ = (
        CheckConstraint(
            "direction IN ('inbound', 'outbound')", name="check_call_direction"
        ),
        {"schema": "integra"},
    )

    # Primary key
    id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()"),
        comment="UUID primary key",
    )

    # Foreign keys (nullable - call may not link to booking/customer)
    booking_id: Mapped[Optional[UUID]] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("core.bookings.id", ondelete="SET NULL"),
        nullable=True,
        comment="Reference to core.bookings (if call related to a booking)",
    )

    customer_id: Mapped[Optional[UUID]] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("core.customers.id", ondelete="SET NULL"),
        nullable=True,
        comment="Reference to core.customers (if we identified the caller)",
    )

    # Call metadata
    direction: Mapped[CallDirection] = mapped_column(
        String(10), nullable=False, comment="Call direction (inbound or outbound)"
    )

    phone_number: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        comment="Customer's phone number (E.164 format, e.g., +14155551234)",
    )

    # Call details
    duration_seconds: Mapped[Optional[int]] = mapped_column(
        Integer,
        nullable=True,
        comment="Call duration in seconds (null if not answered)",
    )

    transcript: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True, comment="AI-generated transcript from recording (optional)"
    )

    outcome: Mapped[Optional[str]] = mapped_column(
        String(50),
        nullable=True,
        comment="Call outcome (e.g., 'booked', 'rescheduled', 'no_answer', 'voicemail')",
    )

    recording_url: Mapped[Optional[str]] = mapped_column(
        String(500), nullable=True, comment="URL to call recording (S3 or RingCentral)"
    )

    # RingCentral metadata
    ringcentral_call_id: Mapped[Optional[str]] = mapped_column(
        String(255), nullable=True, comment="RingCentral's unique call ID"
    )

    # Timing
    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True),
        nullable=False,
        server_default="NOW()",
        comment="When the call started",
    )

    ended_at: Mapped[Optional[datetime]] = mapped_column(
        TIMESTAMP(timezone=True), nullable=True, comment="When the call ended"
    )

    # Note: Relationships to Booking/Customer defined in core.py (avoids circular import)


class SocialInbox(Base):
    """Social media webhook inbox with idempotency and deduplication.

    Webhook receiver for social media platforms (Instagram, Facebook, etc.):
    - Prevents duplicate processing (signature primary key)
    - Tracks processing status and errors
    - Links to social accounts for routing

    Business Rules:
    - signature: Webhook signature (platform-specific, e.g., X-Hub-Signature)
    - payload_hash: SHA256 of payload for deduplication
    - processed: False until successfully handled
    - processing_attempts: Retry counter (max 3 attempts)
    - Idempotency: Same signature = skip processing

    Processing Flow:
    1. Webhook arrives → signature extracted
    2. Check if signature exists (idempotency)
    3. Compute payload_hash (detect duplicates)
    4. Store in social_inbox (processed=False)
    5. Background worker processes webhook
    6. Mark processed=True + processed_at timestamp
    7. If error: Increment processing_attempts, store last_error

    Related Models:
    - SocialAccount: Which business page received the webhook (core.social_accounts)
    """

    __tablename__ = "social_inbox"
    __table_args__ = (
        Index("ix_social_inbox_platform_received", "platform", "received_at"),
        {"schema": "integra"},
    )

    # Primary key (webhook signature for idempotency)
    signature: Mapped[str] = mapped_column(
        String(255),
        primary_key=True,
        comment="Webhook signature for idempotency (e.g., X-Hub-Signature, X-Webhook-Signature)",
    )

    # Webhook metadata
    platform: Mapped[SocialPlatform] = mapped_column(
        Enum(SocialPlatform, schema="integra", create_type=False),
        nullable=False,
        comment="Social media platform (instagram, facebook, google_business, yelp, tiktok, twitter)",
    )

    webhook_type: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        comment="Type of webhook event (e.g., 'messages', 'comments', 'mentions', 'reviews')",
    )

    # Account linkage
    account_id: Mapped[Optional[UUID]] = mapped_column(
        PG_UUID(as_uuid=True),
        nullable=True,
        comment="Reference to core.social_accounts (which business page)",
    )

    # Deduplication
    payload_hash: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
        comment="SHA256 hash of payload (for detecting duplicate webhooks)",
    )

    # Processing status
    processed: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        comment="Whether webhook has been successfully processed",
    )

    processing_attempts: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        comment="Number of processing attempts (max 3)",
    )

    last_error: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True, comment="Last error message (if processing failed)"
    )

    # Timing
    received_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True),
        nullable=False,
        server_default="NOW()",
        comment="When webhook was received",
    )

    processed_at: Mapped[Optional[datetime]] = mapped_column(
        TIMESTAMP(timezone=True),
        nullable=True,
        comment="When webhook was successfully processed",
    )

    # Note: Relationship to SocialAccount defined in core.py (avoids circular import)
