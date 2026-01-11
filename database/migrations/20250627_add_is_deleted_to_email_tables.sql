-- =====================================================
-- Migration: Add is_deleted columns to email tables
-- Created: 2025-06-27
-- Purpose: Support soft-delete for email messages and threads
-- =====================================================

BEGIN;

-- Add is_deleted to ai.email_messages if not exists
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_schema = 'ai'
        AND table_name = 'email_messages'
        AND column_name = 'is_deleted'
    ) THEN
        ALTER TABLE ai.email_messages ADD COLUMN is_deleted BOOLEAN DEFAULT false;
        RAISE NOTICE 'Added is_deleted column to ai.email_messages';
    ELSE
        RAISE NOTICE 'is_deleted column already exists in ai.email_messages';
    END IF;
END $$;

-- Add is_deleted to ai.email_threads if not exists
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_schema = 'ai'
        AND table_name = 'email_threads'
        AND column_name = 'is_deleted'
    ) THEN
        ALTER TABLE ai.email_threads ADD COLUMN is_deleted BOOLEAN DEFAULT false;
        RAISE NOTICE 'Added is_deleted column to ai.email_threads';
    ELSE
        RAISE NOTICE 'is_deleted column already exists in ai.email_threads';
    END IF;
END $$;

-- Create ai.email_labels table if not exists
CREATE TABLE IF NOT EXISTS ai.email_labels (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(100) NOT NULL,
    color VARCHAR(20),
    email_account_id UUID REFERENCES ai.email_accounts(id) ON DELETE CASCADE,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(name, email_account_id)
);

-- Add comments
COMMENT ON COLUMN ai.email_messages.is_deleted IS 'Soft delete flag for email messages';
COMMENT ON COLUMN ai.email_threads.is_deleted IS 'Soft delete flag for email threads';
COMMENT ON TABLE ai.email_labels IS 'Email labels for organizing emails';

-- Create index on is_deleted for faster queries
CREATE INDEX IF NOT EXISTS idx_email_messages_is_deleted ON ai.email_messages(is_deleted);
CREATE INDEX IF NOT EXISTS idx_email_threads_is_deleted ON ai.email_threads(is_deleted);

COMMIT;

-- =====================================================
-- ROLLBACK SCRIPT (keep as comment for emergency):
-- =====================================================
-- ALTER TABLE ai.email_messages DROP COLUMN IF EXISTS is_deleted;
-- ALTER TABLE ai.email_threads DROP COLUMN IF EXISTS is_deleted;
-- DROP TABLE IF EXISTS ai.email_labels;
