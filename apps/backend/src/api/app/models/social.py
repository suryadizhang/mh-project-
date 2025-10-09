"""Social media integration models."""

from enum import Enum

from sqlalchemy import (
    ARRAY,
    Boolean,
    Column,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy.dialects.postgresql import ENUM, JSONB, UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from api.app.database import Base


class SocialPlatform(str, Enum):
    """Supported social media platforms."""
    INSTAGRAM = "instagram"
    FACEBOOK = "facebook"
    GOOGLE_BUSINESS = "google_business"
    YELP = "yelp"
    TIKTOK = "tiktok"
    TWITTER = "twitter"


class MessageDirection(str, Enum):
    """Direction of social media messages."""
    IN = "in"
    OUT = "out"


class MessageKind(str, Enum):
    """Type of social media message."""
    DM = "dm"
    COMMENT = "comment"
    REVIEW = "review"
    REPLY = "reply"
    MENTION = "mention"
    STORY_REPLY = "story_reply"


class ThreadStatus(str, Enum):
    """Status of social media threads."""
    OPEN = "open"
    PENDING = "pending"
    RESOLVED = "resolved"
    SNOOZED = "snoozed"
    ESCALATED = "escalated"


class ReviewStatus(str, Enum):
    """Status of reviews."""
    NEW = "new"
    ACKNOWLEDGED = "acknowledged"
    RESPONDED = "responded"
    ESCALATED = "escalated"
    CLOSED = "closed"


class SocialAccount(Base):
    """Connected social media business accounts."""
    __tablename__ = "social_accounts"
    __table_args__ = {"schema": "core"}

    id = Column(UUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid())
    platform = Column(ENUM(SocialPlatform), nullable=False)
    page_id = Column(String(255), nullable=False, comment="Platform-specific page/business ID")
    page_name = Column(String(255), nullable=False, comment="Display name of the business page")
    handle = Column(String(100), nullable=True, comment="@username or handle if applicable")
    profile_url = Column(Text, nullable=True)
    avatar_url = Column(Text, nullable=True)
    connected_by = Column(UUID(as_uuid=True), nullable=False, comment="User who connected this account")
    connected_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    token_ref = Column(Text, nullable=True, comment="Encrypted reference to access tokens")
    webhook_verified = Column(Boolean, default=False, nullable=False)
    last_sync_at = Column(DateTime(timezone=True), nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    platform_metadata = Column(JSONB, nullable=True, comment="Platform-specific settings and capabilities")
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    deleted_at = Column(DateTime(timezone=True), nullable=True)

    # Relationships
    threads = relationship("SocialThread", back_populates="account")
    reviews = relationship("Review", back_populates="account")


class SocialIdentity(Base):
    """Social media identities mapped to customers."""
    __tablename__ = "social_identities"
    __table_args__ = {"schema": "core"}

    id = Column(UUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid())
    platform = Column(ENUM(SocialPlatform), nullable=False)
    handle = Column(String(100), nullable=False, comment="Social handle without @ prefix")
    display_name = Column(String(255), nullable=True)
    profile_url = Column(Text, nullable=True)
    avatar_url = Column(Text, nullable=True)
    customer_id = Column(UUID(as_uuid=True), nullable=True, comment="Link to known customer")
    confidence_score = Column(Float, default=1.0, nullable=False, comment="Confidence in customer mapping")
    verification_status = Column(String(50), default="unverified", nullable=False)
    first_seen_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    last_active_at = Column(DateTime(timezone=True), nullable=True)
    platform_metadata = Column(JSONB, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    # Relationships
    threads = relationship("SocialThread", back_populates="social_identity")


class SocialThread(Base):
    """Social media conversation threads."""
    __tablename__ = "social_threads"
    __table_args__ = {"schema": "core"}

    id = Column(UUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid())
    platform = Column(ENUM(SocialPlatform), nullable=False)
    thread_ref = Column(String(255), nullable=False, comment="Platform-specific thread/conversation ID")
    account_id = Column(UUID(as_uuid=True), ForeignKey("core.social_accounts.id", ondelete="CASCADE"), nullable=False)
    customer_id = Column(UUID(as_uuid=True), nullable=True, comment="Linked customer if known")
    lead_id = Column(UUID(as_uuid=True), nullable=True, comment="Generated lead if applicable")
    social_identity_id = Column(UUID(as_uuid=True), ForeignKey("core.social_identities.id", ondelete="SET NULL"), nullable=True)
    status = Column(ENUM(ThreadStatus), default=ThreadStatus.OPEN, nullable=False)
    priority = Column(Integer, default=3, nullable=False, comment="1=urgent, 5=low")
    subject = Column(String(255), nullable=True, comment="Thread subject or first message preview")
    context_url = Column(Text, nullable=True, comment="Link to original post/content")
    message_count = Column(Integer, default=0, nullable=False)
    unread_count = Column(Integer, default=0, nullable=False)
    last_message_at = Column(DateTime(timezone=True), nullable=True)
    last_response_at = Column(DateTime(timezone=True), nullable=True)
    assigned_to = Column(UUID(as_uuid=True), nullable=True, comment="Assigned team member")
    tags = Column(ARRAY(String(50)), nullable=True)
    platform_metadata = Column(JSONB, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    resolved_at = Column(DateTime(timezone=True), nullable=True)

    # Relationships
    account = relationship("SocialAccount", back_populates="threads")
    social_identity = relationship("SocialIdentity", back_populates="threads")
    messages = relationship("SocialMessage", back_populates="thread", cascade="all, delete-orphan")


class SocialMessage(Base):
    """Individual messages within social media threads."""
    __tablename__ = "social_messages"
    __table_args__ = {"schema": "core"}

    id = Column(UUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid())
    thread_id = Column(UUID(as_uuid=True), ForeignKey("core.social_threads.id", ondelete="CASCADE"), nullable=False)
    message_ref = Column(String(255), nullable=True, comment="Platform-specific message ID")
    direction = Column(ENUM(MessageDirection), nullable=False)
    kind = Column(ENUM(MessageKind), nullable=False)
    author_handle = Column(String(100), nullable=True)
    author_name = Column(String(255), nullable=True)
    body = Column(Text, nullable=True)
    media = Column(JSONB, nullable=True, comment="Attachments, images, videos")
    sentiment_score = Column(Float, nullable=True, comment="AI sentiment analysis -1 to 1")
    intent_tags = Column(ARRAY(String(50)), nullable=True, comment="Detected intents: booking, complaint, etc")
    is_public = Column(Boolean, default=False, nullable=False, comment="Public comment vs private DM")
    requires_approval = Column(Boolean, default=False, nullable=False, comment="AI response needs human approval")
    approved_by = Column(UUID(as_uuid=True), nullable=True, comment="Who approved the response")
    ai_generated = Column(Boolean, default=False, nullable=False)
    parent_message_id = Column(UUID(as_uuid=True), ForeignKey("core.social_messages.id", ondelete="CASCADE"), nullable=True)
    platform_metadata = Column(JSONB, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    sent_at = Column(DateTime(timezone=True), nullable=True, comment="When actually posted to platform")
    failed_at = Column(DateTime(timezone=True), nullable=True)
    error_details = Column(Text, nullable=True)

    # Relationships
    thread = relationship("SocialThread", back_populates="messages")
    parent_message = relationship("SocialMessage", remote_side=[id])


class Review(Base):
    """Social media reviews and ratings."""
    __tablename__ = "reviews"
    __table_args__ = {"schema": "core"}

    id = Column(UUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid())
    platform = Column(ENUM(SocialPlatform), nullable=False)
    account_id = Column(UUID(as_uuid=True), ForeignKey("core.social_accounts.id", ondelete="CASCADE"), nullable=False)
    review_ref = Column(String(255), nullable=False, comment="Platform-specific review ID")
    thread_id = Column(UUID(as_uuid=True), ForeignKey("core.social_threads.id", ondelete="SET NULL"), nullable=True)
    author_handle = Column(String(100), nullable=True)
    author_name = Column(String(255), nullable=True)
    rating = Column(Integer, nullable=True, comment="1-5 star rating where applicable")
    title = Column(String(255), nullable=True)
    body = Column(Text, nullable=True)
    review_url = Column(Text, nullable=True)
    status = Column(ENUM(ReviewStatus), default=ReviewStatus.NEW, nullable=False)
    sentiment_score = Column(Float, nullable=True)
    keywords = Column(ARRAY(String(50)), nullable=True)
    customer_id = Column(UUID(as_uuid=True), nullable=True)
    booking_ref = Column(String(50), nullable=True, comment="Reference to related booking if found")
    assigned_to = Column(UUID(as_uuid=True), nullable=True)
    escalation_reason = Column(String(255), nullable=True)
    response_due_at = Column(DateTime(timezone=True), nullable=True, comment="SLA deadline")
    responded_at = Column(DateTime(timezone=True), nullable=True)
    platform_metadata = Column(JSONB, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    # Relationships
    account = relationship("SocialAccount", back_populates="reviews")
    thread = relationship("SocialThread")


class SocialInbox(Base):
    """Webhook idempotency tracking."""
    __tablename__ = "social_inbox"
    __table_args__ = {"schema": "integra"}

    signature = Column(String(255), primary_key=True, comment="Webhook signature for idempotency")
    platform = Column(ENUM(SocialPlatform), nullable=False)
    webhook_type = Column(String(100), nullable=False, comment="Type of webhook event")
    account_id = Column(UUID(as_uuid=True), nullable=True)
    payload_hash = Column(String(64), nullable=False, comment="SHA256 of payload for deduplication")
    processed = Column(Boolean, default=False, nullable=False)
    processing_attempts = Column(Integer, default=0, nullable=False)
    last_error = Column(Text, nullable=True)
    received_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    processed_at = Column(DateTime(timezone=True), nullable=True)
