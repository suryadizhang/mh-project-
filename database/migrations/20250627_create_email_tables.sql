-- =====================================================
-- Migration: Create Email Storage Tables
-- Created: 2025-06-27
-- Purpose: Create email_messages, email_threads, email_sync_status,
--          and email_labels tables for IMAP email storage
-- =====================================================

BEGIN;

-- Create email_messages table
CREATE TABLE IF NOT EXISTS public.email_messages (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- IMAP Identifiers
    message_id VARCHAR(500) NOT NULL UNIQUE,
    imap_uid INTEGER,
    thread_id VARCHAR(500),

    -- Inbox/Folder
    inbox VARCHAR(100) NOT NULL,
    folder VARCHAR(200) DEFAULT 'INBOX',

    -- Email Headers
    subject VARCHAR(1000),
    from_address VARCHAR(500) NOT NULL,
    from_name VARCHAR(500),
    to_addresses JSONB DEFAULT '[]'::jsonb,
    cc_addresses JSONB DEFAULT '[]'::jsonb,
    bcc_addresses JSONB DEFAULT '[]'::jsonb,
    reply_to VARCHAR(500),

    -- Message Content
    text_body TEXT,
    html_body TEXT,

    -- Metadata
    received_at TIMESTAMPTZ NOT NULL,
    sent_at TIMESTAMPTZ,

    -- Flags and Status
    is_read BOOLEAN DEFAULT FALSE,
    is_starred BOOLEAN DEFAULT FALSE,
    is_archived BOOLEAN DEFAULT FALSE,
    is_spam BOOLEAN DEFAULT FALSE,
    is_draft BOOLEAN DEFAULT FALSE,
    is_sent BOOLEAN DEFAULT FALSE,
    is_deleted BOOLEAN DEFAULT FALSE,

    -- Attachments
    has_attachments BOOLEAN DEFAULT FALSE,
    attachments JSONB DEFAULT '[]'::jsonb,

    -- Labels/Tags
    labels JSONB DEFAULT '[]'::jsonb,

    -- Raw Data
    raw_headers JSONB DEFAULT '{}'::jsonb,

    -- Sync Metadata
    last_synced_at TIMESTAMPTZ,
    sync_error TEXT,

    -- Timestamps
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Create indexes for email_messages
CREATE INDEX IF NOT EXISTS idx_email_messages_message_id ON public.email_messages(message_id);
CREATE INDEX IF NOT EXISTS idx_email_messages_imap_uid ON public.email_messages(imap_uid);
CREATE INDEX IF NOT EXISTS idx_email_messages_thread_id ON public.email_messages(thread_id);
CREATE INDEX IF NOT EXISTS idx_email_messages_inbox ON public.email_messages(inbox);
CREATE INDEX IF NOT EXISTS idx_email_messages_subject ON public.email_messages(subject);
CREATE INDEX IF NOT EXISTS idx_email_messages_from_address ON public.email_messages(from_address);
CREATE INDEX IF NOT EXISTS idx_email_messages_received_at ON public.email_messages(received_at);
CREATE INDEX IF NOT EXISTS idx_email_messages_is_read ON public.email_messages(is_read);
CREATE INDEX IF NOT EXISTS idx_email_messages_is_starred ON public.email_messages(is_starred);
CREATE INDEX IF NOT EXISTS idx_email_messages_is_archived ON public.email_messages(is_archived);
CREATE INDEX IF NOT EXISTS idx_email_messages_is_deleted ON public.email_messages(is_deleted);
CREATE INDEX IF NOT EXISTS idx_email_messages_inbox_received ON public.email_messages(inbox, received_at);
CREATE INDEX IF NOT EXISTS idx_email_messages_inbox_read_archived ON public.email_messages(inbox, is_read, is_archived);
CREATE INDEX IF NOT EXISTS idx_email_messages_thread_received ON public.email_messages(thread_id, received_at);
CREATE INDEX IF NOT EXISTS idx_email_messages_from_received ON public.email_messages(from_address, received_at);

-- Create email_threads table
CREATE TABLE IF NOT EXISTS public.email_threads (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Thread Identifier
    thread_id VARCHAR(500) NOT NULL UNIQUE,

    -- Inbox
    inbox VARCHAR(100) NOT NULL,

    -- Thread Metadata
    subject VARCHAR(1000),
    participants JSONB DEFAULT '[]'::jsonb,

    -- Counts
    message_count INTEGER DEFAULT 0,
    unread_count INTEGER DEFAULT 0,

    -- Timestamps
    first_message_at TIMESTAMPTZ,
    last_message_at TIMESTAMPTZ,

    -- Thread Status
    is_read BOOLEAN DEFAULT FALSE,
    is_starred BOOLEAN DEFAULT FALSE,
    is_archived BOOLEAN DEFAULT FALSE,
    is_deleted BOOLEAN DEFAULT FALSE,
    has_attachments BOOLEAN DEFAULT FALSE,

    -- Labels
    labels JSONB DEFAULT '[]'::jsonb,

    -- Timestamps
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Create indexes for email_threads
CREATE INDEX IF NOT EXISTS idx_email_threads_thread_id ON public.email_threads(thread_id);
CREATE INDEX IF NOT EXISTS idx_email_threads_inbox ON public.email_threads(inbox);
CREATE INDEX IF NOT EXISTS idx_email_threads_subject ON public.email_threads(subject);
CREATE INDEX IF NOT EXISTS idx_email_threads_first_message ON public.email_threads(first_message_at);
CREATE INDEX IF NOT EXISTS idx_email_threads_last_message ON public.email_threads(last_message_at);
CREATE INDEX IF NOT EXISTS idx_email_threads_is_read ON public.email_threads(is_read);
CREATE INDEX IF NOT EXISTS idx_email_threads_is_starred ON public.email_threads(is_starred);
CREATE INDEX IF NOT EXISTS idx_email_threads_is_archived ON public.email_threads(is_archived);
CREATE INDEX IF NOT EXISTS idx_email_threads_is_deleted ON public.email_threads(is_deleted);
CREATE INDEX IF NOT EXISTS idx_email_threads_inbox_last_message ON public.email_threads(inbox, last_message_at);
CREATE INDEX IF NOT EXISTS idx_email_threads_inbox_read_archived ON public.email_threads(inbox, is_read, is_archived);

-- Create email_sync_status table
CREATE TABLE IF NOT EXISTS public.email_sync_status (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Inbox
    inbox VARCHAR(100) NOT NULL UNIQUE,

    -- Sync Status
    last_sync_at TIMESTAMPTZ,
    last_sync_uid INTEGER,
    total_messages_synced INTEGER DEFAULT 0,
    sync_errors INTEGER DEFAULT 0,
    last_error TEXT,
    last_error_at TIMESTAMPTZ,

    -- IMAP Connection Info
    imap_host VARCHAR(200),
    imap_folder VARCHAR(200) DEFAULT 'INBOX',

    -- Status
    is_syncing BOOLEAN DEFAULT FALSE,
    is_enabled BOOLEAN DEFAULT TRUE,

    -- Timestamps
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Create indexes for email_sync_status
CREATE INDEX IF NOT EXISTS idx_email_sync_status_inbox ON public.email_sync_status(inbox);

-- Create email_labels table
CREATE TABLE IF NOT EXISTS public.email_labels (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Label Info
    name VARCHAR(100) NOT NULL,
    color VARCHAR(50) DEFAULT '#3B82F6',
    description TEXT,

    -- Which inbox this label belongs to
    inbox VARCHAR(100),

    -- System or user-created
    is_system BOOLEAN DEFAULT FALSE,

    -- Order for display
    display_order INTEGER DEFAULT 0,

    -- Timestamps
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),

    -- Unique constraint: label name per inbox
    UNIQUE(name, inbox)
);

-- Create indexes for email_labels
CREATE INDEX IF NOT EXISTS idx_email_labels_name ON public.email_labels(name);
CREATE INDEX IF NOT EXISTS idx_email_labels_inbox ON public.email_labels(inbox);
CREATE INDEX IF NOT EXISTS idx_email_labels_display_order ON public.email_labels(display_order);

-- Insert default labels
INSERT INTO public.email_labels (name, color, is_system, display_order)
VALUES
    ('inbox', '#3B82F6', TRUE, 1),
    ('important', '#EF4444', TRUE, 2),
    ('starred', '#F59E0B', TRUE, 3),
    ('sent', '#10B981', TRUE, 4),
    ('draft', '#6B7280', TRUE, 5),
    ('spam', '#DC2626', TRUE, 6),
    ('trash', '#374151', TRUE, 7)
ON CONFLICT (name, inbox) DO NOTHING;

-- Add comments for documentation
COMMENT ON TABLE public.email_messages IS 'Individual email messages synced from IMAP servers';
COMMENT ON TABLE public.email_threads IS 'Email conversation threads grouping related messages';
COMMENT ON TABLE public.email_sync_status IS 'IMAP sync tracking for each inbox';
COMMENT ON TABLE public.email_labels IS 'Labels/tags for organizing emails';

COMMIT;

-- Verify tables were created
SELECT 'email_messages' as table_name, COUNT(*) as row_count FROM public.email_messages
UNION ALL
SELECT 'email_threads', COUNT(*) FROM public.email_threads
UNION ALL
SELECT 'email_sync_status', COUNT(*) FROM public.email_sync_status
UNION ALL
SELECT 'email_labels', COUNT(*) FROM public.email_labels;
