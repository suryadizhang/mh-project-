"""
Email storage models for database persistence
Stores emails from IMAP for faster access, offline support, and advanced querying
"""

from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    JSON,
    Index,
)
from sqlalchemy.orm import relationship

from .base import BaseModel


class EmailMessage(BaseModel):
    """
    Individual email message stored in database
    Synced from IMAP servers (customer support and payments)
    """

    __tablename__ = "email_messages"

    # IMAP Identifiers
    message_id = Column(String(500), unique=True, nullable=False, index=True)
    """Unique message ID from email headers (Message-ID)"""

    imap_uid = Column(Integer, nullable=True, index=True)
    """IMAP UID for the message (may change if mailbox is rebuilt)"""

    thread_id = Column(String(500), nullable=True, index=True)
    """Thread ID for grouping related messages"""

    # Inbox/Folder
    inbox = Column(String(100), nullable=False, index=True)
    """Which inbox: 'customer_support' or 'payments'"""

    folder = Column(String(200), default="INBOX", nullable=False)
    """IMAP folder/label"""

    # Email Headers
    subject = Column(String(1000), nullable=True, index=True)
    """Email subject line"""

    from_address = Column(String(500), nullable=False, index=True)
    """Sender email address"""

    from_name = Column(String(500), nullable=True)
    """Sender display name"""

    to_addresses = Column(JSON, nullable=True)
    """List of recipient email addresses"""

    cc_addresses = Column(JSON, nullable=True)
    """List of CC email addresses"""

    bcc_addresses = Column(JSON, nullable=True)
    """List of BCC email addresses"""

    reply_to = Column(String(500), nullable=True)
    """Reply-to email address"""

    # Message Content
    text_body = Column(Text, nullable=True)
    """Plain text body"""

    html_body = Column(Text, nullable=True)
    """HTML body"""

    # Metadata
    received_at = Column(DateTime, nullable=False, index=True)
    """When the email was received (from email headers)"""

    sent_at = Column(DateTime, nullable=True)
    """When the email was sent (from Date header)"""

    # Flags and Status
    is_read = Column(Boolean, default=False, nullable=False, index=True)
    """Read/unread status"""

    is_starred = Column(Boolean, default=False, nullable=False, index=True)
    """Starred/flagged status"""

    is_archived = Column(Boolean, default=False, nullable=False, index=True)
    """Archived status"""

    is_spam = Column(Boolean, default=False, nullable=False)
    """Spam flag"""

    is_draft = Column(Boolean, default=False, nullable=False)
    """Draft flag"""

    is_sent = Column(Boolean, default=False, nullable=False)
    """Sent by us flag"""

    # Attachments
    has_attachments = Column(Boolean, default=False, nullable=False)
    """Whether the message has attachments"""

    attachments = Column(JSON, nullable=True)
    """
    List of attachment metadata:
    [{"filename": "doc.pdf", "size_bytes": 12345, "content_type": "application/pdf"}]
    """

    # Labels/Tags
    labels = Column(JSON, nullable=True)
    """Custom labels/tags: ["important", "follow-up", "urgent"]"""

    # Raw Data (for debugging/recovery)
    raw_headers = Column(JSON, nullable=True)
    """Raw email headers as JSON"""

    # Sync Metadata
    last_synced_at = Column(DateTime, nullable=True)
    """Last time this message was synced from IMAP"""

    sync_error = Column(Text, nullable=True)
    """Any sync errors encountered"""

    # Relationships
    thread = relationship(
        "EmailThread",
        back_populates="messages",
        foreign_keys="EmailMessage.thread_id",
        primaryjoin="EmailMessage.thread_id == EmailThread.thread_id",
    )

    # Indexes for performance
    __table_args__ = (
        Index("idx_inbox_received", "inbox", "received_at"),
        Index("idx_inbox_read_archived", "inbox", "is_read", "is_archived"),
        Index("idx_thread_received", "thread_id", "received_at"),
        Index("idx_from_address_received", "from_address", "received_at"),
    )

    def __repr__(self):
        return f"<EmailMessage(id={self.id}, message_id={self.message_id}, subject={self.subject[:50]})>"


class EmailThread(BaseModel):
    """
    Email conversation thread (group of related messages)
    """

    __tablename__ = "email_threads"

    # Thread Identifier
    thread_id = Column(String(500), unique=True, nullable=False, index=True)
    """Unique thread ID"""

    # Inbox
    inbox = Column(String(100), nullable=False, index=True)
    """Which inbox: 'customer_support' or 'payments'"""

    # Thread Metadata
    subject = Column(String(1000), nullable=True, index=True)
    """Thread subject (from first message)"""

    participants = Column(JSON, nullable=True)
    """
    List of all participants in thread:
    [{"email": "user@example.com", "name": "John Doe"}]
    """

    # Counts
    message_count = Column(Integer, default=0, nullable=False)
    """Total number of messages in thread"""

    unread_count = Column(Integer, default=0, nullable=False)
    """Number of unread messages"""

    # Timestamps
    first_message_at = Column(DateTime, nullable=True, index=True)
    """When the first message was received"""

    last_message_at = Column(DateTime, nullable=True, index=True)
    """When the last message was received"""

    # Thread Status
    is_read = Column(Boolean, default=False, nullable=False, index=True)
    """All messages read"""

    is_starred = Column(Boolean, default=False, nullable=False, index=True)
    """Thread is starred"""

    is_archived = Column(Boolean, default=False, nullable=False, index=True)
    """Thread is archived"""

    has_attachments = Column(Boolean, default=False, nullable=False)
    """Thread contains attachments"""

    # Labels
    labels = Column(JSON, nullable=True)
    """Thread labels/tags"""

    # Relationships
    messages = relationship(
        "EmailMessage",
        back_populates="thread",
        foreign_keys="EmailMessage.thread_id",
        primaryjoin="EmailThread.thread_id == EmailMessage.thread_id",
        order_by="EmailMessage.received_at.desc()",
    )

    # Indexes
    __table_args__ = (
        Index("idx_inbox_last_message", "inbox", "last_message_at"),
        Index("idx_inbox_read_archived", "inbox", "is_read", "is_archived"),
    )

    def __repr__(self):
        return f"<EmailThread(id={self.id}, thread_id={self.thread_id}, message_count={self.message_count})>"


class EmailSyncStatus(BaseModel):
    """
    Tracks IMAP sync status for each inbox
    """

    __tablename__ = "email_sync_status"

    # Inbox
    inbox = Column(String(100), unique=True, nullable=False, index=True)
    """Which inbox: 'customer_support' or 'payments'"""

    # Sync Status
    last_sync_at = Column(DateTime, nullable=True)
    """Last successful sync timestamp"""

    last_sync_uid = Column(Integer, nullable=True)
    """Last IMAP UID synced"""

    total_messages_synced = Column(Integer, default=0, nullable=False)
    """Total messages synced to database"""

    sync_errors = Column(Integer, default=0, nullable=False)
    """Number of sync errors encountered"""

    last_error = Column(Text, nullable=True)
    """Last sync error message"""

    last_error_at = Column(DateTime, nullable=True)
    """When the last error occurred"""

    # IMAP Connection Info
    imap_host = Column(String(200), nullable=True)
    """IMAP server hostname"""

    imap_folder = Column(String(200), default="INBOX", nullable=False)
    """IMAP folder being synced"""

    # Status
    is_syncing = Column(Boolean, default=False, nullable=False)
    """Whether sync is currently in progress"""

    is_enabled = Column(Boolean, default=True, nullable=False)
    """Whether sync is enabled for this inbox"""

    def __repr__(self):
        return f"<EmailSyncStatus(inbox={self.inbox}, last_sync={self.last_sync_at})>"
