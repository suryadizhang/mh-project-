"""
CRM Contact model for unified inbox and customer relationship management
"""

from datetime import UTC, datetime
from uuid import uuid4

from sqlalchemy import Boolean, Column, DateTime, String, Text, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from .base import Base


class Contact(Base):
    """
    CRM Contact model - unified contact record for all communication channels.
    Links to Customer model for existing customers, but can exist independently
    for leads and prospects who haven't booked yet.
    """

    __tablename__ = "crm_contacts"

    # Primary identifier (UUID for distributed systems)
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)

    # Basic information
    first_name = Column(String(100), nullable=True)
    last_name = Column(String(100), nullable=True)
    email = Column(String(255), nullable=True, index=True)
    phone_number = Column(String(20), nullable=True, index=True)

    # Social media handles
    facebook_handle = Column(String(100), nullable=True)
    instagram_handle = Column(String(100), nullable=True)
    twitter_handle = Column(String(100), nullable=True)

    # Contact metadata
    contact_source = Column(String(50), nullable=True)  # web_form, phone_call, social_media, etc.
    contact_notes = Column(Text, nullable=True)
    contact_metadata = Column(JSON, nullable=True)  # Flexible storage for additional data

    # Status
    is_active = Column(Boolean, default=True, nullable=False)
    is_verified = Column(Boolean, default=False, nullable=False)  # Email/phone verified

    # Link to Customer (if they've booked)
    # Note: customer_id relationship will be added in future migration when linking is needed
    # For now, contacts can exist independently

    # Timestamps
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False)
    updated_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),
        nullable=False,
    )
    last_contacted_at = Column(DateTime(timezone=True), nullable=True)

    # Relationships
    messages = relationship("api.v1.inbox.models.InboxMessage", back_populates="contact", lazy="select")
    threads = relationship("api.v1.inbox.models.Thread", back_populates="contact", lazy="select")
    tcpa_statuses = relationship("api.v1.inbox.models.TCPAOptStatus", back_populates="contact", lazy="select")

    def __repr__(self):
        name = f"{self.first_name} {self.last_name}".strip() or "Unknown"
        return f"<Contact(id={self.id}, name={name}, email={self.email})>"

    @property
    def full_name(self):
        """Return full name or fallback identifier"""
        if self.first_name and self.last_name:
            return f"{self.first_name} {self.last_name}"
        elif self.first_name:
            return self.first_name
        elif self.last_name:
            return self.last_name
        elif self.email:
            return self.email
        elif self.phone_number:
            return self.phone_number
        return "Unknown Contact"
