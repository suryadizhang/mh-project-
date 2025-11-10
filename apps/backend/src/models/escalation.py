"""
Escalation Model - Customer Support Escalations
Handles customer requests for human intervention from AI chat
"""

import enum
import uuid

from models.base import Base
from sqlalchemy import Column, DateTime, ForeignKey, String, Text, func
from sqlalchemy import Enum as SQLEnum
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import relationship


class EscalationStatus(str, enum.Enum):
    """Escalation lifecycle status"""

    PENDING = "pending"  # Created, waiting for admin assignment
    ASSIGNED = "assigned"  # Assigned to a support admin
    IN_PROGRESS = "in_progress"  # Admin is handling the escalation
    WAITING_CUSTOMER = "waiting_customer"  # Waiting for customer response
    RESOLVED = "resolved"  # Escalation resolved, can resume AI
    CLOSED = "closed"  # Closed without resolution
    ERROR = "error"  # Failed to send notification or other error


class EscalationMethod(str, enum.Enum):
    """Preferred contact method for escalation"""

    SMS = "sms"  # Contact via SMS
    CALL = "call"  # Request phone call
    EMAIL = "email"  # Contact via email


class EscalationPriority(str, enum.Enum):
    """Priority level for escalation routing"""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"


class Escalation(Base):
    """
    Escalation Model - Tracks customer requests for human intervention

    When a customer needs human support:
    1. AI conversation is paused
    2. Escalation record created with contact info
    3. On-call admin notified via SMS/webhook
    4. Admin inbox shows escalation
    5. Admin handles via SMS/call/email
    6. Admin can resume AI when resolved
    """

    __tablename__ = "escalations"
    __table_args__ = {"schema": "support"}

    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)

    # Links to conversation and customer
    conversation_id = Column(
        UUID(as_uuid=True),
        ForeignKey("ai.conversations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    customer_id = Column(
        UUID(as_uuid=True),
        ForeignKey("bookings.customers.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    # Contact information
    phone = Column(String(20), nullable=False, index=True)  # Customer phone number
    email = Column(String(255), nullable=True)  # Optional email
    preferred_method = Column(
        SQLEnum(EscalationMethod, values_callable=lambda x: [e.value for e in x]),
        default=EscalationMethod.SMS,
        nullable=False,
    )

    # Escalation details
    reason = Column(Text, nullable=False)  # Why customer escalated
    priority = Column(
        SQLEnum(EscalationPriority, values_callable=lambda x: [e.value for e in x]),
        default=EscalationPriority.MEDIUM,
        nullable=False,
        index=True,
    )
    status = Column(
        SQLEnum(EscalationStatus, values_callable=lambda x: [e.value for e in x]),
        default=EscalationStatus.PENDING,
        nullable=False,
        index=True,
    )

    # Assignment
    assigned_to_id = Column(
        UUID(as_uuid=True),
        ForeignKey("identity.users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    assigned_at = Column(DateTime(timezone=True), nullable=True)

    # Resolution
    resolved_by_id = Column(
        UUID(as_uuid=True),
        ForeignKey("identity.users.id", ondelete="SET NULL"),
        nullable=True,
    )
    resolved_at = Column(DateTime(timezone=True), nullable=True)
    resolution_notes = Column(Text, nullable=True)

    # Communication tracking
    sms_sent = Column(DateTime(timezone=True), nullable=True)  # When SMS was sent to customer
    call_initiated = Column(DateTime(timezone=True), nullable=True)  # When call was made
    last_contact_at = Column(DateTime(timezone=True), nullable=True)  # Last interaction time

    # Error handling
    error_message = Column(Text, nullable=True)  # If notification failed
    retry_count = Column(String(10), default="0", nullable=False)  # SMS/call retry attempts

    # Metadata
    metadata = Column(JSONB, default={}, nullable=False)  # Additional context
    tags = Column(JSONB, default=[], nullable=False)  # Categorization tags

    # Timestamps
    created_at = Column(
        DateTime(timezone=True), server_default=func.now(), nullable=False, index=True
    )
    updated_at = Column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    # Consent
    customer_consent = Column(String(10), default="true", nullable=False)  # SMS/call consent

    # Relationships
    conversation = relationship("Conversation", back_populates="escalations", lazy="selectin")
    customer = relationship("Customer", back_populates="escalations", lazy="selectin")
    assigned_to = relationship(
        "User", foreign_keys=[assigned_to_id], backref="assigned_escalations", lazy="selectin"
    )
    resolved_by = relationship(
        "User", foreign_keys=[resolved_by_id], backref="resolved_escalations", lazy="selectin"
    )

    def __repr__(self):
        return f"<Escalation(id={self.id}, status={self.status}, phone={self.phone})>"

    def to_dict(self):
        return {
            "id": str(self.id),
            "conversation_id": str(self.conversation_id) if self.conversation_id else None,
            "customer_id": str(self.customer_id) if self.customer_id else None,
            "phone": self.phone,
            "email": self.email,
            "preferred_method": self.preferred_method,
            "reason": self.reason,
            "priority": self.priority,
            "status": self.status,
            "assigned_to_id": str(self.assigned_to_id) if self.assigned_to_id else None,
            "assigned_to": self.assigned_to.full_name if self.assigned_to else None,
            "resolved_by_id": str(self.resolved_by_id) if self.resolved_by_id else None,
            "resolved_by": self.resolved_by.full_name if self.resolved_by else None,
            "resolution_notes": self.resolution_notes,
            "error_message": self.error_message,
            "metadata": self.metadata,
            "tags": self.tags,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "resolved_at": self.resolved_at.isoformat() if self.resolved_at else None,
        }
