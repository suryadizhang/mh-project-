"""
Terms & Conditions Acknowledgment Model

Tracks customer agreement to terms across ALL booking channels:
- Web booking form
- Phone bookings
- SMS text bookings
- AI chatbot bookings

Legal Protection: Records when, how, and from where customer agreed to terms.
"""

from datetime import datetime, timezone
from enum import Enum

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Text, Boolean
from sqlalchemy import Enum as SQLEnum
from sqlalchemy.dialects.postgresql import INET
from sqlalchemy.orm import relationship

from .base import BaseModel


class AcknowledgmentChannel(str, Enum):
    """Channel through which terms were acknowledged"""
    WEB = "web"  # Website booking form
    PHONE = "phone"  # Phone booking with staff
    SMS = "sms"  # Text message booking
    WHATSAPP = "whatsapp"  # WhatsApp booking
    AI_CHAT = "ai_chat"  # AI chatbot booking
    EMAIL = "email"  # Email booking confirmation
    IN_PERSON = "in_person"  # Walk-in booking


class TermsAcknowledgment(BaseModel):
    """
    Records customer acknowledgment of Terms & Conditions

    Legal Requirements:
    - Who agreed (customer_id)
    - What they agreed to (terms_version, terms_url)
    - When they agreed (acknowledged_at)
    - How they agreed (channel, method)
    - Where they agreed from (ip_address, user_agent)
    - Proof of agreement (acknowledgment_text, booking_id)
    """
    __tablename__ = "terms_acknowledgments"

    # Who agreed
    customer_id = Column(Integer, ForeignKey("customers.id"), nullable=False, index=True)
    booking_id = Column(Integer, ForeignKey("core.bookings.id"), nullable=True, index=True)  # core schema

    # What they agreed to
    terms_version = Column(String(20), nullable=False, default="1.0")
    terms_url = Column(String(500), nullable=False)
    terms_text_hash = Column(String(64))  # SHA-256 hash of terms text at time of agreement

    # When they agreed
    acknowledged_at = Column(DateTime, nullable=False, default=lambda: datetime.now(timezone.utc), index=True)

    # How they agreed
    channel = Column(SQLEnum(AcknowledgmentChannel), nullable=False, index=True)
    acknowledgment_method = Column(String(50), nullable=False)  # e.g., "checkbox", "reply_agree", "verbal_confirmation"
    acknowledgment_text = Column(Text)  # Exact text customer sent/said (e.g., "I agree", "Yes, I confirm")

    # Where they agreed from (for web/digital channels)
    ip_address = Column(INET)
    user_agent = Column(Text)

    # Additional context
    staff_member_name = Column(String(255))  # For phone/in-person bookings
    staff_member_email = Column(String(255))  # Who recorded the acknowledgment
    notes = Column(Text)  # Additional context

    # Verification
    verified = Column(Boolean, default=True, nullable=False)  # Manual verification for ambiguous cases
    verification_notes = Column(Text)

    # Relationships (temporarily commented for Bug #13 schema fixes)
    customer = relationship("models.customer.Customer", back_populates="terms_acknowledgments", lazy="select")
    # booking = relationship("models.booking.Booking", back_populates="terms_acknowledgments", lazy="select")

    def __repr__(self):
        return (
            f"<TermsAcknowledgment("
            f"id={self.id}, "
            f"customer_id={self.customer_id}, "
            f"channel={self.channel}, "
            f"acknowledged_at={self.acknowledged_at}"
            f")>"
        )

    @property
    def is_digital_acknowledgment(self) -> bool:
        """Check if acknowledgment was captured digitally (stronger proof)"""
        return self.channel in [
            AcknowledgmentChannel.WEB,
            AcknowledgmentChannel.SMS,
            AcknowledgmentChannel.WHATSAPP,
            AcknowledgmentChannel.AI_CHAT,
            AcknowledgmentChannel.EMAIL,
        ]

    @property
    def is_verbal_acknowledgment(self) -> bool:
        """Check if acknowledgment was verbal (requires staff verification)"""
        return self.channel in [
            AcknowledgmentChannel.PHONE,
            AcknowledgmentChannel.IN_PERSON,
        ]
