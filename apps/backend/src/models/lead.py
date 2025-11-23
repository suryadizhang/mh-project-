"""
Lead Management Models

Enterprise-grade lead tracking and management system with:
- Multi-channel lead acquisition tracking
- Automated lead scoring
- Contact verification across channels
- Event context and preferences
- Comprehensive activity tracking
"""

from datetime import date, datetime
from typing import Any, Optional
import uuid

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Column,
    Date,
    DateTime,
    Enum,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID as PostgresUUID
from sqlalchemy.orm import relationship

from models.base import BaseModel
from models.enums import LeadSource, LeadStatus, LeadQuality, ContactChannel


class Lead(BaseModel):
    """Lead management with comprehensive tracking."""

    __tablename__ = "leads"
    __table_args__ = (
        CheckConstraint("score >= 0 AND score <= 100", name="check_lead_score_range"),
        {"schema": "lead", "extend_existing": True},
    )

    id = Column(PostgresUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    source = Column(Enum(LeadSource, name='lead_source', create_type=False), nullable=False)
    status = Column(Enum(LeadStatus, name='lead_status', create_type=False), nullable=False, default=LeadStatus.NEW)
    quality = Column(Enum(LeadQuality, name='lead_quality', create_type=False), nullable=True)
    
    # Soft reference to customer (validated at application level - keeps modules decoupled)
    customer_id = Column(
        PostgresUUID(as_uuid=True),
        nullable=True,
        comment="Soft reference to customer (validated at application level)",
    )
    
    score = Column(Numeric(5, 2), nullable=False, default=0)
    assigned_to = Column(String(100), nullable=True)
    last_contact_date = Column(DateTime(timezone=True), nullable=True)
    follow_up_date = Column(DateTime(timezone=True), nullable=True)
    conversion_date = Column(DateTime(timezone=True), nullable=True)
    lost_reason = Column(Text, nullable=True)
    
    # UTM tracking
    utm_source = Column(String(100), nullable=True)
    utm_medium = Column(String(100), nullable=True)
    utm_campaign = Column(String(100), nullable=True)

    # Relationships
    contacts = relationship("LeadContact", back_populates="lead", cascade="all, delete-orphan")
    context = relationship(
        "LeadContext", back_populates="lead", uselist=False, cascade="all, delete-orphan"
    )
    events = relationship("LeadEvent", back_populates="lead", cascade="all, delete-orphan")
    # social_threads relationship defined in social.py to avoid circular imports

    @property
    def primary_contact(self) -> Optional["LeadContact"]:
        """Get the primary contact method."""
        for contact in self.contacts:
            if contact.verified:
                return contact
        return self.contacts[0] if self.contacts else None

    def add_event(self, event_type: str, payload: dict[str, Any] | None = None):
        """Add a tracking event."""
        event = LeadEvent(lead_id=self.id, type=event_type, payload=payload or {})
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
            LeadSource.EVENT: 12,
            LeadSource.WEBSITE: 15,  # Added for compatibility
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
        recent_events = [
            e
            for e in self.events
            if e.occurred_at and (datetime.now(e.occurred_at.tzinfo) - e.occurred_at).days <= 7
        ]
        score += len(recent_events) * 3

        return min(score, 100.0)

    def __repr__(self):
        return f"<Lead {self.id} {self.source.value} {self.status.value} score={self.score}>"


class LeadContact(BaseModel):
    """Lead contact information across channels."""

    __tablename__ = "lead_contacts"
    __table_args__ = {"schema": "lead", "extend_existing": True}

    id = Column(PostgresUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    lead_id = Column(
        PostgresUUID(as_uuid=True), ForeignKey("lead.leads.id", ondelete="CASCADE"), nullable=False
    )
    channel = Column(Enum(ContactChannel, name='contact_channel', create_type=False), nullable=False)
    handle_or_address = Column(Text, nullable=False)
    verified = Column(Boolean, nullable=False, default=False)

    # Relationships
    lead = relationship("Lead", back_populates="contacts")

    def __repr__(self):
        status = "✓" if self.verified else "✗"
        return f"<LeadContact {status} {self.channel.value}: {self.handle_or_address[:30]}>"


class LeadContext(BaseModel):
    """Event context and preferences for leads."""

    __tablename__ = "lead_context"
    __table_args__ = {"schema": "lead", "extend_existing": True}

    lead_id = Column(
        PostgresUUID(as_uuid=True), ForeignKey("lead.leads.id", ondelete="CASCADE"), primary_key=True
    )
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
    def estimated_budget_dollars(self) -> float | None:
        """Convert cents to dollars."""
        return self.estimated_budget_cents / 100 if self.estimated_budget_cents else None

    @estimated_budget_dollars.setter
    def estimated_budget_dollars(self, value: float | None):
        """Convert dollars to cents."""
        self.estimated_budget_cents = int(value * 100) if value else None

    def __repr__(self):
        budget = f"${self.estimated_budget_dollars:.2f}" if self.estimated_budget_dollars else "N/A"
        party_size = self.party_size_adults or 0
        return f"<LeadContext party={party_size} budget={budget}>"


class LeadEvent(BaseModel):
    """Lead activity and interaction tracking."""

    __tablename__ = "lead_events"
    __table_args__ = {"schema": "lead", "extend_existing": True}

    id = Column(PostgresUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    lead_id = Column(
        PostgresUUID(as_uuid=True), ForeignKey("lead.leads.id", ondelete="CASCADE"), nullable=False, index=True
    )
    type = Column(String(50), nullable=False, index=True)
    occurred_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(datetime.now().astimezone().tzinfo))
    payload = Column(JSONB, nullable=True)

    # Relationships
    lead = relationship("Lead", back_populates="events")

    def __repr__(self):
        return f"<LeadEvent {self.type} at {self.occurred_at}>"


__all__ = ["Lead", "LeadContact", "LeadContext", "LeadEvent"]
