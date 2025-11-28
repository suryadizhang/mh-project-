"""
Call Recording Metadata - RingCentral Integration

This module stores ONLY metadata and references to call recordings from RingCentral.
Actual recordings are stored and managed by RingCentral.

Architecture:
- Pure metadata tracking (no audio storage)
- RingCentral is the source of truth for recordings
- Fetch recordings on-demand from RingCentral API
- Optional caching in S3 for faster playback (temporary)

Workflow:
1. RingCentral webhook: recording.completed → Create record (status=PENDING)
2. Worker job: Fetch metadata from RingCentral (status=AVAILABLE)
3. Optional: Download to S3 for temporary cache
4. Admin UI: Playback/download via RingCentral API or S3 cache
5. Retention: Auto-delete metadata after N days

Business Requirements:
- Track all customer call recordings
- Link recordings to bookings/customers/escalations
- RingCentral AI transcription and insights
- Retention policy compliance
- Access audit trail

Schema: public (cross-functional)
Table: call_recordings
"""

from datetime import datetime, timedelta, timezone
from enum import Enum
import uuid

from sqlalchemy import (
    DateTime,
    Integer,
    String,
    Text,
)
from sqlalchemy import Enum as SQLEnum
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

# MIGRATED: from models.base → ..base_class
from ..base_class import Base


# ============================================================================
# ENUMS
# ============================================================================


class RecordingStatus(str, Enum):
    """Recording metadata processing status"""

    PENDING = "pending"  # Webhook received, metadata not yet fetched
    FETCHING = "fetching"  # Fetching metadata from RingCentral
    AVAILABLE = "available"  # Metadata available, can fetch recording on-demand
    CACHED = "cached"  # Temporarily cached in S3 for faster playback
    ARCHIVED = "archived"  # Metadata archived (old recording)
    DELETED = "deleted"  # Soft deleted, pending cleanup
    ERROR = "error"  # Failed to fetch metadata


class CallDirection(str, Enum):
    """Call direction"""

    INBOUND = "inbound"  # Customer calling business
    OUTBOUND = "outbound"  # Business calling customer
    INTERNAL = "internal"  # Internal calls between staff


class CallType(str, Enum):
    """Type of call recording"""

    INBOUND = "inbound"  # Customer inquiry/booking
    OUTBOUND = "outbound"  # Follow-up/confirmation
    INTERNAL = "internal"  # Team communication


# Backward compatibility alias
RecordingType = CallType  # OLD name, use CallType instead


class CallStatus(str, Enum):
    """Real-time call status tracking"""

    RINGING = "ringing"  # Call is ringing
    IN_PROGRESS = "in_progress"  # Call is ongoing
    CONNECTED = "connected"  # Call connected
    COMPLETED = "completed"  # Call ended normally
    TRANSFERRED = "transferred"  # Call transferred to another agent
    VOICEMAIL = "voicemail"  # Call went to voicemail
    MISSED = "missed"  # Call not answered
    FAILED = "failed"  # Call failed to connect
    ERROR = "error"  # Call error


# ============================================================================
# MODELS
# ============================================================================


class CallRecording(Base):
    """
    Call Recording Metadata - RingCentral Reference Model

    Stores metadata ONLY. Actual recordings fetched on-demand from RingCentral.

    Lifecycle:
    1. RingCentral webhook → Create record (status=PENDING)
    2. Fetch metadata from RingCentral → status=AVAILABLE
    3. Optional S3 cache for faster playback → status=CACHED
    4. Retention policy auto-marks for deletion
    5. Background job deletes metadata after retention period

    NO AUDIO STORAGE - Pure reference model
    """

    __tablename__ = "call_recordings"

    # Primary key
    id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # RingCentral identifiers (source of truth)
    rc_call_id: Mapped[str] = mapped_column(
        String(100), unique=True, nullable=False, index=True
    )  # RC session ID
    rc_recording_id: Mapped[str] = mapped_column(
        String(100), unique=True, nullable=False, index=True
    )  # RC recording ID
    rc_recording_uri: Mapped[str] = mapped_column(
        Text, nullable=False
    )  # RC API URI to fetch recording

    # Business context (UUIDs for reference, no FK constraints - RingCentral is external)
    booking_id: Mapped[UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True, index=True)
    customer_id: Mapped[UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True, index=True)
    escalation_id: Mapped[UUID | None] = mapped_column(
        UUID(as_uuid=True), nullable=True, index=True
    )

    # Call details
    call_type: Mapped[CallType] = mapped_column(
        SQLEnum(CallType, values_callable=lambda x: [e.value for e in x]),
        default=CallType.INBOUND,
        nullable=False,
        index=True,
    )
    call_direction: Mapped[CallDirection] = mapped_column(
        SQLEnum(CallDirection, values_callable=lambda x: [e.value for e in x]),
        default=CallDirection.INBOUND,
        nullable=False,
        index=True,
    )
    from_phone: Mapped[str] = mapped_column(String(20), nullable=False, index=True)
    to_phone: Mapped[str] = mapped_column(String(20), nullable=False, index=True)
    duration_seconds: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    call_started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    call_ended_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    # Metadata status
    status: Mapped[RecordingStatus] = mapped_column(
        SQLEnum(RecordingStatus, values_callable=lambda x: [e.value for e in x]),
        default=RecordingStatus.PENDING,
        nullable=False,
        index=True,
    )

    # Optional S3 cache (temporary storage for faster playback)
    # NOTE: This is OPTIONAL cache only - RingCentral is always the source of truth
    s3_bucket: Mapped[str | None] = mapped_column(String(255), nullable=True)
    s3_key: Mapped[str | None] = mapped_column(String(500), nullable=True)
    s3_uri: Mapped[str | None] = mapped_column(Text, nullable=True)
    s3_cached_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    s3_cache_expires_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )  # Cache TTL

    # File metadata
    file_size_bytes: Mapped[int | None] = mapped_column(Integer, nullable=True)
    content_type: Mapped[str | None] = mapped_column(
        String(100), nullable=True
    )  # audio/mpeg, audio/wav

    # RingCentral AI Transcription
    rc_transcript: Mapped[str | None] = mapped_column(Text, nullable=True)
    rc_transcript_confidence: Mapped[int | None] = mapped_column(
        Integer, nullable=True
    )  # 0-100 score
    rc_transcript_fetched_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    # RingCentral AI Insights (sentiment, topics, action items)
    rc_ai_insights: Mapped[dict] = mapped_column(
        JSONB, default=dict, nullable=False
    )  # {sentiment, topics, action_items, intent, speakers, keywords}

    # Additional metadata
    recording_metadata: Mapped[dict] = mapped_column(JSONB, default=dict, nullable=False)
    tags: Mapped[list] = mapped_column(JSONB, default=list, nullable=False)

    # Retention policy (compliance)
    retention_days: Mapped[int] = mapped_column(Integer, default=90, nullable=False)
    delete_after: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True, index=True
    )

    # Access audit trail
    accessed_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    last_accessed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    # Error handling
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    fetch_attempts: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
        index=True,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    metadata_fetched_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    archived_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    def __repr__(self):
        return f"<CallRecording(id={self.id}, rc_call_id={self.rc_call_id}, status={self.status})>"

    def to_dict(self):
        """Convert to dictionary for API responses"""
        return {
            "id": str(self.id),
            "rc_call_id": self.rc_call_id,
            "rc_recording_id": self.rc_recording_id,
            "rc_recording_uri": self.rc_recording_uri,
            "booking_id": str(self.booking_id) if self.booking_id else None,
            "customer_id": str(self.customer_id) if self.customer_id else None,
            "escalation_id": str(self.escalation_id) if self.escalation_id else None,
            "call_type": self.call_type.value,
            "call_direction": self.call_direction.value,
            "from_phone": self.from_phone,
            "to_phone": self.to_phone,
            "duration_seconds": self.duration_seconds,
            "status": self.status.value,
            "s3_uri": self.s3_uri,
            "s3_cache_expires_at": (
                self.s3_cache_expires_at.isoformat() if self.s3_cache_expires_at else None
            ),
            "file_size_bytes": self.file_size_bytes,
            "content_type": self.content_type,
            "rc_transcript": self.rc_transcript,
            "rc_transcript_confidence": self.rc_transcript_confidence,
            "rc_ai_insights": self.rc_ai_insights,
            "retention_days": self.retention_days,
            "delete_after": self.delete_after.isoformat() if self.delete_after else None,
            "accessed_count": self.accessed_count,
            "last_accessed_at": (
                self.last_accessed_at.isoformat() if self.last_accessed_at else None
            ),
            "recording_metadata": self.recording_metadata,
            "tags": self.tags,
            "call_started_at": self.call_started_at.isoformat(),
            "call_ended_at": self.call_ended_at.isoformat() if self.call_ended_at else None,
            "created_at": self.created_at.isoformat(),
            "metadata_fetched_at": (
                self.metadata_fetched_at.isoformat() if self.metadata_fetched_at else None
            ),
        }

    def set_retention_policy(self, days: int | None = None):
        """Set or update retention policy and calculate delete_after date"""
        if days is not None:
            self.retention_days = days
        self.delete_after = datetime.now(timezone.utc) + timedelta(days=self.retention_days)

    def is_expired(self) -> bool:
        """Check if recording metadata has passed retention period"""
        if not self.delete_after:
            return False
        return datetime.now(timezone.utc) >= self.delete_after

    def is_cache_expired(self) -> bool:
        """Check if S3 cache has expired (if cached)"""
        if not self.s3_cache_expires_at:
            return True  # No cache
        return datetime.now(timezone.utc) >= self.s3_cache_expires_at

    def record_access(self):
        """Track access for audit purposes"""
        self.accessed_count += 1
        self.last_accessed_at = datetime.now(timezone.utc)

    def set_cache(self, s3_bucket: str, s3_key: str, s3_uri: str, cache_ttl_hours: int = 24):
        """Set S3 cache location with TTL"""
        self.s3_bucket = s3_bucket
        self.s3_key = s3_key
        self.s3_uri = s3_uri
        self.s3_cached_at = datetime.now(timezone.utc)
        self.s3_cache_expires_at = datetime.now(timezone.utc) + timedelta(hours=cache_ttl_hours)
        self.status = RecordingStatus.CACHED

    def clear_cache(self):
        """Clear S3 cache (keep metadata)"""
        self.s3_bucket = None
        self.s3_key = None
        self.s3_uri = None
        self.s3_cached_at = None
        self.s3_cache_expires_at = None
        if self.status == RecordingStatus.CACHED:
            self.status = RecordingStatus.AVAILABLE
