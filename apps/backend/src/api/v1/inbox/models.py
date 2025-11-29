"""
Unified Inbox Database Models
Handles all communication channels: SMS, Email, WebSocket, Social Media
"""

from datetime import UTC, datetime
from enum import Enum
from typing import Any
from uuid import uuid4

# MIGRATED: from models.base → db.base_class (4 levels up from api/v1/inbox)
from db.base_class import Base
from sqlalchemy import (
    JSON,
    Boolean,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship


class MessageChannel(str, Enum):
    """Communication channel types"""

    SMS = "sms"
    EMAIL = "email"
    WEBSOCKET = "websocket"
    FACEBOOK = "facebook"
    INSTAGRAM = "instagram"
    TWITTER = "twitter"
    WHATSAPP = "whatsapp"


class MessageDirection(str, Enum):
    """Message direction"""

    INBOUND = "inbound"
    OUTBOUND = "outbound"


class MessageStatus(str, Enum):
    """Message processing status"""

    PENDING = "pending"
    DELIVERED = "delivered"
    FAILED = "failed"
    READ = "read"
    REPLIED = "replied"


class TCPAStatus(str, Enum):
    """TCPA compliance status"""

    OPTED_IN = "opted_in"
    OPTED_OUT = "opted_out"
    PENDING = "pending"


class InboxMessage(Base):
    """Unified message model for all communication channels"""

    __tablename__ = "inbox_messages"

    # Primary identifiers
    id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid4)

    # Channel and direction
    channel: Mapped[MessageChannel] = mapped_column(String(20), nullable=False)
    direction: Mapped[MessageDirection] = mapped_column(String(20), nullable=False)

    # Contact information
    contact_id: Mapped[UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("crm_contacts.id"), nullable=True
    )
    phone_number: Mapped[str | None] = mapped_column(String(20), nullable=True)
    email_address: Mapped[str | None] = mapped_column(String(255), nullable=True)
    social_handle: Mapped[str | None] = mapped_column(String(100), nullable=True)

    # Message content
    subject: Mapped[str | None] = mapped_column(String(255), nullable=True)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    content_type: Mapped[str] = mapped_column(String(50), default="text/plain")

    # Status and metadata
    status: Mapped[MessageStatus] = mapped_column(String(20), default=MessageStatus.PENDING)
    external_id: Mapped[str | None] = mapped_column(String(255), nullable=True)  # Provider ID
    message_metadata: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)

    # Threading and conversation
    thread_id: Mapped[UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("inbox_threads.id"), nullable=True
    )
    parent_message_id: Mapped[UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("inbox_messages.id"), nullable=True
    )

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC)
    )
    sent_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    delivered_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    read_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    # Relationships
    contact = relationship("Contact", back_populates="messages", lazy="select")
    thread = relationship("Thread", back_populates="messages")
    parent_message = relationship("InboxMessage", remote_side=[id])
    replies = relationship("InboxMessage", back_populates="parent_message")

    # Indexes for performance
    __table_args__ = (
        Index("idx_inbox_messages_channel", "channel"),
        Index("idx_inbox_messages_contact", "contact_id"),
        Index("idx_inbox_messages_thread", "thread_id"),
        Index("idx_inbox_messages_phone", "phone_number"),
        Index("idx_inbox_messages_email", "email_address"),
        Index("idx_inbox_messages_created", "created_at"),
        Index("idx_inbox_messages_status", "status"),
        CheckConstraint(
            "channel IN ('sms', 'email', 'websocket', 'facebook', 'instagram', 'twitter', 'whatsapp')",
            name="chk_valid_channel",
        ),
        CheckConstraint("direction IN ('inbound', 'outbound')", name="chk_valid_direction"),
    )


class Thread(Base):
    """Conversation thread grouping related messages"""

    __tablename__ = "inbox_threads"

    id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid4)

    # Thread identification
    subject: Mapped[str | None] = mapped_column(String(255), nullable=True)
    channel: Mapped[MessageChannel] = mapped_column(String(20), nullable=False)

    # Contact and booking association
    contact_id: Mapped[UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("crm_contacts.id"), nullable=True
    )
    booking_id: Mapped[UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("core.bookings.id"), nullable=True  # core schema
    )

    # Thread status
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    is_archived: Mapped[bool] = mapped_column(Boolean, default=False)

    # TCPA compliance
    tcpa_status: Mapped[TCPAStatus] = mapped_column(String(20), default=TCPAStatus.PENDING)
    tcpa_updated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    # Metadata
    thread_metadata: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),
    )
    last_message_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    # Relationships (temporarily commented booking for Bug #13 schema fixes)
    messages = relationship(
        "InboxMessage", back_populates="thread", order_by="InboxMessage.created_at"
    )
    contact = relationship("Contact", back_populates="threads", lazy="select")
    # booking = relationship("models.booking.Booking", back_populates="message_threads")

    # Indexes
    __table_args__ = (
        Index("idx_inbox_threads_contact", "contact_id"),
        Index("idx_inbox_threads_booking", "booking_id"),
        Index("idx_inbox_threads_channel", "channel"),
        Index("idx_inbox_threads_active", "is_active"),
        Index("idx_inbox_threads_tcpa", "tcpa_status"),
        Index("idx_inbox_threads_updated", "updated_at"),
    )


class TCPAOptStatus(Base):
    """TCPA opt-in/opt-out status tracking"""

    __tablename__ = "inbox_tcpa_status"

    id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid4)

    # Contact identification
    contact_id: Mapped[UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("crm_contacts.id"), nullable=True
    )
    phone_number: Mapped[str] = mapped_column(String(20), nullable=False)

    # Status tracking
    status: Mapped[TCPAStatus] = mapped_column(String(20), nullable=False)
    channel: Mapped[MessageChannel] = mapped_column(String(20), nullable=False)

    # Audit trail
    opt_in_method: Mapped[str | None] = mapped_column(
        String(100), nullable=True
    )  # web_form, sms_reply, etc.
    opt_in_source: Mapped[str | None] = mapped_column(
        String(255), nullable=True
    )  # URL, campaign, etc.

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),
    )

    # Relationships
    contact = relationship("Contact", back_populates="tcpa_statuses", lazy="select")

    # Constraints
    __table_args__ = (
        UniqueConstraint("phone_number", "channel", name="uq_tcpa_phone_channel"),
        Index("idx_tcpa_phone", "phone_number"),
        Index("idx_tcpa_status", "status"),
        Index("idx_tcpa_contact", "contact_id"),
    )


class WebSocketConnection(Base):
    """Active WebSocket connections for real-time messaging"""

    __tablename__ = "inbox_websocket_connections"

    id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid4)

    # Connection details
    connection_id: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    user_id: Mapped[UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("auth_users.id"), nullable=True
    )

    # Session information
    session_data: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)

    # Status
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    # Timestamps
    connected_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC)
    )
    last_ping_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    disconnected_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    # Indexes
    __table_args__ = (
        Index("idx_websocket_user", "user_id"),
        Index("idx_websocket_active", "is_active"),
        Index("idx_websocket_connected", "connected_at"),
    )
