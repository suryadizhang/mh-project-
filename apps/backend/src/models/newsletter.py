"""
Newsletter & Campaign Models

Enterprise-grade email/SMS marketing and campaign management with:
- Multi-channel campaigns (email, SMS, WhatsApp, push)
- Subscriber management with preferences
- Campaign event tracking and analytics
- SMS delivery status tracking
- Engagement metrics
"""

from datetime import datetime, timezone
import uuid

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Enum,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID as PostgresUUID
from sqlalchemy.orm import relationship

from models.base import BaseModel
from models.enums import (
    CampaignChannel,
    CampaignStatus,
    CampaignEventType,
    SMSDeliveryStatus,
)


class Campaign(BaseModel):
    """Marketing campaign tracking across channels."""

    __tablename__ = "campaigns"
    __table_args__ = {"schema": "lead", "extend_existing": True}

    id = Column(
        PostgresUUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    name = Column(String(200), nullable=False)
    channel = Column(
        Enum(CampaignChannel, name="campaign_channel", create_type=False),
        nullable=False,
    )
    status = Column(
        Enum(CampaignStatus, name="campaign_status", create_type=False),
        nullable=False,
        default=CampaignStatus.DRAFT,
    )

    subject = Column(String(500), nullable=True)
    content = Column(Text, nullable=False)
    sender_name = Column(String(100), nullable=True)
    reply_to = Column(String(200), nullable=True)

    scheduled_at = Column(DateTime(timezone=True), nullable=True)
    sent_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)

    target_segment = Column(String(100), nullable=True)
    extra_data = Column(
        JSONB, nullable=True, comment="Campaign metadata and custom fields"
    )

    # Relationships
    events = relationship(
        "CampaignEvent",
        back_populates="campaign",
        cascade="all, delete-orphan",
    )
    sms_deliveries = relationship(
        "SMSDeliveryEvent",
        back_populates="campaign",
        cascade="all, delete-orphan",
    )

    def __repr__(self):
        return f"<Campaign {self.name} ({self.channel.value}) {self.status.value}>"


class CampaignEvent(BaseModel):
    """Campaign analytics and event tracking."""

    __tablename__ = "campaign_events"
    __table_args__ = {"schema": "lead", "extend_existing": True}

    id = Column(
        PostgresUUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    campaign_id = Column(
        PostgresUUID(as_uuid=True),
        ForeignKey("lead.campaigns.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    subscriber_id = Column(
        PostgresUUID(as_uuid=True),
        ForeignKey("lead.subscribers.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    event_type = Column(
        Enum(CampaignEventType, name="campaign_event_type", create_type=False),
        nullable=False,
        index=True,
    )
    occurred_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )
    extra_data = Column(
        JSONB, nullable=True, comment="Event metadata and tracking info"
    )

    # Relationships
    campaign = relationship("Campaign", back_populates="events")
    subscriber = relationship("Subscriber", back_populates="campaign_events")

    def __repr__(self):
        return f"<CampaignEvent {self.event_type.value} at {self.occurred_at}>"


class SMSDeliveryEvent(BaseModel):
    """SMS delivery status tracking."""

    __tablename__ = "sms_delivery_events"
    __table_args__ = {"schema": "lead", "extend_existing": True}

    id = Column(
        PostgresUUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    campaign_id = Column(
        PostgresUUID(as_uuid=True),
        ForeignKey("lead.campaigns.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )
    subscriber_id = Column(
        PostgresUUID(as_uuid=True),
        ForeignKey("lead.subscribers.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    phone_number = Column(String(20), nullable=False)
    message_sid = Column(String(100), nullable=True, unique=True)
    status = Column(
        Enum(SMSDeliveryStatus, name="sms_delivery_status", create_type=False),
        nullable=False,
        index=True,
    )

    sent_at = Column(DateTime(timezone=True), nullable=True)
    delivered_at = Column(DateTime(timezone=True), nullable=True)
    failed_at = Column(DateTime(timezone=True), nullable=True)

    error_code = Column(String(50), nullable=True)
    error_message = Column(Text, nullable=True)

    cost = Column(Integer, nullable=True, comment="Cost in cents")
    extra_data = Column(
        JSONB, nullable=True, comment="SMS delivery metadata and carrier info"
    )

    # Relationships
    campaign = relationship("Campaign", back_populates="sms_deliveries")
    subscriber = relationship("Subscriber", back_populates="sms_deliveries")

    @property
    def cost_dollars(self) -> float | None:
        """Convert cents to dollars."""
        return self.cost / 100 if self.cost else None

    @cost_dollars.setter
    def cost_dollars(self, value: float | None):
        """Convert dollars to cents."""
        self.cost = int(value * 100) if value else None

    def __repr__(self):
        return f"<SMSDeliveryEvent {self.phone_number} {self.status.value}>"


class Subscriber(BaseModel):
    """Newsletter subscriber with multi-channel preferences."""

    __tablename__ = "subscribers"
    __table_args__ = {"schema": "lead", "extend_existing": True}

    id = Column(
        PostgresUUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )

    # Contact info
    email = Column(String(255), nullable=True, index=True)
    phone = Column(String(20), nullable=True, index=True)
    first_name = Column(String(100), nullable=True)
    last_name = Column(String(100), nullable=True)

    # Subscription status
    email_subscribed = Column(Boolean, nullable=False, default=True)
    sms_subscribed = Column(Boolean, nullable=False, default=False)
    push_subscribed = Column(Boolean, nullable=False, default=False)
    whatsapp_subscribed = Column(Boolean, nullable=False, default=False)

    # Subscription metadata
    subscribed_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )
    email_unsubscribed_at = Column(DateTime(timezone=True), nullable=True)
    sms_unsubscribed_at = Column(DateTime(timezone=True), nullable=True)

    # Preferences
    language = Column(String(10), nullable=False, default="en")
    timezone = Column(String(50), nullable=True)
    tags = Column(
        JSONB, nullable=True, comment="Subscriber tags for segmentation"
    )

    # Soft reference to customer
    customer_id = Column(
        PostgresUUID(as_uuid=True),
        nullable=True,
        index=True,
        comment="Soft reference to customer (validated at application level)",
    )

    # Soft reference to lead
    lead_id = Column(
        PostgresUUID(as_uuid=True),
        nullable=True,
        index=True,
        comment="Soft reference to lead (validated at application level)",
    )

    # Source tracking
    source = Column(String(100), nullable=True)
    utm_source = Column(String(100), nullable=True)
    utm_medium = Column(String(100), nullable=True)
    utm_campaign = Column(String(100), nullable=True)

    # Engagement metrics
    last_email_sent_at = Column(DateTime(timezone=True), nullable=True)
    last_email_opened_at = Column(DateTime(timezone=True), nullable=True)
    last_email_clicked_at = Column(DateTime(timezone=True), nullable=True)
    last_sms_sent_at = Column(DateTime(timezone=True), nullable=True)

    email_open_count = Column(Integer, nullable=False, default=0)
    email_click_count = Column(Integer, nullable=False, default=0)
    sms_response_count = Column(Integer, nullable=False, default=0)

    extra_data = Column(
        JSONB, nullable=True, comment="Subscriber metadata and custom fields"
    )

    # Relationships
    campaign_events = relationship(
        "CampaignEvent",
        back_populates="subscriber",
        cascade="all, delete-orphan",
    )
    sms_deliveries = relationship(
        "SMSDeliveryEvent",
        back_populates="subscriber",
        cascade="all, delete-orphan",
    )

    @property
    def full_name(self) -> str:
        """Get subscriber's full name."""
        parts = [p for p in [self.first_name, self.last_name] if p]
        return " ".join(parts) if parts else "Unknown Subscriber"

    @property
    def is_engaged(self) -> bool:
        """Check if subscriber is engaged (opened/clicked within 30 days)."""
        if not self.last_email_opened_at:
            return False
        days_since_open = (
            datetime.now(self.last_email_opened_at.tzinfo)
            - self.last_email_opened_at
        ).days
        return days_since_open <= 30

    def unsubscribe_email(self):
        """Unsubscribe from email communications."""
        self.email_subscribed = False
        self.email_unsubscribed_at = datetime.now(timezone.utc)

    def unsubscribe_sms(self):
        """Unsubscribe from SMS communications."""
        self.sms_subscribed = False
        self.sms_unsubscribed_at = datetime.now(timezone.utc)

    def __repr__(self):
        channels = []
        if self.email_subscribed:
            channels.append("📧")
        if self.sms_subscribed:
            channels.append("📱")
        if self.push_subscribed:
            channels.append("🔔")
        if self.whatsapp_subscribed:
            channels.append("💬")
        return f"<Subscriber {self.full_name} {' '.join(channels)}>"


__all__ = ["Campaign", "CampaignEvent", "SMSDeliveryEvent", "Subscriber"]
