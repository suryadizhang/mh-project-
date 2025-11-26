"""
SQLAlchemy Models - Newsletter Schema
======================================

SMS & Email campaign management system:
- Subscriber (newsletter subscribers with consent tracking)
- Campaign (email/SMS campaigns)
- CampaignEvent (delivery tracking - sent, opened, clicked, etc.)
- SMSTemplate (admin + AI-suggested templates)
- CampaignSMSLimit (RingCentral package limits tracking)
- SMSSendQueue (retry mechanism for SMS delivery)
- SMSDeliveryEvent (RingCentral delivery status)

Business Logic:
- CAN-SPAM & TCPA compliance
- Consent management (SMS + email)
- Engagement scoring
- RingCentral API integration
- AI-powered template suggestions
- Package limit enforcement
- Retry mechanism with backoff
- Delivery tracking and analytics

All models use:
- UUID primary keys
- Timezone-aware datetime fields
- Schema qualification (__table_args__ = {"schema": "newsletter"})
- Proper foreign key relationships
- Type hints for IDE support
"""

from datetime import datetime
from typing import Optional, List
from uuid import UUID, uuid4

from sqlalchemy import (
    Column, String, Text, Integer, Float, Boolean, DateTime, LargeBinary,
    ForeignKey, Index, CheckConstraint, Enum as SQLEnum, ARRAY
)
from sqlalchemy.dialects.postgresql import UUID as PGUUID, JSONB
from sqlalchemy.orm import relationship, Mapped, mapped_column
from sqlalchemy.sql import func

from ..base_class import Base


# ==================== ENUMS ====================

import enum

class CampaignChannel(str, enum.Enum):
    """Campaign delivery channel"""
    EMAIL = "email"
    SMS = "sms"
    BOTH = "both"


class CampaignStatus(str, enum.Enum):
    """Campaign workflow status"""
    DRAFT = "draft"
    SCHEDULED = "scheduled"
    SENDING = "sending"
    SENT = "sent"
    CANCELLED = "cancelled"


class CampaignEventType(str, enum.Enum):
    """Campaign event types for tracking"""
    SENT = "sent"
    DELIVERED = "delivered"
    OPENED = "opened"
    CLICKED = "clicked"
    REPLIED = "replied"
    BOUNCED = "bounced"
    UNSUBSCRIBED = "unsubscribed"
    COMPLAINED = "complained"


class TemplateSource(str, enum.Enum):
    """Where the template came from"""
    ADMIN = "admin"
    AI_SUGGESTED = "ai_suggested"
    SYSTEM = "system"


class TemplateStatus(str, enum.Enum):
    """Template approval workflow"""
    DRAFT = "draft"
    PENDING_APPROVAL = "pending_approval"
    APPROVED = "approved"
    REJECTED = "rejected"
    ARCHIVED = "archived"


class SMSQueueStatus(str, enum.Enum):
    """SMS queue processing status"""
    PENDING = "pending"
    SENDING = "sending"
    SENT = "sent"
    FAILED = "failed"
    CANCELLED = "cancelled"


class SMSDeliveryStatus(str, enum.Enum):
    """RingCentral delivery status"""
    QUEUED = "queued"
    SENDING = "sending"
    SENT = "sent"
    DELIVERED = "delivered"
    FAILED = "failed"
    UNDELIVERED = "undelivered"


# ==================== MODELS ====================

class Subscriber(Base):
    """
    Newsletter subscriber entity

    Manages newsletter subscriptions with CAN-SPAM/TCPA compliance.
    Tracks engagement metrics and consent.
    """
    __tablename__ = "subscribers"
    __table_args__ = (
        Index("ix_newsletter_subscribers_subscribed", "subscribed"),
        Index("ix_newsletter_subscribers_customer", "customer_id"),
        Index("ix_newsletter_subscribers_engagement", "engagement_score"),
        CheckConstraint("engagement_score >= 0 AND engagement_score <= 100", name="check_engagement_score_range"),
        {"schema": "newsletter"}
    )

    # Primary Key
    id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        primary_key=True,
        server_default=func.gen_random_uuid()
    )

    # Customer Link
    customer_id: Mapped[Optional[UUID]] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("core.customers.id", ondelete="SET NULL"),
        nullable=True
    )

    # Encrypted Contact Info (PII)
    email_enc: Mapped[bytes] = mapped_column(LargeBinary, nullable=False)
    phone_enc: Mapped[Optional[bytes]] = mapped_column(LargeBinary, nullable=True)

    # Subscription Status
    subscribed: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    source: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)

    # Consent Tracking (CAN-SPAM & TCPA)
    sms_consent: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    email_consent: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    consent_updated_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    consent_ip_address: Mapped[Optional[str]] = mapped_column(String(45), nullable=True)

    # Segmentation
    tags: Mapped[Optional[List[str]]] = mapped_column(ARRAY(String(50)), nullable=True)

    # Engagement Metrics
    engagement_score: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    total_emails_sent: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    total_emails_opened: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    total_clicks: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    last_email_sent_date: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    last_opened_date: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now()
    )
    unsubscribed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    # Relationships
    campaign_events: Mapped[List["CampaignEvent"]] = relationship(
        "CampaignEvent",
        back_populates="subscriber",
        cascade="all, delete-orphan"
    )
    sms_queue: Mapped[List["SMSSendQueue"]] = relationship(
        "SMSSendQueue",
        back_populates="subscriber",
        cascade="all, delete-orphan"
    )


class Campaign(Base):
    """
    Marketing campaign entity

    Email/SMS campaigns with scheduling and analytics.
    """
    __tablename__ = "campaigns"
    __table_args__ = (
        Index("ix_newsletter_campaigns_status", "status"),
        Index("ix_newsletter_campaigns_sent", "sent_at"),
        {"schema": "newsletter"}
    )

    # Primary Key
    id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        primary_key=True,
        server_default=func.gen_random_uuid()
    )

    # Campaign Details
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    channel: Mapped[CampaignChannel] = mapped_column(
        SQLEnum(CampaignChannel, name="campaign_channel", schema="public", create_type=False),
        nullable=False
    )
    subject: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    content: Mapped[dict] = mapped_column(JSONB, nullable=False)

    # Segmentation
    segment_filter: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)

    # Scheduling
    scheduled_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    sent_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    # Status
    status: Mapped[CampaignStatus] = mapped_column(
        SQLEnum(CampaignStatus, name="campaign_status", schema="public", create_type=False),
        nullable=False,
        default=CampaignStatus.DRAFT
    )

    # Analytics
    total_recipients: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    # Audit
    created_by: Mapped[str] = mapped_column(String(100), nullable=False)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now()
    )

    # Relationships
    events: Mapped[List["CampaignEvent"]] = relationship(
        "CampaignEvent",
        back_populates="campaign",
        cascade="all, delete-orphan"
    )
    sms_limits: Mapped[Optional["CampaignSMSLimit"]] = relationship(
        "CampaignSMSLimit",
        back_populates="campaign",
        uselist=False,
        cascade="all, delete-orphan"
    )
    sms_queue: Mapped[List["SMSSendQueue"]] = relationship(
        "SMSSendQueue",
        back_populates="campaign",
        cascade="all, delete-orphan"
    )


class CampaignEvent(Base):
    """
    Campaign event tracking

    Tracks delivery, opens, clicks, bounces, etc.
    """
    __tablename__ = "campaign_events"
    __table_args__ = (
        Index("ix_newsletter_events_campaign", "campaign_id", "type"),
        Index("ix_newsletter_events_subscriber", "subscriber_id", "occurred_at"),
        {"schema": "newsletter"}
    )

    # Primary Key
    id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        primary_key=True,
        server_default=func.gen_random_uuid()
    )

    # Foreign Keys
    campaign_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("newsletter.campaigns.id", ondelete="CASCADE"),
        nullable=False
    )
    subscriber_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("newsletter.subscribers.id", ondelete="CASCADE"),
        nullable=False
    )

    # Event Details
    type: Mapped[CampaignEventType] = mapped_column(
        SQLEnum(CampaignEventType, name="campaign_event_type", schema="public", create_type=False),
        nullable=False
    )
    payload: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)

    # Timestamp
    occurred_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now()
    )

    # Relationships
    campaign: Mapped["Campaign"] = relationship("Campaign", back_populates="events")
    subscriber: Mapped["Subscriber"] = relationship("Subscriber", back_populates="campaign_events")
    sms_delivery: Mapped[Optional["SMSDeliveryEvent"]] = relationship(
        "SMSDeliveryEvent",
        back_populates="campaign_event",
        uselist=False,
        cascade="all, delete-orphan"
    )


class SMSTemplate(Base):
    """
    SMS template entity

    Admin-created and AI-suggested SMS templates with approval workflow.
    Supports variable substitution.
    """
    __tablename__ = "sms_templates"
    __table_args__ = (
        Index("idx_sms_templates_category", "category"),
        Index("idx_sms_templates_source", "source"),
        Index("idx_sms_templates_status", "status"),
        Index("idx_sms_templates_active", "is_active"),
        {"schema": "newsletter"}
    )

    # Primary Key
    id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        primary_key=True,
        server_default=func.gen_random_uuid()
    )

    # Template Details
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    content: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        comment="Template with {{variables}}"
    )
    category: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        comment="reminder, promotion, transactional, newsletter"
    )

    # Source & Status
    source: Mapped[TemplateSource] = mapped_column(
        SQLEnum(TemplateSource, name="template_source", schema="newsletter", create_type=False),
        nullable=False,
        server_default=TemplateSource.ADMIN.value
    )
    status: Mapped[TemplateStatus] = mapped_column(
        SQLEnum(TemplateStatus, name="template_status", schema="newsletter", create_type=False),
        nullable=False,
        server_default=TemplateStatus.DRAFT.value
    )

    # Variables Tracking
    variables: Mapped[List[str]] = mapped_column(
        JSONB,
        server_default='[]',
        comment='["first_name", "booking_date", "amount"]'
    )
    example_data: Mapped[dict] = mapped_column(
        JSONB,
        server_default='{}',
        comment='{"first_name": "John", "booking_date": "Dec 25"}'
    )

    # AI Suggestion Metadata
    ai_prompt: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="Original AI prompt if AI-generated"
    )
    ai_confidence: Mapped[Optional[float]] = mapped_column(
        Float,
        nullable=True,
        comment="AI confidence score 0.0-1.0"
    )
    ai_model: Mapped[Optional[str]] = mapped_column(
        String(50),
        nullable=True,
        comment="GPT-4, Claude, etc."
    )

    # Approval Workflow
    created_by: Mapped[Optional[UUID]] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("identity.users.id", ondelete="SET NULL"),
        nullable=True
    )
    approved_by: Mapped[Optional[UUID]] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("identity.users.id", ondelete="SET NULL"),
        nullable=True
    )
    approved_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    rejection_reason: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Usage Tracking
    usage_count: Mapped[int] = mapped_column(
        Integer,
        server_default='0',
        comment="How many times used"
    )
    last_used_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    # Status
    is_active: Mapped[bool] = mapped_column(Boolean, server_default='true')

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now()
    )

    # Relationships
    sms_queue: Mapped[List["SMSSendQueue"]] = relationship(
        "SMSSendQueue",
        back_populates="template"
    )


class CampaignSMSLimit(Base):
    """
    RingCentral SMS package limits tracking

    Enforces monthly SMS limits per RingCentral package.
    Tracks cost and sends alerts at thresholds.
    """
    __tablename__ = "campaign_sms_limits"
    __table_args__ = (
        Index("idx_campaign_sms_limits_month", "current_month"),
        Index("idx_campaign_sms_limits_exceeded", "monthly_limit_exceeded_at"),
        {"schema": "newsletter"}
    )

    # Primary Key (also FK to Campaign)
    campaign_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("newsletter.campaigns.id", ondelete="CASCADE"),
        primary_key=True
    )

    # RingCentral Package Limits
    monthly_sms_limit: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        server_default='1000',
        comment="RingCentral plan monthly limit"
    )
    monthly_sms_used: Mapped[int] = mapped_column(Integer, nullable=False, server_default='0')
    current_month: Mapped[str] = mapped_column(
        String(7),
        nullable=False,
        comment="YYYY-MM"
    )

    # Campaign-Specific Limits
    campaign_sms_limit: Mapped[Optional[int]] = mapped_column(
        Integer,
        nullable=True,
        comment="Max SMS for this campaign (optional)"
    )
    campaign_sms_sent: Mapped[int] = mapped_column(Integer, nullable=False, server_default='0')
    campaign_sms_queued: Mapped[int] = mapped_column(Integer, nullable=False, server_default='0')
    campaign_sms_failed: Mapped[int] = mapped_column(Integer, nullable=False, server_default='0')

    # Cost Tracking
    cost_per_sms_cents: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        server_default='75',
        comment="Cost in cents (e.g., $0.0075)"
    )
    total_cost_cents: Mapped[int] = mapped_column(Integer, nullable=False, server_default='0')

    # Limit Exceeded Tracking
    monthly_limit_exceeded_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    campaign_limit_exceeded_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    limit_exceeded_action: Mapped[str] = mapped_column(
        String(50),
        server_default='pause',
        comment="pause, notify, continue"
    )

    # Alert Thresholds
    alert_at_percentage: Mapped[int] = mapped_column(
        Integer,
        server_default='80',
        comment="Alert when 80% of limit used"
    )
    alert_sent_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now()
    )

    # Relationships
    campaign: Mapped["Campaign"] = relationship("Campaign", back_populates="sms_limits")


class SMSSendQueue(Base):
    """
    SMS send queue with retry mechanism

    Queues SMS messages for delivery with retry logic and RingCentral tracking.
    """
    __tablename__ = "sms_send_queue"
    __table_args__ = (
        Index("idx_sms_queue_pending", "status", "scheduled_at"),
        Index("idx_sms_queue_retry", "status", "next_retry_at"),
        Index("idx_sms_queue_priority", "priority", "scheduled_at"),
        {"schema": "newsletter"}
    )

    # Primary Key
    id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        primary_key=True,
        server_default=func.gen_random_uuid()
    )

    # Foreign Keys
    campaign_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("newsletter.campaigns.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    subscriber_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("newsletter.subscribers.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    template_id: Mapped[Optional[UUID]] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("newsletter.sms_templates.id", ondelete="SET NULL"),
        nullable=True
    )

    # Message Details
    phone_number: Mapped[str] = mapped_column(String(20), nullable=False, index=True)
    message_content: Mapped[str] = mapped_column(Text, nullable=False)
    personalized_variables: Mapped[dict] = mapped_column(
        JSONB,
        server_default='{}',
        comment="Rendered template variables"
    )

    # Queue Status
    status: Mapped[SMSQueueStatus] = mapped_column(
        SQLEnum(SMSQueueStatus, name="sms_queue_status", schema="newsletter", create_type=False),
        nullable=False,
        server_default=SMSQueueStatus.PENDING.value,
        index=True
    )
    priority: Mapped[int] = mapped_column(
        Integer,
        server_default='0',
        comment="Higher = sent first"
    )

    # Scheduling
    scheduled_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        index=True
    )
    sent_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    failed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    # Retry Logic
    attempts: Mapped[int] = mapped_column(Integer, server_default='0')
    max_attempts: Mapped[int] = mapped_column(Integer, server_default='3')
    next_retry_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    last_error: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    error_code: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)

    # RingCentral Tracking
    message_sid: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
        unique=True,
        comment="RingCentral message ID"
    )
    ringcentral_status: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now()
    )

    # Relationships
    campaign: Mapped["Campaign"] = relationship("Campaign", back_populates="sms_queue")
    subscriber: Mapped["Subscriber"] = relationship("Subscriber", back_populates="sms_queue")
    template: Mapped[Optional["SMSTemplate"]] = relationship("SMSTemplate", back_populates="sms_queue")


class SMSDeliveryEvent(Base):
    """
    SMS delivery event tracking

    Tracks RingCentral delivery status and carrier responses.
    """
    __tablename__ = "sms_delivery_events"
    __table_args__ = (
        Index("ix_sms_delivery_ringcentral_msg_id", "ringcentral_message_id", unique=True),
        Index("ix_sms_delivery_campaign_event", "campaign_event_id"),
        Index("ix_sms_delivery_status", "status"),
        Index("ix_sms_delivery_timestamp", "delivery_timestamp"),
        {"schema": "newsletter"}
    )

    # Primary Key
    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)

    # Foreign Keys
    campaign_event_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("newsletter.campaign_events.id", ondelete="CASCADE"),
        nullable=False
    )

    # RingCentral Tracking
    ringcentral_message_id: Mapped[str] = mapped_column(String(255), nullable=False)

    # Delivery Status
    status: Mapped[SMSDeliveryStatus] = mapped_column(
        SQLEnum(SMSDeliveryStatus, name="sms_delivery_status", schema="newsletter", create_type=False),
        nullable=False,
        server_default=SMSDeliveryStatus.QUEUED.value
    )
    delivery_timestamp: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    # Failure Tracking
    failure_reason: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    carrier_error_code: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)

    # Cost Tracking
    segments_used: Mapped[int] = mapped_column(Integer, nullable=False, server_default='1')
    cost_cents: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    # Metadata
    ringcentral_metadata: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)

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
    campaign_event: Mapped["CampaignEvent"] = relationship("CampaignEvent", back_populates="sms_delivery")
