"""
Social Media & Review Models

Enterprise-grade social media conversation tracking and review management with:
- Multi-platform social account management
- Social identity mapping to customers
- Multi-platform social thread tracking
- Lead conversion from social conversations
- Customer review management
- Discount coupon tracking
"""

from datetime import datetime
from typing import Optional
import uuid

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Enum,
    Float,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    Text,
)
from sqlalchemy.dialects.postgresql import ARRAY, JSONB, UUID as PostgresUUID
from sqlalchemy.orm import relationship

from models.base import BaseModel
from models.enums import (
    MessageDirection,
    MessageKind,
    ReviewSource,
    ReviewStatus,
    SocialPlatform,
    ThreadStatus,
)


# ============================================================================
# SOCIAL ACCOUNT MANAGEMENT
# ============================================================================


class SocialAccount(BaseModel):
    """
    Connected social media business accounts/pages.
    
    Represents authenticated business accounts (Instagram Business, Facebook Page, etc.)
    that the restaurant uses to engage with customers.
    
    Features:
    - Multi-platform support (Instagram, Facebook, Google Business, Yelp)
    - Secure token storage (encrypted references)
    - Webhook verification status
    - Last sync tracking
    - Soft delete support
    """

    __tablename__ = "social_accounts"
    __table_args__ = (
        Index("ix_social_accounts_platform_page_id", "platform", "page_id", unique=True),
        Index("ix_social_accounts_is_active", "is_active"),
        {"schema": "lead", "extend_existing": True},
    )

    id = Column(PostgresUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Platform identification
    platform = Column(
        Enum(SocialPlatform, name='social_platform', create_type=False),
        nullable=False,
        index=True,
        comment="Social media platform (instagram, facebook, etc.)"
    )
    page_id = Column(
        String(255),
        nullable=False,
        comment="Platform-specific page/business ID"
    )
    page_name = Column(
        String(255),
        nullable=False,
        comment="Display name of the business page"
    )
    handle = Column(
        String(100),
        nullable=True,
        comment="@username or handle if applicable"
    )
    
    # Profile information
    profile_url = Column(Text, nullable=True)
    avatar_url = Column(Text, nullable=True)
    
    # Connection metadata
    connected_by = Column(
        PostgresUUID(as_uuid=True),
        nullable=False,
        comment="User ID who connected this account"
    )
    connected_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)
    
    # Security & authentication
    token_ref = Column(
        Text,
        nullable=True,
        comment="Encrypted reference to access tokens (do not store plaintext tokens)"
    )
    webhook_verified = Column(
        Boolean,
        default=False,
        nullable=False,
        comment="Whether webhook subscription is verified"
    )
    
    # Sync tracking
    last_sync_at = Column(
        DateTime(timezone=True),
        nullable=True,
        comment="Last successful sync with platform API"
    )
    
    # Status
    is_active = Column(
        Boolean,
        default=True,
        nullable=False,
        index=True,
        comment="Whether account is currently active"
    )
    
    # Platform-specific configuration
    platform_metadata = Column(
        JSONB,
        nullable=True,
        default=dict,
        comment="Platform-specific settings, capabilities, and metadata"
    )
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)
    updated_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=datetime.utcnow,
        onupdate=datetime.utcnow
    )
    deleted_at = Column(
        DateTime(timezone=True),
        nullable=True,
        comment="Soft delete timestamp"
    )
    
    # Relationships
    threads = relationship(
        "SocialThread",
        back_populates="account",
        cascade="all, delete-orphan",
        passive_deletes=True
    )
    reviews = relationship(
        "Review",
        back_populates="account",
        cascade="all, delete-orphan",
        passive_deletes=True
    )

    def __repr__(self) -> str:
        return f"<SocialAccount(platform={self.platform}, page_name={self.page_name})>"


class SocialIdentity(BaseModel):
    """
    Social media identities mapped to customers.
    
    Links social media handles to known customers for personalized engagement.
    Tracks confidence scores for automated customer matching.
    
    Features:
    - Multi-platform identity tracking
    - Customer mapping with confidence scores
    - Verification status
    - Activity tracking
    - Profile metadata
    """

    __tablename__ = "social_identities"
    __table_args__ = (
        Index("ix_social_identities_platform_handle", "platform", "handle", unique=True),
        Index("ix_social_identities_customer_id", "customer_id"),
        {"schema": "lead", "extend_existing": True},
    )

    id = Column(PostgresUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Platform & identity
    platform = Column(
        Enum(SocialPlatform, name='social_platform', create_type=False),
        nullable=False,
        index=True
    )
    handle = Column(
        String(100),
        nullable=False,
        comment="Social handle without @ prefix"
    )
    display_name = Column(String(255), nullable=True)
    
    # Profile information
    profile_url = Column(Text, nullable=True)
    avatar_url = Column(Text, nullable=True)
    
    # Customer mapping
    customer_id = Column(
        PostgresUUID(as_uuid=True),
        nullable=True,
        index=True,
        comment="Link to known customer (soft reference)"
    )
    confidence_score = Column(
        Float,
        default=1.0,
        nullable=False,
        comment="Confidence in customer mapping (0.0 to 1.0)"
    )
    verification_status = Column(
        String(50),
        default="unverified",
        nullable=False,
        comment="Verification status: unverified, pending, verified, rejected"
    )
    
    # Activity tracking
    first_seen_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=datetime.utcnow,
        comment="When this identity was first detected"
    )
    last_active_at = Column(
        DateTime(timezone=True),
        nullable=True,
        comment="Last interaction timestamp"
    )
    
    # Platform-specific data
    platform_metadata = Column(
        JSONB,
        nullable=True,
        default=dict,
        comment="Platform-specific profile data"
    )
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)
    updated_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=datetime.utcnow,
        onupdate=datetime.utcnow
    )
    
    # Relationships
    threads = relationship(
        "SocialThread",
        back_populates="social_identity",
        cascade="all, delete-orphan",
        passive_deletes=True
    )

    def __repr__(self) -> str:
        return f"<SocialIdentity(platform={self.platform}, handle=@{self.handle})>"


# ============================================================================
# SOCIAL CONVERSATIONS
# ============================================================================


class SocialThread(BaseModel):
    """Social media conversation tracking."""

    __tablename__ = "social_threads"
    __table_args__ = (
        Index("ix_social_threads_platform", "platform", "thread_external_id", unique=True),
        Index("ix_social_threads_account_id", "account_id"),
        Index("ix_social_threads_status", "status"),
        Index("ix_social_threads_assigned_to", "assigned_to"),
        {"schema": "lead", "extend_existing": True},
    )

    id = Column(PostgresUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    platform = Column(Enum(SocialPlatform, name='social_platform', create_type=False), nullable=False, index=True)
    thread_external_id = Column(String(255), nullable=False)  # External platform thread ID
    thread_ref = Column(String(255), nullable=True)  # Alternative reference field for compatibility
    
    # Foreign keys
    account_id = Column(
        PostgresUUID(as_uuid=True),
        ForeignKey("lead.social_accounts.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="Connected social account"
    )
    social_identity_id = Column(
        PostgresUUID(as_uuid=True),
        ForeignKey("lead.social_identities.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
        comment="Social identity of the person messaging us"
    )
    
    # Soft references (validated at application level)
    lead_id = Column(
        PostgresUUID(as_uuid=True),
        nullable=True,
        index=True,
        comment="Soft reference to lead (validated at application level)",
    )
    customer_id = Column(
        PostgresUUID(as_uuid=True),
        nullable=True,
        index=True,
        comment="Soft reference to customer (validated at application level)",
    )
    assigned_to = Column(
        PostgresUUID(as_uuid=True),
        nullable=True,
        index=True,
        comment="Assigned team member (soft reference to user)"
    )

    # Thread management
    status = Column(Enum(ThreadStatus, name='thread_status', create_type=False), nullable=False, default=ThreadStatus.OPEN, index=True)
    priority = Column(Integer, default=3, nullable=False, comment="1=urgent, 5=low")
    subject = Column(String(255), nullable=True, comment="Thread subject or first message preview")
    context_url = Column(Text, nullable=True, comment="Link to original post/content")
    customer_handle = Column(String(255), nullable=True)  # Customer's display name/handle
    message_count = Column(Integer, nullable=False, default=0)
    unread_count = Column(Integer, nullable=False, default=0)
    last_message_at = Column(DateTime(timezone=True), nullable=True)
    last_response_at = Column(DateTime(timezone=True), nullable=True, comment="Last time we responded")
    closed_at = Column(DateTime(timezone=True), nullable=True)
    resolved_at = Column(DateTime(timezone=True), nullable=True)
    tags = Column(ARRAY(String(50)), nullable=True, comment="Categorization tags")

    # Platform-specific data
    platform_metadata = Column(JSONB, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)
    updated_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=datetime.utcnow,
        onupdate=datetime.utcnow
    )
    
    # Relationships
    account = relationship(
        "SocialAccount",
        back_populates="threads"
    )
    social_identity = relationship(
        "SocialIdentity",
        back_populates="threads"
    )
    messages = relationship(
        "SocialMessage",
        back_populates="thread",
        cascade="all, delete-orphan",
        order_by="SocialMessage.sent_at"
    )

    def __repr__(self):
        return f"<SocialThread {self.platform.value} {self.thread_external_id} {self.status.value}>"


class SocialMessage(BaseModel):
    """Individual messages within social threads."""

    __tablename__ = "social_messages"
    __table_args__ = (
        Index("ix_social_messages_thread_id", "thread_id"),
        Index("ix_social_messages_sent_at", "sent_at"),
        {"schema": "lead", "extend_existing": True},
    )

    id = Column(PostgresUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    thread_id = Column(
        PostgresUUID(as_uuid=True),
        ForeignKey("lead.social_threads.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    message_external_id = Column(String(255), nullable=True, unique=True, comment="Platform-specific message ID")
    message_ref = Column(String(255), nullable=True, comment="Alternative message reference")
    
    # Message content
    direction = Column(
        Enum(MessageDirection, name='message_direction', create_type=False),
        nullable=False,
        comment="IN (from customer) or OUT (from business)"
    )
    kind = Column(
        Enum(MessageKind, name='message_kind', create_type=False),
        nullable=False,
        comment="Type of message: DM, comment, review, etc."
    )
    content = Column(Text, nullable=False)
    
    # Sender information
    sender_handle = Column(String(255), nullable=False)
    author_handle = Column(String(100), nullable=True, comment="Alternative author field")
    author_name = Column(String(255), nullable=True)
    is_from_customer = Column(Boolean, nullable=False, default=True)
    
    # Media attachments
    media = Column(JSONB, nullable=True, comment="Attachments, images, videos")
    
    # AI analysis
    sentiment_score = Column(
        Float,
        nullable=True,
        comment="AI sentiment analysis -1 (negative) to 1 (positive)"
    )
    intent_tags = Column(
        ARRAY(String(50)),
        nullable=True,
        comment="Detected intents: booking, complaint, question, etc."
    )
    
    # Timestamps
    sent_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(datetime.now().astimezone().tzinfo))
    read_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)
    
    # Platform-specific data
    extra_data = Column(JSONB, nullable=True, comment="Message metadata and platform-specific data")
    
    # Relationships
    thread = relationship(
        "SocialThread",
        back_populates="messages"
    )

    def __repr__(self):
        sender_type = "Customer" if self.is_from_customer else "Business"
        return f"<SocialMessage {sender_type} at {self.sent_at}>"


class Review(BaseModel):
    """Customer review from various platforms."""

    __tablename__ = "reviews"
    __table_args__ = (
        Index("ix_reviews_source", "source"),
        Index("ix_reviews_rating", "rating"),
        Index("ix_reviews_customer_id", "customer_id"),
        {"schema": "public", "extend_existing": True},
    )

    id = Column(PostgresUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Foreign keys
    account_id = Column(
        PostgresUUID(as_uuid=True),
        ForeignKey("lead.social_accounts.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
        comment="Social account where review was posted (if applicable)"
    )
    
    # Soft references
    customer_id = Column(
        PostgresUUID(as_uuid=True),
        nullable=True,
        index=True,
        comment="Soft reference to customer (validated at application level)",
    )
    booking_id = Column(
        PostgresUUID(as_uuid=True),
        nullable=True,
        index=True,
        comment="Soft reference to booking (validated at application level)",
    )
    
    source = Column(Enum(ReviewSource, name='review_source', create_type=False), nullable=False, index=True)
    status = Column(
        Enum(ReviewStatus, name='review_status', create_type=False),
        nullable=False,
        default=ReviewStatus.NEW,
        index=True
    )
    rating = Column(Integer, nullable=False)
    title = Column(String(200), nullable=True)
    content = Column(Text, nullable=False)
    reviewer_name = Column(String(200), nullable=True)
    reviewer_email = Column(String(255), nullable=True)
    
    verified = Column(Boolean, nullable=False, default=False)
    published = Column(Boolean, nullable=False, default=False)
    featured = Column(Boolean, nullable=False, default=False)
    
    review_date = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(datetime.now().astimezone().tzinfo))
    published_at = Column(DateTime(timezone=True), nullable=True)
    acknowledged_at = Column(DateTime(timezone=True), nullable=True)
    responded_at = Column(DateTime(timezone=True), nullable=True)
    
    # Platform-specific data
    platform_metadata = Column(JSONB, nullable=True, comment="Platform-specific review data")
    
    # Relationships
    account = relationship(
        "SocialAccount",
        back_populates="reviews"
    )
    
    response_text = Column(Text, nullable=True)
    responded_at = Column(DateTime(timezone=True), nullable=True)
    
    external_id = Column(String(255), nullable=True, unique=True)
    external_url = Column(String(500), nullable=True)
    extra_data = Column(JSONB, nullable=True, comment="Review metadata and platform-specific data")

    @property
    def is_positive(self) -> bool:
        """Check if review is positive (4-5 stars)."""
        return self.rating >= 4

    @property
    def needs_response(self) -> bool:
        """Check if review needs a response."""
        return self.published and not self.response_text and self.rating <= 3

    def __repr__(self):
        stars = "⭐" * self.rating
        return f"<Review {stars} from {self.source.value}>"


class CustomerReview(BaseModel):
    """Legacy customer review model (for compatibility)."""

    __tablename__ = "customer_reviews"
    __table_args__ = {"schema": "public", "extend_existing": True}

    id = Column(PostgresUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Soft references
    customer_id = Column(
        PostgresUUID(as_uuid=True),
        nullable=True,
        index=True,
        comment="Soft reference to customer (validated at application level)",
    )
    booking_id = Column(
        PostgresUUID(as_uuid=True),
        nullable=True,
        index=True,
        comment="Soft reference to booking (validated at application level)",
    )
    
    rating = Column(Integer, nullable=False)
    review_text = Column(Text, nullable=False)
    reviewer_name = Column(String(200), nullable=True)
    
    approved = Column(Boolean, nullable=False, default=False)
    featured = Column(Boolean, nullable=False, default=False)
    
    review_date = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(datetime.now().astimezone().tzinfo))

    def __repr__(self):
        stars = "⭐" * self.rating
        status = "✓" if self.approved else "⏳"
        return f"<CustomerReview {status} {stars}>"


class DiscountCoupon(BaseModel):
    """Promotional discount coupons."""

    __tablename__ = "discount_coupons"
    __table_args__ = {"schema": "public", "extend_existing": True}

    id = Column(PostgresUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    code = Column(String(50), nullable=False, unique=True, index=True)
    description = Column(Text, nullable=True)
    
    discount_type = Column(String(20), nullable=False)  # "percentage" or "fixed"
    discount_value = Column(Numeric(10, 2), nullable=False)
    
    min_order_amount = Column(Numeric(10, 2), nullable=True)
    max_discount_amount = Column(Numeric(10, 2), nullable=True)
    
    valid_from = Column(DateTime(timezone=True), nullable=False)
    valid_until = Column(DateTime(timezone=True), nullable=True)
    
    usage_limit = Column(Integer, nullable=True)
    usage_count = Column(Integer, nullable=False, default=0)
    
    active = Column(Boolean, nullable=False, default=True)
    extra_data = Column(JSONB, nullable=True, comment="Coupon metadata and campaign tracking")

    @property
    def is_valid(self) -> bool:
        """Check if coupon is currently valid."""
        now = datetime.now(datetime.now().astimezone().tzinfo)
        if not self.active:
            return False
        if now < self.valid_from:
            return False
        if self.valid_until and now > self.valid_until:
            return False
        if self.usage_limit and self.usage_count >= self.usage_limit:
            return False
        return True

    @property
    def is_percentage(self) -> bool:
        """Check if discount is percentage-based."""
        return self.discount_type == "percentage"

    def calculate_discount(self, order_amount: float) -> float:
        """Calculate discount amount for given order."""
        if not self.is_valid:
            return 0.0
        
        if self.min_order_amount and order_amount < float(self.min_order_amount):
            return 0.0
        
        if self.is_percentage:
            discount = order_amount * (float(self.discount_value) / 100)
        else:
            discount = float(self.discount_value)
        
        if self.max_discount_amount:
            discount = min(discount, float(self.max_discount_amount))
        
        return discount

    def __repr__(self):
        status = "✓" if self.is_valid else "✗"
        if self.is_percentage:
            value = f"{self.discount_value}%"
        else:
            value = f"${self.discount_value}"
        return f"<DiscountCoupon {status} {self.code}: {value}>"


__all__ = [
    "SocialThread",
    "SocialMessage",
    "Review",
    "CustomerReview",
    "DiscountCoupon",
]
