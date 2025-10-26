"""Lead and Newsletter SQLAlchemy models with encryption."""

from datetime import datetime, date
from typing import Optional, List, Dict, Any
from sqlalchemy import (
    Column, String, Text, Integer, Boolean, DateTime, Date, Enum, 
    ForeignKey, CheckConstraint, Index, LargeBinary, ARRAY, Numeric
)
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.ext.declarative import declared_attr
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum
import uuid

from .base import BaseModel
from .encryption import CryptoUtil


# Enums for type safety
class LeadSource(str, enum.Enum):
    """Lead acquisition sources."""
    WEB_QUOTE = "web_quote"
    CHAT = "chat"
    BOOKING_FAILED = "booking_failed"
    INSTAGRAM = "instagram"
    FACEBOOK = "facebook"
    GOOGLE = "google"
    GOOGLE_MY_BUSINESS = "google_my_business"
    YELP = "yelp"
    SMS = "sms"
    PHONE = "phone"
    REFERRAL = "referral"
    EVENT = "event"
    PAYMENT = "payment"
    FINANCIAL = "financial"
    STRIPE = "stripe"
    PLAID = "plaid"


class LeadStatus(str, enum.Enum):
    """Lead lifecycle status."""
    NEW = "new"
    WORKING = "working"
    QUALIFIED = "qualified"
    DISQUALIFIED = "disqualified"
    CONVERTED = "converted"
    NURTURING = "nurturing"
    CUSTOMER = "customer"


class LeadQuality(str, enum.Enum):
    """Lead quality scoring."""
    HOT = "hot"
    WARM = "warm"
    COLD = "cold"


class ContactChannel(str, enum.Enum):
    """Communication channels."""
    EMAIL = "email"
    SMS = "sms"
    INSTAGRAM = "instagram"
    FACEBOOK = "facebook"
    GOOGLE = "google"
    YELP = "yelp"
    WEB = "web"


class SocialPlatform(str, enum.Enum):
    """Social media platforms."""
    INSTAGRAM = "instagram"
    FACEBOOK = "facebook"
    GOOGLE = "google"
    GOOGLE_BUSINESS = "google_business"
    YELP = "yelp"
    SMS = "sms"
    PHONE = "phone"
    STRIPE = "stripe"
    PLAID = "plaid"


class ThreadStatus(str, enum.Enum):
    """Social thread status."""
    OPEN = "open"
    PENDING = "pending"
    RESOLVED = "resolved"
    CLOSED = "closed"
    URGENT = "urgent"


class CampaignChannel(str, enum.Enum):
    """Marketing campaign channels."""
    EMAIL = "email"
    SMS = "sms"
    BOTH = "both"


class CampaignStatus(str, enum.Enum):
    """Campaign lifecycle status."""
    DRAFT = "draft"
    SCHEDULED = "scheduled"
    SENDING = "sending"
    SENT = "sent"
    CANCELLED = "cancelled"


class CampaignEventType(str, enum.Enum):
    """Campaign interaction events."""
    SENT = "sent"
    DELIVERED = "delivered"
    OPENED = "opened"
    CLICKED = "clicked"
    REPLIED = "replied"
    BOUNCED = "bounced"
    UNSUBSCRIBED = "unsubscribed"
    COMPLAINED = "complained"


class Lead(BaseModel):
    """Lead management with comprehensive tracking."""
    __tablename__ = "leads"
    __table_args__ = (
        CheckConstraint('score >= 0 AND score <= 100', name='check_lead_score_range'),
        {'schema': 'lead'}
    )

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    source = Column(Enum(LeadSource), nullable=False)
    status = Column(Enum(LeadStatus), nullable=False, default=LeadStatus.NEW)
    quality = Column(Enum(LeadQuality), nullable=True)
    customer_id = Column(
        UUID(as_uuid=True), 
        nullable=True,
        comment="Soft reference to customer (validated at application level)"
    )  # No FK - keeps modules decoupled, validated in service layer
    score = Column(Numeric(5,2), nullable=False, default=0)
    assigned_to = Column(String(100), nullable=True)
    last_contact_date = Column(DateTime(timezone=True), nullable=True)
    follow_up_date = Column(DateTime(timezone=True), nullable=True)
    conversion_date = Column(DateTime(timezone=True), nullable=True)
    lost_reason = Column(Text, nullable=True)
    utm_source = Column(String(100), nullable=True)
    utm_medium = Column(String(100), nullable=True)
    utm_campaign = Column(String(100), nullable=True)

    # Relationships
    # customer = relationship("Customer", back_populates="leads")  # Commented out - Customer model not in this module
    contacts = relationship("LeadContact", back_populates="lead", cascade="all, delete-orphan")
    context = relationship("LeadContext", back_populates="lead", uselist=False, cascade="all, delete-orphan")
    events = relationship("LeadEvent", back_populates="lead", cascade="all, delete-orphan")
    social_threads = relationship("SocialThread", back_populates="lead")

    @property
    def primary_contact(self) -> Optional["LeadContact"]:
        """Get the primary contact method."""
        for contact in self.contacts:
            if contact.verified:
                return contact
        return self.contacts[0] if self.contacts else None

    def add_event(self, event_type: str, payload: Optional[Dict[str, Any]] = None):
        """Add a tracking event."""
        event = LeadEvent(
            lead_id=self.id,
            type=event_type,
            payload=payload or {}
        )
        self.events.append(event)

    def calculate_score(self) -> float:
        """Calculate lead score based on context and engagement."""
        score = 0.0
        
        # Source quality scoring
        source_scores = {
            LeadSource.WEB_QUOTE: 20,
            LeadSource.CHAT: 15,
            LeadSource.PHONE: 15,
            LeadSource.REFERRAL: 25,
            LeadSource.INSTAGRAM: 10,
            LeadSource.FACEBOOK: 10,
            LeadSource.GOOGLE: 8,
            LeadSource.YELP: 8,
            LeadSource.SMS: 5,
            LeadSource.EVENT: 12
        }
        score += source_scores.get(self.source, 0)

        # Context scoring
        if self.context:
            if self.context.party_size_adults:
                score += min(self.context.party_size_adults * 2, 15)
            if self.context.estimated_budget_cents:
                budget_score = min(self.context.estimated_budget_cents / 10000, 20)
                score += budget_score
            if self.context.event_date_pref:
                days_out = (self.context.event_date_pref - date.today()).days
                if 7 <= days_out <= 90:
                    score += 15
                elif days_out < 7:
                    score += 10

        # Contact method scoring
        verified_contacts = [c for c in self.contacts if c.verified]
        score += len(verified_contacts) * 5

        # Engagement scoring
        recent_events = [e for e in self.events if e.occurred_at and 
                        (datetime.now(e.occurred_at.tzinfo) - e.occurred_at).days <= 7]
        score += len(recent_events) * 3

        return min(score, 100.0)


class LeadContact(BaseModel):
    """Lead contact information across channels."""
    __tablename__ = "lead_contacts"
    __table_args__ = {'schema': 'lead'}

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    lead_id = Column(UUID(as_uuid=True), ForeignKey('lead.leads.id', ondelete='CASCADE'), nullable=False)
    channel = Column(Enum(ContactChannel), nullable=False)
    handle_or_address = Column(Text, nullable=False)
    verified = Column(Boolean, nullable=False, default=False)

    # Relationships
    lead = relationship("Lead", back_populates="contacts")


class LeadContext(BaseModel):
    """Event context and preferences for leads."""
    __tablename__ = "lead_context"
    __table_args__ = {'schema': 'lead'}

    lead_id = Column(UUID(as_uuid=True), ForeignKey('lead.leads.id', ondelete='CASCADE'), primary_key=True)
    party_size_adults = Column(Integer, nullable=True)
    party_size_kids = Column(Integer, nullable=True)
    estimated_budget_cents = Column(Integer, nullable=True)
    event_date_pref = Column(Date, nullable=True)
    event_date_range_start = Column(Date, nullable=True)
    event_date_range_end = Column(Date, nullable=True)
    zip_code = Column(String(10), nullable=True)
    service_type = Column(String(50), nullable=True)
    notes = Column(Text, nullable=True)

    # Relationships
    lead = relationship("Lead", back_populates="context")

    @property
    def estimated_budget_dollars(self) -> Optional[float]:
        """Convert cents to dollars."""
        return self.estimated_budget_cents / 100 if self.estimated_budget_cents else None

    @estimated_budget_dollars.setter
    def estimated_budget_dollars(self, value: Optional[float]):
        """Convert dollars to cents."""
        self.estimated_budget_cents = int(value * 100) if value else None


class LeadEvent(BaseModel):
    """Lead activity tracking."""
    __tablename__ = "lead_events"
    __table_args__ = {'schema': 'lead'}

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    lead_id = Column(UUID(as_uuid=True), ForeignKey('lead.leads.id', ondelete='CASCADE'), nullable=False)
    type = Column(String(50), nullable=False)
    payload = Column(JSONB, nullable=True)
    occurred_at = Column(DateTime(timezone=True), nullable=False, default=func.now())

    # Relationships
    lead = relationship("Lead", back_populates="events")


class SocialThread(BaseModel):
    """Social media conversation tracking."""
    __tablename__ = "social_threads"
    __table_args__ = (
        Index('ix_social_threads_platform', 'platform', 'thread_external_id', unique=True),
        {'schema': 'lead'}
    )

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    platform = Column(Enum(SocialPlatform), nullable=False)
    thread_external_id = Column(String(255), nullable=False)  # External platform thread ID
    lead_id = Column(UUID(as_uuid=True), ForeignKey('lead.leads.id', ondelete='SET NULL'), nullable=True)
    customer_id = Column(UUID(as_uuid=True), nullable=True)  # FK removed - Customer model not in this module
    
    # Thread management
    status = Column(Enum(ThreadStatus), nullable=False, default=ThreadStatus.OPEN)
    customer_handle = Column(String(255), nullable=True)  # Customer's display name/handle
    unread_count = Column(Integer, nullable=False, default=0)
    last_message_at = Column(DateTime(timezone=True), nullable=True)
    closed_at = Column(DateTime(timezone=True), nullable=True)
    
    # Platform-specific data
    platform_metadata = Column(JSONB, nullable=True)

    # Relationships
    lead = relationship("Lead", back_populates="social_threads")
    # customer = relationship("Customer", back_populates="social_threads")  # Commented out - Customer model not in this module


# Newsletter models
class Subscriber(BaseModel):
    """Newsletter subscriber with engagement tracking."""
    __tablename__ = "subscribers"
    __table_args__ = (
        CheckConstraint('engagement_score >= 0 AND engagement_score <= 100', name='check_engagement_score_range'),
        {'schema': 'newsletter'}
    )

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    customer_id = Column(UUID(as_uuid=True), nullable=True)  # FK removed - Customer model not in this module
    email_enc = Column(LargeBinary, nullable=False)
    phone_enc = Column(LargeBinary, nullable=True)
    subscribed = Column(Boolean, nullable=False, default=True)
    source = Column(String(50), nullable=True)
    sms_consent = Column(Boolean, nullable=False, default=False)
    email_consent = Column(Boolean, nullable=False, default=True)
    consent_updated_at = Column(DateTime(timezone=True), nullable=True)
    consent_ip_address = Column(String(45), nullable=True)
    tags = Column(ARRAY(String(50)), nullable=True)
    engagement_score = Column(Integer, nullable=False, default=0)
    total_emails_sent = Column(Integer, nullable=False, default=0)
    total_emails_opened = Column(Integer, nullable=False, default=0)
    total_clicks = Column(Integer, nullable=False, default=0)
    last_email_sent_date = Column(DateTime(timezone=True), nullable=True)
    last_opened_date = Column(DateTime(timezone=True), nullable=True)
    unsubscribed_at = Column(DateTime(timezone=True), nullable=True)

    # Relationships
    # customer = relationship("Customer", back_populates="newsletter_subscriptions")  # Commented out - Customer model not in this module
    campaign_events = relationship("CampaignEvent", back_populates="subscriber", cascade="all, delete-orphan")

    @property
    def email(self) -> Optional[str]:
        """Decrypt email address."""
        return CryptoUtil.decrypt_text(self.email_enc) if self.email_enc else None

    @email.setter
    def email(self, value: Optional[str]):
        """Encrypt email address."""
        self.email_enc = CryptoUtil.encrypt_text(value) if value else None

    @property
    def phone(self) -> Optional[str]:
        """Decrypt phone number."""
        return CryptoUtil.decrypt_text(self.phone_enc) if self.phone_enc else None

    @phone.setter
    def phone(self, value: Optional[str]):
        """Encrypt phone number."""
        self.phone_enc = CryptoUtil.encrypt_text(value) if value else None

    @property
    def open_rate(self) -> float:
        """Calculate email open rate."""
        return (self.total_emails_opened / self.total_emails_sent) if self.total_emails_sent > 0 else 0.0

    @property
    def click_rate(self) -> float:
        """Calculate click-through rate."""
        return (self.total_clicks / self.total_emails_sent) if self.total_emails_sent > 0 else 0.0

    def update_engagement_score(self):
        """Update engagement score based on recent activity."""
        score = 0
        
        # Base score from open rate
        score += self.open_rate * 40
        
        # Click rate bonus
        score += self.click_rate * 30
        
        # Recency bonus
        if self.last_opened_date:
            days_since_open = (datetime.now(self.last_opened_date.tzinfo) - self.last_opened_date).days
            if days_since_open <= 7:
                score += 20
            elif days_since_open <= 30:
                score += 10
        
        # Consent and subscription status
        if self.subscribed and self.email_consent:
            score += 10
        
        self.engagement_score = int(min(score, 100))


class Campaign(BaseModel):
    """Marketing campaign management."""
    __tablename__ = "campaigns"
    __table_args__ = {'schema': 'newsletter'}

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(200), nullable=False)
    channel = Column(Enum(CampaignChannel), nullable=False)
    subject = Column(Text, nullable=True)
    content = Column(JSONB, nullable=False)
    segment_filter = Column(JSONB, nullable=True)
    scheduled_at = Column(DateTime(timezone=True), nullable=True)
    sent_at = Column(DateTime(timezone=True), nullable=True)
    status = Column(Enum(CampaignStatus), nullable=False, default=CampaignStatus.DRAFT)
    total_recipients = Column(Integer, nullable=False, default=0)
    created_by = Column(String(100), nullable=False)

    # Relationships
    events = relationship("CampaignEvent", back_populates="campaign", cascade="all, delete-orphan")

    @property
    def delivery_rate(self) -> float:
        """Calculate delivery rate."""
        delivered = len([e for e in self.events if e.type == CampaignEventType.DELIVERED])
        return (delivered / self.total_recipients) if self.total_recipients > 0 else 0.0

    @property
    def open_rate(self) -> float:
        """Calculate open rate."""
        opened = len([e for e in self.events if e.type == CampaignEventType.OPENED])
        return (opened / self.total_recipients) if self.total_recipients > 0 else 0.0

    @property
    def click_rate(self) -> float:
        """Calculate click rate."""
        clicked = len([e for e in self.events if e.type == CampaignEventType.CLICKED])
        return (clicked / self.total_recipients) if self.total_recipients > 0 else 0.0


class CampaignEvent(BaseModel):
    """Campaign interaction tracking."""
    __tablename__ = "campaign_events"
    __table_args__ = {'schema': 'newsletter'}

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    campaign_id = Column(UUID(as_uuid=True), ForeignKey('newsletter.campaigns.id', ondelete='CASCADE'), nullable=False)
    subscriber_id = Column(UUID(as_uuid=True), ForeignKey('newsletter.subscribers.id', ondelete='CASCADE'), nullable=False)
    type = Column(Enum(CampaignEventType), nullable=False)
    payload = Column(JSONB, nullable=True)
    occurred_at = Column(DateTime(timezone=True), nullable=False, default=func.now())

    # Relationships
    campaign = relationship("Campaign", back_populates="events")
    subscriber = relationship("Subscriber", back_populates="campaign_events")