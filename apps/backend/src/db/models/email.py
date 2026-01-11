"""
Email storage models for database persistence (Modern SQLAlchemy 2.0)
Stores emails from IMAP for faster access, offline support, and advanced querying

Tables:
1. email_messages - Individual email messages
2. email_threads - Email conversation threads
3. email_sync_status - IMAP sync tracking
"""

from datetime import datetime
from typing import TYPE_CHECKING
from uuid import UUID, uuid4

from sqlalchemy import Boolean, DateTime, Index, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..base_class import Base

if TYPE_CHECKING:
    pass  # Add imports if relationships need typing


class EmailMessage(Base):
    """
    Individual email message stored in database
    Synced from IMAP servers (customer support and payments)
    """

    __tablename__ = "email_messages"
    __table_args__ = (
        Index("idx_inbox_received", "inbox", "received_at"),
        Index("idx_inbox_read_archived", "inbox", "is_read", "is_archived"),
        Index("idx_thread_received", "thread_id", "received_at"),
        Index("idx_from_address_received", "from_address", "received_at"),
        {"extend_existing": True},
    )

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)

    # IMAP Identifiers
    message_id: Mapped[str] = mapped_column(String(500), unique=True, index=True)
    """Unique message ID from email headers (Message-ID)"""

    imap_uid: Mapped[int | None] = mapped_column(Integer, index=True)
    """IMAP UID for the message"""

    thread_id: Mapped[str | None] = mapped_column(String(500), index=True)
    """Thread ID for grouping related messages"""

    # Inbox/Folder
    inbox: Mapped[str] = mapped_column(String(100), index=True)
    """Which inbox: 'customer_support' or 'payments'"""

    folder: Mapped[str] = mapped_column(String(200), default="INBOX")
    """IMAP folder/label"""

    # Email Headers
    subject: Mapped[str | None] = mapped_column(String(1000), index=True)
    """Email subject line"""

    from_address: Mapped[str] = mapped_column(String(500), index=True)
    """Sender email address"""

    from_name: Mapped[str | None] = mapped_column(String(500))
    """Sender display name"""

    to_addresses: Mapped[list] = mapped_column(JSONB, default=list)
    """List of recipient email addresses"""

    cc_addresses: Mapped[list] = mapped_column(JSONB, default=list)
    """List of CC email addresses"""

    bcc_addresses: Mapped[list] = mapped_column(JSONB, default=list)
    """List of BCC email addresses"""

    reply_to: Mapped[str | None] = mapped_column(String(500))
    """Reply-to email address"""

    # Message Content
    text_body: Mapped[str | None] = mapped_column(Text)
    """Plain text body"""

    html_body: Mapped[str | None] = mapped_column(Text)
    """HTML body"""

    # Metadata
    received_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    """When the email was received"""

    sent_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    """When the email was sent (from Date header)"""

    # Flags and Status
    is_read: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    """Read/unread status"""

    is_starred: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    """Starred/flagged status"""

    is_archived: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    """Archived status"""

    is_spam: Mapped[bool] = mapped_column(Boolean, default=False)
    """Spam flag"""

    is_draft: Mapped[bool] = mapped_column(Boolean, default=False)
    """Draft flag"""

    is_sent: Mapped[bool] = mapped_column(Boolean, default=False)
    """Sent by us flag"""

    is_deleted: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    """Soft delete flag (message moved to trash)"""

    # Attachments
    has_attachments: Mapped[bool] = mapped_column(Boolean, default=False)
    """Whether the message has attachments"""

    attachments: Mapped[list] = mapped_column(JSONB, default=list)
    """
    List of attachment metadata:
    [{"filename": "doc.pdf", "size_bytes": 12345, "content_type": "application/pdf"}]
    """

    # Labels/Tags
    labels: Mapped[list] = mapped_column(JSONB, default=list)
    """Custom labels/tags: ["important", "follow-up", "urgent"]"""

    # Raw Data (for debugging/recovery)
    raw_headers: Mapped[dict] = mapped_column(JSONB, default=dict)
    """Raw email headers as JSON"""

    # Sync Metadata
    last_synced_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    """Last time this message was synced from IMAP"""

    sync_error: Mapped[str | None] = mapped_column(Text)
    """Any sync errors encountered"""

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    # Relationships
    thread: Mapped["EmailThread"] = relationship(
        back_populates="messages",
        foreign_keys=[thread_id],
        primaryjoin="EmailMessage.thread_id == EmailThread.thread_id",
    )

    def __repr__(self):
        subject_preview = self.subject[:50] if self.subject else "No subject"
        return f"<EmailMessage(id={self.id}, subject={subject_preview})>"


class EmailThread(Base):
    """
    Email conversation thread (group of related messages)
    """

    __tablename__ = "email_threads"
    __table_args__ = (
        Index("idx_inbox_last_message", "inbox", "last_message_at"),
        Index("idx_inbox_read_archived", "inbox", "is_read", "is_archived"),
        {"extend_existing": True},
    )

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)

    # Thread Identifier
    thread_id: Mapped[str] = mapped_column(String(500), unique=True, index=True)
    """Unique thread ID"""

    # Inbox
    inbox: Mapped[str] = mapped_column(String(100), index=True)
    """Which inbox: 'customer_support' or 'payments'"""

    # Thread Metadata
    subject: Mapped[str | None] = mapped_column(String(1000), index=True)
    """Thread subject (from first message)"""

    participants: Mapped[list] = mapped_column(JSONB, default=list)
    """
    List of all participants in thread:
    [{"email": "user@example.com", "name": "John Doe"}]
    """

    # Counts
    message_count: Mapped[int] = mapped_column(Integer, default=0)
    """Total number of messages in thread"""

    unread_count: Mapped[int] = mapped_column(Integer, default=0)
    """Number of unread messages"""

    # Timestamps
    first_message_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), index=True)
    """When the first message was received"""

    last_message_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), index=True)
    """When the last message was received"""

    # Thread Status
    is_read: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    """All messages read"""

    is_starred: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    """Thread is starred"""

    is_archived: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    """Thread is archived"""

    is_deleted: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    """Soft delete flag (thread moved to trash)"""

    has_attachments: Mapped[bool] = mapped_column(Boolean, default=False)
    """Thread contains attachments"""

    # Labels
    labels: Mapped[list] = mapped_column(JSONB, default=list)
    """Thread labels/tags"""

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    # Relationships
    messages: Mapped[list["EmailMessage"]] = relationship(
        back_populates="thread",
        foreign_keys="EmailMessage.thread_id",
        primaryjoin="EmailThread.thread_id == EmailMessage.thread_id",
        order_by="EmailMessage.received_at.desc()",
    )

    def __repr__(self):
        return f"<EmailThread(id={self.id}, message_count={self.message_count})>"


class EmailSyncStatus(Base):
    """
    Tracks IMAP sync status for each inbox
    """

    __tablename__ = "email_sync_status"
    __table_args__ = {"extend_existing": True}

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)

    # Inbox
    inbox: Mapped[str] = mapped_column(String(100), unique=True, index=True)
    """Which inbox: 'customer_support' or 'payments'"""

    # Sync Status
    last_sync_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    """Last successful sync timestamp"""

    last_sync_uid: Mapped[int | None] = mapped_column(Integer)
    """Last IMAP UID synced"""

    total_messages_synced: Mapped[int] = mapped_column(Integer, default=0)
    """Total messages synced to database"""

    sync_errors: Mapped[int] = mapped_column(Integer, default=0)
    """Number of sync errors encountered"""

    last_error: Mapped[str | None] = mapped_column(Text)
    """Last sync error message"""

    last_error_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    """When the last error occurred"""

    # IMAP Connection Info
    imap_host: Mapped[str | None] = mapped_column(String(200))
    """IMAP server hostname"""

    imap_folder: Mapped[str] = mapped_column(String(200), default="INBOX")
    """IMAP folder being synced"""

    # Status
    is_syncing: Mapped[bool] = mapped_column(Boolean, default=False)
    """Whether sync is currently in progress"""

    is_enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    """Whether sync is enabled for this inbox"""

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    def __repr__(self):
        return f"<EmailSyncStatus(inbox={self.inbox}, last_sync={self.last_sync_at})>"
