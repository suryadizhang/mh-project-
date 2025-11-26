"""Add email storage tables for database persistence

Revision ID: 20251124_email_storage
Revises: 20250113_fix_race
Create Date: 2025-11-24

Email Storage in Database
==========================

Purpose:
--------
Store emails from IMAP servers (customer support and payments) in PostgreSQL
for faster access, offline support, advanced querying, and better UX.

Benefits:
---------
1. **Fast Loading**: No IMAP fetch delays, instant UI response
2. **Offline Access**: View emails even when IMAP is down
3. **Advanced Search**: Full-text search, date ranges, complex queries
4. **Better UX**: Pagination, sorting, filtering without IMAP limitations
5. **Analytics**: Track response times, email volume, customer patterns
6. **Caching**: Reduce IMAP server load and API rate limits
7. **Reliability**: Survive IMAP connection issues gracefully

Tables:
-------
1. email_messages: Individual email messages
2. email_threads: Conversation threads (grouped messages)
3. email_sync_status: Track sync status per inbox

Features:
---------
- Message-ID based deduplication
- Thread grouping by subject/references
- Full metadata storage (headers, flags, attachments)
- Labels/tags support
- Sync error tracking
- Performance indexes for common queries

Migration Actions:
------------------
1. Create email_messages table
2. Create email_threads table
3. Create email_sync_status table
4. Add indexes for performance
5. Initialize sync status records
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSON


revision = '20251124_email_storage'
down_revision = '20250113_fix_race'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """
    Create email storage tables
    """

    # 1. Create email_threads table (must be first for foreign key)
    op.create_table(
        'email_threads',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.Column('is_deleted', sa.Boolean(), nullable=False, server_default='false'),

        # Thread Identifier
        sa.Column('thread_id', sa.String(500), nullable=False),
        sa.Column('inbox', sa.String(100), nullable=False),

        # Thread Metadata
        sa.Column('subject', sa.String(1000), nullable=True),
        sa.Column('participants', JSON, nullable=True),

        # Counts
        sa.Column('message_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('unread_count', sa.Integer(), nullable=False, server_default='0'),

        # Timestamps
        sa.Column('first_message_at', sa.DateTime(), nullable=True),
        sa.Column('last_message_at', sa.DateTime(), nullable=True),

        # Thread Status
        sa.Column('is_read', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('is_starred', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('is_archived', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('has_attachments', sa.Boolean(), nullable=False, server_default='false'),

        # Labels
        sa.Column('labels', JSON, nullable=True),

        # Primary Key
        sa.PrimaryKeyConstraint('id'),

        # Unique Constraints
        sa.UniqueConstraint('thread_id', name='uq_email_threads_thread_id'),
    )

    # Indexes for email_threads
    op.create_index('ix_email_threads_thread_id', 'email_threads', ['thread_id'])
    op.create_index('ix_email_threads_inbox', 'email_threads', ['inbox'])
    op.create_index('ix_email_threads_subject', 'email_threads', ['subject'])
    op.create_index('ix_email_threads_first_message_at', 'email_threads', ['first_message_at'])
    op.create_index('ix_email_threads_last_message_at', 'email_threads', ['last_message_at'])
    op.create_index('ix_email_threads_is_read', 'email_threads', ['is_read'])
    op.create_index('ix_email_threads_is_starred', 'email_threads', ['is_starred'])
    op.create_index('ix_email_threads_is_archived', 'email_threads', ['is_archived'])

    # Composite indexes for common queries
    op.create_index(
        'idx_inbox_last_message',
        'email_threads',
        ['inbox', 'last_message_at'],
    )
    op.create_index(
        'idx_inbox_read_archived',
        'email_threads',
        ['inbox', 'is_read', 'is_archived'],
    )

    # 2. Create email_messages table
    op.create_table(
        'email_messages',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.Column('is_deleted', sa.Boolean(), nullable=False, server_default='false'),

        # IMAP Identifiers
        sa.Column('message_id', sa.String(500), nullable=False),
        sa.Column('imap_uid', sa.Integer(), nullable=True),
        sa.Column('thread_id', sa.String(500), nullable=True),

        # Inbox/Folder
        sa.Column('inbox', sa.String(100), nullable=False),
        sa.Column('folder', sa.String(200), nullable=False, server_default='INBOX'),

        # Email Headers
        sa.Column('subject', sa.String(1000), nullable=True),
        sa.Column('from_address', sa.String(500), nullable=False),
        sa.Column('from_name', sa.String(500), nullable=True),
        sa.Column('to_addresses', JSON, nullable=True),
        sa.Column('cc_addresses', JSON, nullable=True),
        sa.Column('bcc_addresses', JSON, nullable=True),
        sa.Column('reply_to', sa.String(500), nullable=True),

        # Message Content
        sa.Column('text_body', sa.Text(), nullable=True),
        sa.Column('html_body', sa.Text(), nullable=True),

        # Metadata
        sa.Column('received_at', sa.DateTime(), nullable=False),
        sa.Column('sent_at', sa.DateTime(), nullable=True),

        # Flags and Status
        sa.Column('is_read', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('is_starred', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('is_archived', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('is_spam', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('is_draft', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('is_sent', sa.Boolean(), nullable=False, server_default='false'),

        # Attachments
        sa.Column('has_attachments', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('attachments', JSON, nullable=True),

        # Labels/Tags
        sa.Column('labels', JSON, nullable=True),

        # Raw Data
        sa.Column('raw_headers', JSON, nullable=True),

        # Sync Metadata
        sa.Column('last_synced_at', sa.DateTime(), nullable=True),
        sa.Column('sync_error', sa.Text(), nullable=True),

        # Primary Key
        sa.PrimaryKeyConstraint('id'),

        # Unique Constraints
        sa.UniqueConstraint('message_id', name='uq_email_messages_message_id'),
    )

    # Indexes for email_messages
    op.create_index('ix_email_messages_message_id', 'email_messages', ['message_id'])
    op.create_index('ix_email_messages_imap_uid', 'email_messages', ['imap_uid'])
    op.create_index('ix_email_messages_thread_id', 'email_messages', ['thread_id'])
    op.create_index('ix_email_messages_inbox', 'email_messages', ['inbox'])
    op.create_index('ix_email_messages_subject', 'email_messages', ['subject'])
    op.create_index('ix_email_messages_from_address', 'email_messages', ['from_address'])
    op.create_index('ix_email_messages_received_at', 'email_messages', ['received_at'])
    op.create_index('ix_email_messages_is_read', 'email_messages', ['is_read'])
    op.create_index('ix_email_messages_is_starred', 'email_messages', ['is_starred'])
    op.create_index('ix_email_messages_is_archived', 'email_messages', ['is_archived'])

    # Composite indexes for common queries
    op.create_index(
        'idx_inbox_received',
        'email_messages',
        ['inbox', 'received_at'],
    )
    op.create_index(
        'idx_inbox_read_archived',
        'email_messages',
        ['inbox', 'is_read', 'is_archived'],
    )
    op.create_index(
        'idx_thread_received',
        'email_messages',
        ['thread_id', 'received_at'],
    )
    op.create_index(
        'idx_from_address_received',
        'email_messages',
        ['from_address', 'received_at'],
    )

    # 3. Create email_sync_status table
    op.create_table(
        'email_sync_status',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.Column('is_deleted', sa.Boolean(), nullable=False, server_default='false'),

        # Inbox
        sa.Column('inbox', sa.String(100), nullable=False),

        # Sync Status
        sa.Column('last_sync_at', sa.DateTime(), nullable=True),
        sa.Column('last_sync_uid', sa.Integer(), nullable=True),
        sa.Column('total_messages_synced', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('sync_errors', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('last_error', sa.Text(), nullable=True),
        sa.Column('last_error_at', sa.DateTime(), nullable=True),

        # IMAP Connection Info
        sa.Column('imap_host', sa.String(200), nullable=True),
        sa.Column('imap_folder', sa.String(200), nullable=False, server_default='INBOX'),

        # Status
        sa.Column('is_syncing', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('is_enabled', sa.Boolean(), nullable=False, server_default='true'),

        # Primary Key
        sa.PrimaryKeyConstraint('id'),

        # Unique Constraints
        sa.UniqueConstraint('inbox', name='uq_email_sync_status_inbox'),
    )

    # Indexes for email_sync_status
    op.create_index('ix_email_sync_status_inbox', 'email_sync_status', ['inbox'])

    # 4. Initialize sync status for both inboxes
    op.execute("""
        INSERT INTO email_sync_status (inbox, is_enabled, imap_folder, created_at, updated_at, is_deleted)
        VALUES
            ('customer_support', true, 'INBOX', NOW(), NOW(), false),
            ('payments', true, 'INBOX', NOW(), NOW(), false)
    """)


def downgrade() -> None:
    """
    Drop email storage tables
    """
    op.drop_table('email_messages')
    op.drop_table('email_threads')
    op.drop_table('email_sync_status')
