"""
Call Recording Model - RingCentral Call Recording Storage
Stores metadata and links to call recordings from RingCentral
"""

import enum
import uuid
from datetime import datetime, timedelta

from models.base import Base
from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy import Enum as SQLEnum
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import relationship


class RecordingStatus(str, enum.Enum):
    """Recording processing status"""

    PENDING = "pending"  # Webhook received, not yet fetched
    DOWNLOADING = "downloading"  # Downloading from RingCentral
    AVAILABLE = "available"  # Available for playback
    ARCHIVED = "archived"  # Moved to cold storage
    DELETED = "deleted"  # Soft deleted, pending hard delete
    ERROR = "error"  # Failed to download or process


class RecordingType(str, enum.Enum):
    """Type of call recording"""

    INBOUND = "inbound"  # Customer calling business
    OUTBOUND = "outbound"  # Business calling customer
    INTERNAL = "internal"  # Internal calls between staff


class CallRecording(Base):
    """
    Call Recording Model - Tracks voice call recordings from RingCentral

    Lifecycle:
    1. RingCentral webhook: recording.completed
    2. Create record with status=PENDING
    3. Worker job downloads from RingCentral, uploads to S3
    4. Update status=AVAILABLE, set s3_uri
    5. Admin can play/download via UI
    6. Retention policy auto-deletes after N days
    """

    __tablename__ = "call_recordings"
    __table_args__ = {"schema": "communications"}

    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)

    # RingCentral identifiers
    rc_call_id = Column(String(100), unique=True, nullable=False, index=True)  # RC call session ID
    rc_recording_id = Column(
        String(100), unique=True, nullable=False, index=True
    )  # RC recording ID
    rc_recording_uri = Column(Text, nullable=False)  # RC API URI to fetch recording

    # Business context
    booking_id = Column(
        UUID(as_uuid=True),
        ForeignKey("bookings.bookings.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    customer_id = Column(
        UUID(as_uuid=True),
        ForeignKey("bookings.customers.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    escalation_id = Column(
        UUID(as_uuid=True),
        ForeignKey("support.escalations.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    agent_id = Column(
        UUID(as_uuid=True),
        ForeignKey("identity.users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    # Call details
    call_type = Column(
        SQLEnum(RecordingType, values_callable=lambda x: [e.value for e in x]),
        default=RecordingType.INBOUND,
        nullable=False,
        index=True,
    )
    from_phone = Column(String(20), nullable=False, index=True)  # Caller phone
    to_phone = Column(String(20), nullable=False, index=True)  # Recipient phone
    duration_seconds = Column(Integer, nullable=False, default=0)  # Call duration
    call_started_at = Column(DateTime(timezone=True), nullable=False, index=True)
    call_ended_at = Column(DateTime(timezone=True), nullable=True)

    # Storage
    status = Column(
        SQLEnum(RecordingStatus, values_callable=lambda x: [e.value for e in x]),
        default=RecordingStatus.PENDING,
        nullable=False,
        index=True,
    )
    s3_bucket = Column(String(255), nullable=True)  # S3 bucket name
    s3_key = Column(String(500), nullable=True)  # S3 object key
    s3_uri = Column(Text, nullable=True)  # Full S3 URI for access
    file_size_bytes = Column(Integer, nullable=True)  # File size
    content_type = Column(String(100), nullable=True)  # audio/mpeg, audio/wav, etc.

    # Metadata
    metadata = Column(JSONB, default={}, nullable=False)  # Additional context
    tags = Column(JSONB, default=[], nullable=False)  # Categorization

    # Retention policy
    retention_days = Column(Integer, default=90, nullable=False)  # Days to keep
    delete_after = Column(DateTime(timezone=True), nullable=True, index=True)  # Auto-delete date

    # Access control
    accessed_count = Column(Integer, default=0, nullable=False)  # Play/download count
    last_accessed_at = Column(DateTime(timezone=True), nullable=True)
    last_accessed_by_id = Column(
        UUID(as_uuid=True),
        ForeignKey("identity.users.id", ondelete="SET NULL"),
        nullable=True,
    )

    # Error handling
    error_message = Column(Text, nullable=True)
    download_attempts = Column(Integer, default=0, nullable=False)

    # Timestamps
    created_at = Column(
        DateTime(timezone=True), server_default=func.now(), nullable=False, index=True
    )
    updated_at = Column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )
    downloaded_at = Column(DateTime(timezone=True), nullable=True)  # When fetched from RC
    archived_at = Column(DateTime(timezone=True), nullable=True)
    deleted_at = Column(DateTime(timezone=True), nullable=True)  # Soft delete timestamp

    # Relationships
    booking = relationship("Booking", back_populates="call_recordings", lazy="selectin")
    customer = relationship("Customer", back_populates="call_recordings", lazy="selectin")
    escalation = relationship("Escalation", backref="call_recordings", lazy="selectin")
    agent = relationship(
        "User", foreign_keys=[agent_id], backref="call_recordings", lazy="selectin"
    )
    last_accessed_by = relationship(
        "User", foreign_keys=[last_accessed_by_id], backref="accessed_recordings", lazy="selectin"
    )

    def __repr__(self):
        return f"<CallRecording(id={self.id}, rc_call_id={self.rc_call_id}, status={self.status})>"

    def to_dict(self):
        return {
            "id": str(self.id),
            "rc_call_id": self.rc_call_id,
            "rc_recording_id": self.rc_recording_id,
            "booking_id": str(self.booking_id) if self.booking_id else None,
            "customer_id": str(self.customer_id) if self.customer_id else None,
            "escalation_id": str(self.escalation_id) if self.escalation_id else None,
            "agent_id": str(self.agent_id) if self.agent_id else None,
            "agent_name": self.agent.full_name if self.agent else None,
            "call_type": self.call_type,
            "from_phone": self.from_phone,
            "to_phone": self.to_phone,
            "duration_seconds": self.duration_seconds,
            "status": self.status,
            "s3_uri": self.s3_uri,
            "file_size_bytes": self.file_size_bytes,
            "content_type": self.content_type,
            "retention_days": self.retention_days,
            "delete_after": self.delete_after.isoformat() if self.delete_after else None,
            "accessed_count": self.accessed_count,
            "last_accessed_at": (
                self.last_accessed_at.isoformat() if self.last_accessed_at else None
            ),
            "metadata": self.metadata,
            "tags": self.tags,
            "call_started_at": self.call_started_at.isoformat() if self.call_started_at else None,
            "call_ended_at": self.call_ended_at.isoformat() if self.call_ended_at else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "downloaded_at": self.downloaded_at.isoformat() if self.downloaded_at else None,
        }

    def set_retention_policy(self, days: int = None):
        """Set or update retention policy and calculate delete_after date"""
        if days is not None:
            self.retention_days = days
        self.delete_after = datetime.utcnow() + timedelta(days=self.retention_days)

    def is_expired(self) -> bool:
        """Check if recording has passed retention period"""
        if not self.delete_after:
            return False
        return datetime.utcnow() >= self.delete_after

    def record_access(self, user_id: UUID):
        """Track access for audit purposes"""
        self.accessed_count += 1
        self.last_accessed_at = datetime.utcnow()
        self.last_accessed_by_id = user_id
