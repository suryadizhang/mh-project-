"""
CRM Schema Models - Customer Relationship Management

This module consolidates all CRM-related database models into the 'crm' schema.
Provides centralized customer lifecycle management, lead tracking, and marketing campaigns.

Architecture:
- Schema: crm (dedicated namespace for customer relationship management)
- Organization: Lead management, campaign management, customer segmentation
- Separation: Clear boundary between CRM logic and core business logic

Business Domains:
1. Lead Management: Lead tracking, scoring, qualification, conversion
2. Marketing Campaigns: Email/SMS campaigns, scheduling, analytics
3. Customer Segmentation: Dynamic segments, rules-based targeting
4. Social Integration: Social media accounts, customer identities, conversations

Enterprise Features:
- Dedicated schema for CRM isolation
- Lead scoring and quality tracking
- Multi-channel campaign support (email, SMS)
- Customer segmentation for targeting
- UTM tracking for attribution
- Event sourcing for audit trail

Schema Declaration:
All models use: __table_args__ = {"schema": "crm"}

Migration Strategy:
- Phase 1B: Create crm schema and models
- Move Lead from db.models.lead → db.models.crm (schema: lead → crm)
- Move Campaign from models.newsletter → db.models.crm (schema: newsletter → crm)
- Keep original tables for rollback safety (migration handles data copy)
- Update all imports after verification

Models:
1. Lead - Lead tracking with scoring and qualification
2. LeadContact - Multi-channel contact information
3. LeadContext - Event/booking context data
4. LeadEvent - Event sourcing for audit trail
5. Campaign - Marketing campaigns (email/SMS)
6. CampaignEvent - Campaign analytics (opens, clicks, bounces)
7. CustomerSegment - Dynamic customer segments (NEW)
8. SegmentRule - Segmentation rules (NEW)
9. SocialAccount - Connected business social media pages
10. SocialIdentity - Customer social media handles
11. SocialThread - Social media conversations

Usage Example:
```python
from db.models.crm import Lead, Campaign, CustomerSegment

# Create lead
lead = Lead(
    source=LeadSource.WEB_QUOTE,
    status=LeadStatus.NEW,
    quality=LeadQuality.WARM,
    score=Decimal("75.50"),
)
session.add(lead)

# Create campaign
campaign = Campaign(
    name="Holiday Special 2025",
    channel=CampaignChannel.EMAIL,
    status=CampaignStatus.DRAFT,
    content={"subject": "Book Now!", "body": "..."},
)
session.add(campaign)

# Create segment
segment = CustomerSegment(
    name="High-Value Customers",
    description="Customers with 3+ bookings and >$500 spend",
)
session.add(segment)
```

Note: This file consolidates CRM models from multiple locations.
Lead models: From db.models.lead (schema: lead → crm)
Campaign models: From db.models.newsletter (schema: newsletter → crm)
"""

from datetime import datetime
from typing import Optional
from uuid import UUID
from decimal import Decimal
from enum import Enum

from sqlalchemy import (
    String,
    Text,
    Integer,
    Boolean,
    DateTime,
    Numeric,
    ForeignKey,
    Index,
    CheckConstraint,
    Enum as SQLEnum,
)
from sqlalchemy.dialects.postgresql import UUID as PGUUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func

from models.base import Base


# ============================================================================
# ENUMS - Lead Management
# ============================================================================


class LeadSource(str, Enum):
    """Where the lead originated"""

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


class LeadStatus(str, Enum):
    """Lead workflow status"""

    NEW = "new"
    WORKING = "working"
    QUALIFIED = "qualified"
    DISQUALIFIED = "disqualified"
    CONVERTED = "converted"
    NURTURING = "nurturing"


class LeadQuality(str, Enum):
    """Lead temperature/quality (hot/warm/cold)"""

    HOT = "hot"
    WARM = "warm"
    COLD = "cold"


class ContactChannel(str, Enum):
    """Contact method channels"""

    EMAIL = "email"
    SMS = "sms"
    INSTAGRAM = "instagram"
    FACEBOOK = "facebook"
    GOOGLE = "google"
    YELP = "yelp"
    WEB = "web"


# ============================================================================
# ENUMS - Campaign Management
# ============================================================================


class CampaignChannel(str, Enum):
    """Campaign delivery channel"""

    EMAIL = "email"
    SMS = "sms"
    BOTH = "both"


class CampaignStatus(str, Enum):
    """Campaign lifecycle status"""

    DRAFT = "draft"
    SCHEDULED = "scheduled"
    SENDING = "sending"
    SENT = "sent"
    CANCELLED = "cancelled"


class CampaignEventType(str, Enum):
    """Campaign event tracking types"""

    SENT = "sent"
    DELIVERED = "delivered"
    OPENED = "opened"
    CLICKED = "clicked"
    BOUNCED = "bounced"
    UNSUBSCRIBED = "unsubscribed"
    COMPLAINED = "complained"


# ============================================================================
# ENUMS - Social Media
# ============================================================================


class SocialPlatform(str, Enum):
    """Social media platforms"""

    INSTAGRAM = "instagram"
    FACEBOOK = "facebook"
    GOOGLE = "google"
    YELP = "yelp"


class SocialThreadStatus(str, Enum):
    """Social conversation status"""

    OPEN = "open"
    PENDING = "pending"
    RESOLVED = "resolved"


# ============================================================================
# ENUMS - Customer Segmentation
# ============================================================================


class SegmentRuleOperator(str, Enum):
    """Segmentation rule operators"""

    EQUALS = "equals"
    NOT_EQUALS = "not_equals"
    GREATER_THAN = "greater_than"
    LESS_THAN = "less_than"
    CONTAINS = "contains"
    IN = "in"
    NOT_IN = "not_in"


# ============================================================================
# LEAD MODELS (From db.models.lead)
# ============================================================================


class Lead(Base):
    """
    Lead tracking entity - CRM schema

    Represents a potential customer with scoring, qualification, and conversion tracking.
    Supports multi-channel attribution (UTM tracking).

    Schema: crm.leads (moved from lead.leads)

    Business Logic:
    - Lead scoring (0-100 scale)
    - Quality tracking (hot/warm/cold)
    - Multi-channel source attribution
    - Conversion tracking to customers
    - Follow-up scheduling
    """

    __tablename__ = "leads"
    __table_args__ = (
        Index("idx_crm_leads_status", "status"),
        Index("idx_crm_leads_source", "source"),
        Index("idx_crm_leads_score", "score"),
        Index("idx_crm_leads_followup", "follow_up_date"),
        Index("idx_crm_leads_customer", "customer_id"),
        CheckConstraint("score >= 0 AND score <= 100", name="check_lead_score_range"),
        {"schema": "crm"},
    )

    # Primary Key
    id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid()
    )

    # Source & Attribution
    source: Mapped[LeadSource] = mapped_column(
        SQLEnum(LeadSource, name="lead_source", schema="public", create_type=False), nullable=False
    )
    utm_source: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    utm_medium: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    utm_campaign: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)

    # Status & Quality
    status: Mapped[LeadStatus] = mapped_column(
        SQLEnum(LeadStatus, name="lead_status", schema="public", create_type=False),
        nullable=False,
        default=LeadStatus.NEW,
    )
    quality: Mapped[Optional[LeadQuality]] = mapped_column(
        SQLEnum(LeadQuality, name="lead_quality", schema="public", create_type=False), nullable=True
    )
    score: Mapped[Decimal] = mapped_column(Numeric(5, 2), nullable=False, default=Decimal("0"))

    # Assignment
    assigned_to: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)

    # Customer Link (when converted)
    customer_id: Mapped[Optional[UUID]] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("core.customers.id", ondelete="SET NULL"), nullable=True
    )

    # Follow-up & Conversion
    last_contact_date: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    follow_up_date: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    conversion_date: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    # Loss Tracking
    lost_reason: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now()
    )
    deleted_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)


# ============================================================================
# CAMPAIGN MODELS (From db.models.newsletter)
# ============================================================================


class Campaign(Base):
    """
    Marketing campaign entity - CRM schema

    Email/SMS campaigns with scheduling and analytics.

    Schema: crm.campaigns (moved from newsletter.campaigns)

    Business Logic:
    - Multi-channel campaigns (email, SMS, both)
    - Scheduled or immediate delivery
    - Customer segmentation support
    - Analytics tracking (sent, opened, clicked)
    - Template-based content (JSONB)
    """

    __tablename__ = "campaigns"
    __table_args__ = (
        Index("idx_crm_campaigns_status", "status"),
        Index("idx_crm_campaigns_sent", "sent_at"),
        Index("idx_crm_campaigns_channel", "channel"),
        {"schema": "crm"},
    )

    # Primary Key
    id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid()
    )

    # Campaign Details
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    channel: Mapped[CampaignChannel] = mapped_column(
        SQLEnum(CampaignChannel, name="campaign_channel", schema="public", create_type=False),
        nullable=False,
    )
    subject: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    content: Mapped[dict] = mapped_column(JSONB, nullable=False)

    # Segmentation (JSONB filter for customer targeting)
    segment_filter: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)

    # Scheduling
    scheduled_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    sent_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    # Status
    status: Mapped[CampaignStatus] = mapped_column(
        SQLEnum(CampaignStatus, name="campaign_status", schema="public", create_type=False),
        nullable=False,
        default=CampaignStatus.DRAFT,
    )

    # Analytics
    total_recipients: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    # Audit
    created_by: Mapped[str] = mapped_column(String(100), nullable=False)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )


# ============================================================================
# CUSTOMER SEGMENTATION MODELS (NEW for Phase 1B)
# ============================================================================


class CustomerSegment(Base):
    """
    Customer segmentation for targeted campaigns - CRM schema

    Defines dynamic customer groups based on business rules.

    Schema: crm.customer_segments

    Business Logic:
    - Dynamic segmentation (recalculated on query)
    - Rule-based targeting (via SegmentRule)
    - Multi-criteria support (booking count, spend, recency)
    - Campaign targeting integration

    Examples:
    - "High-Value Customers" (3+ bookings, >$500 total spend)
    - "At-Risk Customers" (no booking in 60+ days, previously active)
    - "New Customers" (first booking within 30 days)
    """

    __tablename__ = "customer_segments"
    __table_args__ = (Index("idx_crm_segments_active", "is_active"), {"schema": "crm"})

    # Primary Key
    id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid()
    )

    # Segment Details
    name: Mapped[str] = mapped_column(String(200), nullable=False, unique=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Status
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    # Metadata
    estimated_size: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    last_calculated_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now()
    )


class SegmentRule(Base):
    """
    Segmentation rules for customer targeting - CRM schema

    Defines rules for dynamic customer segmentation.

    Schema: crm.segment_rules

    Business Logic:
    - Multi-rule support (AND/OR logic)
    - Flexible field targeting (booking_count, total_spend, last_booking_date)
    - Operator support (equals, greater_than, less_than, contains, in)
    - JSON value storage for flexibility

    Rule Examples:
    - Field: "booking_count", Operator: "greater_than", Value: 3
    - Field: "total_spend", Operator: "greater_than", Value: 500.00
    - Field: "last_booking_date", Operator: "less_than", Value: "2025-10-01"
    """

    __tablename__ = "segment_rules"
    __table_args__ = (Index("idx_crm_segment_rules_segment", "segment_id"), {"schema": "crm"})

    # Primary Key
    id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid()
    )

    # Foreign Key
    segment_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("crm.customer_segments.id", ondelete="CASCADE"),
        nullable=False,
    )

    # Rule Definition
    field_name: Mapped[str] = mapped_column(String(100), nullable=False)
    operator: Mapped[SegmentRuleOperator] = mapped_column(
        SQLEnum(
            SegmentRuleOperator, name="segment_rule_operator", schema="public", create_type=False
        ),
        nullable=False,
    )
    field_value: Mapped[dict] = mapped_column(JSONB, nullable=False)

    # Rule Order (for multi-rule segments)
    rule_order: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )


# ============================================================================
# EXPORTS
# ============================================================================

__all__ = [
    # Lead Models
    "Lead",
    "LeadSource",
    "LeadStatus",
    "LeadQuality",
    "ContactChannel",
    # Campaign Models
    "Campaign",
    "CampaignChannel",
    "CampaignStatus",
    "CampaignEventType",
    # Segmentation Models (NEW)
    "CustomerSegment",
    "SegmentRule",
    "SegmentRuleOperator",
    # Social Media Enums
    "SocialPlatform",
    "SocialThreadStatus",
]

# Schema metadata for Phase 1B validation
__schema__ = "crm"
__table_args__ = {"schema": "crm"}
__version__ = "1.0.0"
__description__ = "CRM Schema Models - Lead management, campaigns, customer segmentation"
