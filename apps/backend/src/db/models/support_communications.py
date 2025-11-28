"""
SQLAlchemy Models - Support & Communications Schemas
====================================================

Support Schema:
- Escalations (AI to human handoff)

Communications Schema:
- Call Recordings (RingCentral integration)

All models use:
- UUID primary keys
- Timezone-aware datetime fields
- Schema qualification (__table_args__)
- Proper foreign key relationships
- Type hints for IDE support
"""

from datetime import datetime
from typing import Optional
from uuid import UUID, uuid4

from sqlalchemy import (
    String,
    Text,
    Integer,
    BigInteger,
    Boolean,
    DateTime,
    ForeignKey,
    Index,
    Enum as SQLEnum,
)
from sqlalchemy.dialects.postgresql import UUID as PGUUID, JSONB
from sqlalchemy.orm import relationship, Mapped, mapped_column
from sqlalchemy.sql import func

from ..base_class import Base


# ==================== ENUMS ====================

import enum


class EscalationPriority(str, enum.Enum):
    """Escalation priority levels"""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"


class EscalationMethod(str, enum.Enum):
    """Escalation contact methods"""

    PHONE = "phone"
    EMAIL = "email"
    PREFERRED_METHOD = "preferred_method"


class EscalationStatus(str, enum.Enum):
    """Escalation workflow status"""

    PENDING = "pending"
    ASSIGNED = "assigned"
    IN_PROGRESS = "in_progress"
    WAITING_CUSTOMER = "waiting_customer"
    RESOLVED = "resolved"
    CLOSED = "closed"
    ERROR = "error"


class RecordingType(str, enum.Enum):
    """Call recording types"""

    INBOUND = "inbound"
    OUTBOUND = "outbound"
    INTERNAL = "internal"


class RecordingStatus(str, enum.Enum):
    """Recording processing status"""

    PENDING = "pending"
    DOWNLOADING = "downloading"
    AVAILABLE = "available"
    ARCHIVED = "archived"
    DELETED = "deleted"
    ERROR = "error"


# ==================== SUPPORT SCHEMA ====================


class Escalation(Base):
    """
    Escalation entity

    Tracks AI to human escalations with customer contact info,
    priority, assignment, and resolution workflow.
    """

    __tablename__ = "escalations"
    __table_args__ = (
        Index("idx_escalations_conversation_id", "conversation_id"),
        Index("idx_escalations_customer_phone", "customer_phone"),
        Index("idx_escalations_status", "status"),
        Index("idx_escalations_assigned_to_id", "assigned_to_id"),
        Index("idx_escalations_created_at", "created_at"),
        Index("idx_escalations_status_priority", "status", "priority"),
        Index("idx_escalations_assigned_status", "assigned_to_id", "status"),
        {"schema": "support"},
    )

    # Primary Key
    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)

    # Foreign Keys
    assigned_to_id: Mapped[Optional[UUID]] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey(
            "identity.users.id", ondelete="SET NULL"
        ),  # Fixed: users table is in identity schema
        nullable=True,
        index=True,
    )

    # Conversation Reference
    conversation_id: Mapped[str] = mapped_column(String(255), nullable=False, index=True)

    # Customer Info
    customer_name: Mapped[str] = mapped_column(String(255), nullable=False)
    customer_phone: Mapped[str] = mapped_column(String(20), nullable=False, index=True)
    customer_email: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    # Escalation Details
    reason: Mapped[str] = mapped_column(Text, nullable=False)
    priority: Mapped[EscalationPriority] = mapped_column(
        SQLEnum(
            EscalationPriority, name="escalation_priority", schema="support", create_type=False
        ),
        nullable=False,
        server_default="medium",
    )
    method: Mapped[EscalationMethod] = mapped_column(
        SQLEnum(EscalationMethod, name="escalation_method", schema="support", create_type=False),
        nullable=False,
        server_default="phone",
    )
    status: Mapped[EscalationStatus] = mapped_column(
        SQLEnum(EscalationStatus, name="escalation_status", schema="support", create_type=False),
        nullable=False,
        server_default="pending",
        index=True,
    )

    # Workflow Timestamps
    assigned_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    escalated_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    resolved_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    # Resolution
    resolution_notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    resume_ai_chat: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="false")

    # Customer Response Tracking
    last_customer_response_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    # Communication Tracking
    sms_sent: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="false")
    sms_sent_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    call_initiated: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="false")
    call_initiated_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    # Error Handling
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    retry_count: Mapped[int] = mapped_column(Integer, nullable=False, server_default="0")

    # Metadata
    escalation_metadata: Mapped[dict] = mapped_column(JSONB, nullable=False, server_default="{}")

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now()
    )

    # Relationships
    call_recordings: Mapped[list["CallRecording"]] = relationship(
        "CallRecording", back_populates="escalation", foreign_keys="CallRecording.escalation_id"
    )


# ==================== COMMUNICATIONS SCHEMA ====================


class CallRecording(Base):
    """
    Call recording entity

    Metadata for RingCentral call recordings with retention policy,
    access audit, and S3 storage details.
    """

    __tablename__ = "call_recordings"
    __table_args__ = (
        Index("idx_call_recordings_escalation_id", "escalation_id"),
        Index("idx_call_recordings_rc_call_id", "rc_call_id"),
        Index("idx_call_recordings_status", "status"),
        Index("idx_call_recordings_call_started_at", "call_started_at"),
        Index("idx_call_recordings_delete_after", "delete_after"),
        Index("idx_call_recordings_date_status", "call_started_at", "status"),
        {"schema": "communications"},
    )

    # Primary Key
    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)

    # Foreign Keys
    escalation_id: Mapped[Optional[UUID]] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("support.escalations.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    last_accessed_by_id: Mapped[Optional[UUID]] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey(
            "identity.users.id", ondelete="SET NULL"
        ),  # Fixed: users table is in identity schema
        nullable=True,
    )

    # RingCentral Details
    rc_call_id: Mapped[str] = mapped_column(String(255), nullable=False, unique=True, index=True)
    rc_recording_id: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    rc_recording_uri: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)

    # Recording Details
    recording_type: Mapped[RecordingType] = mapped_column(
        SQLEnum(RecordingType, name="recording_type", schema="communications", create_type=False),
        nullable=False,
        server_default="inbound",
    )
    status: Mapped[RecordingStatus] = mapped_column(
        SQLEnum(
            RecordingStatus, name="recording_status", schema="communications", create_type=False
        ),
        nullable=False,
        server_default="pending",
        index=True,
    )

    # Call Metadata
    call_started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, index=True
    )
    duration_seconds: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    # File Details
    file_size_bytes: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    content_type: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)

    # S3 Storage
    s3_bucket: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    s3_key: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    s3_uri: Mapped[Optional[str]] = mapped_column(String(1000), nullable=True)

    # Retention Policy
    retention_days: Mapped[int] = mapped_column(Integer, nullable=False, server_default="90")
    delete_after: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True, index=True
    )

    # Processing Timestamps
    downloaded_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    archived_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    deleted_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    # Error Handling
    download_attempts: Mapped[int] = mapped_column(Integer, nullable=False, server_default="0")
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Access Audit
    accessed_count: Mapped[int] = mapped_column(Integer, nullable=False, server_default="0")
    last_accessed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    # Metadata
    recording_metadata: Mapped[dict] = mapped_column(JSONB, nullable=False, server_default="{}")

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now()
    )

    # Relationships
    escalation: Mapped[Optional["Escalation"]] = relationship(
        "Escalation", back_populates="call_recordings", foreign_keys=[escalation_id]
    )
