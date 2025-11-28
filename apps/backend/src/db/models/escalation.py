"""
Escalation Model - Customer Support Escalations (Modern SQLAlchemy 2.0)
Handles customer requests for human intervention from AI chat

Architecture:
- AI conversation paused when customer escalates
- Admin notified via SMS/webhook/email
- Admin handles via preferred contact method
- Admin can resume AI when resolved
"""

import enum
from datetime import datetime
from typing import TYPE_CHECKING
from uuid import UUID, uuid4

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy import Enum as SQLEnum
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..base_class import Base

if TYPE_CHECKING:
    from .core import Customer


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
    WHATSAPP = "whatsapp"  # Contact via WhatsApp


class EscalationPriority(str, enum.Enum):
    """Priority level for escalation routing"""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"


class Escalation(Base):
    """
    Escalation Model - Tracks customer requests for human intervention

    Workflow:
    1. AI conversation is paused
    2. Escalation record created with contact info
    3. On-call admin notified via SMS/webhook
    4. Admin inbox shows escalation
    5. Admin handles via SMS/call/email
    6. Admin can resume AI when resolved
    """

    __tablename__ = "escalations"
    __table_args__ = {"extend_existing": True}

    # Primary key
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4, index=True)

    # Links to conversation and customer (no FK - external systems)
    conversation_id: Mapped[UUID | None] = mapped_column(index=True)
    customer_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("core.customers.id", ondelete="SET NULL"),
        index=True,
    )

    # Contact information
    phone: Mapped[str] = mapped_column(String(20), index=True)
    email: Mapped[str | None] = mapped_column(String(255))
    preferred_method: Mapped[EscalationMethod] = mapped_column(
        SQLEnum(EscalationMethod, values_callable=lambda x: [e.value for e in x]),
        default=EscalationMethod.SMS,
    )

    # Escalation details
    reason: Mapped[str] = mapped_column(Text)
    priority: Mapped[EscalationPriority] = mapped_column(
        SQLEnum(EscalationPriority, values_callable=lambda x: [e.value for e in x]),
        default=EscalationPriority.MEDIUM,
        index=True,
    )
    status: Mapped[EscalationStatus] = mapped_column(
        SQLEnum(EscalationStatus, values_callable=lambda x: [e.value for e in x]),
        default=EscalationStatus.PENDING,
        index=True,
    )

    # Assignment (no FK - User model in different context)
    assigned_to_id: Mapped[UUID | None] = mapped_column(index=True)
    assigned_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    # Resolution (no FK - User model in different context)
    resolved_by_id: Mapped[UUID | None]
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    resolution_notes: Mapped[str | None] = mapped_column(Text)

    # Communication tracking
    admin_notified_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    admin_notification_sid: Mapped[str | None] = mapped_column(String(100))  # Twilio SID
    admin_notification_status: Mapped[str | None] = mapped_column(
        String(20)
    )  # delivered, read, failed
    admin_notification_channel: Mapped[str | None] = mapped_column(
        String(20)
    )  # whatsapp, sms, email

    sms_sent: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    call_initiated: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    last_contact_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    # Error handling
    error_message: Mapped[str | None] = mapped_column(Text)
    retry_count: Mapped[int] = mapped_column(Integer, default=0)

    # Additional data (JSONB)
    escalation_metadata: Mapped[dict] = mapped_column(JSONB, default=dict)
    tags: Mapped[list] = mapped_column(JSONB, default=list)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), index=True
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    # Consent
    customer_consent: Mapped[bool] = mapped_column(default=True)

    # Relationships
    customer: Mapped["Customer"] = relationship(
        "Customer", back_populates="escalations", lazy="selectin"
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
            "preferred_method": self.preferred_method.value if self.preferred_method else None,
            "reason": self.reason,
            "priority": self.priority.value if self.priority else None,
            "status": self.status.value if self.status else None,
            "assigned_to_id": str(self.assigned_to_id) if self.assigned_to_id else None,
            "resolved_by_id": str(self.resolved_by_id) if self.resolved_by_id else None,
            "resolution_notes": self.resolution_notes,
            "error_message": self.error_message,
            "escalation_metadata": self.escalation_metadata,
            "tags": self.tags,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "resolved_at": self.resolved_at.isoformat() if self.resolved_at else None,
        }
