-- =====================================================
-- Migration: Fix Processed Emails Schema
-- Created: 2026-02-05
-- Purpose: Align staging processed_emails table with production schema.
--          Staging has an older schema missing critical columns.
-- =====================================================

BEGIN;

-- Check if we have the old schema (missing email_provider column)
DO $$
BEGIN
    -- If email_provider column doesn't exist, we need to migrate
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_schema = 'payments'
        AND table_name = 'processed_emails'
        AND column_name = 'email_provider'
    ) THEN
        RAISE NOTICE 'Migrating processed_emails to new schema...';

        -- Rename old table
        ALTER TABLE IF EXISTS payments.processed_emails
        RENAME TO processed_emails_old;

        -- Create new table with correct schema
        CREATE TABLE payments.processed_emails (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            email_provider VARCHAR(50) NOT NULL DEFAULT 'gmail',
            email_account VARCHAR(255) NOT NULL DEFAULT 'myhibachichef@gmail.com',
            email_message_id VARCHAR(500) NOT NULL,
            email_uid VARCHAR(100),
            payment_provider VARCHAR(50) NOT NULL DEFAULT 'unknown',
            amount_cents INTEGER NOT NULL DEFAULT 0,
            currency VARCHAR(10) DEFAULT 'USD',
            sender_name VARCHAR(255),
            sender_identifier VARCHAR(255),
            transaction_id VARCHAR(255),
            email_subject TEXT,
            email_from VARCHAR(500),
            email_date TIMESTAMPTZ,
            email_body_preview TEXT,
            matched_booking_id UUID REFERENCES core.bookings(id) ON DELETE SET NULL,
            matched_customer_id UUID REFERENCES core.customers(id) ON DELETE SET NULL,
            match_confidence VARCHAR(20) DEFAULT 'none',
            match_method VARCHAR(50),
            processing_status VARCHAR(50) NOT NULL DEFAULT 'processed',
            processing_notes TEXT,
            payment_record_created BOOLEAN DEFAULT false,
            payment_record_id UUID,
            notification_sent BOOLEAN DEFAULT false,
            notification_sent_at TIMESTAMPTZ,
            processed_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            processed_by VARCHAR(100) DEFAULT 'payment_email_monitor',
            UNIQUE(email_account, email_message_id)
        );

        -- Migrate data from old table if it exists
        INSERT INTO payments.processed_emails (
            id,
            email_message_id,
            email_subject,
            email_date,
            processing_status,
            processing_notes,
            processed_at,
            email_from
        )
        SELECT
            id,
            COALESCE(message_id, gen_random_uuid()::text),
            email_subject,
            received_date,
            COALESCE(processing_status, 'processed'),
            COALESCE(error_message, extracted_data::text),
            COALESCE(processed_at, created_at, NOW()),
            sender_email
        FROM payments.processed_emails_old
        ON CONFLICT (email_account, email_message_id) DO NOTHING;

        -- Create indexes
        CREATE INDEX IF NOT EXISTS idx_processed_emails_account
            ON payments.processed_emails(email_account);
        CREATE INDEX IF NOT EXISTS idx_processed_emails_provider
            ON payments.processed_emails(payment_provider);
        CREATE INDEX IF NOT EXISTS idx_processed_emails_date
            ON payments.processed_emails(email_date);
        CREATE INDEX IF NOT EXISTS idx_processed_emails_status
            ON payments.processed_emails(processing_status);
        CREATE INDEX IF NOT EXISTS idx_processed_emails_booking
            ON payments.processed_emails(matched_booking_id);
        CREATE INDEX IF NOT EXISTS idx_processed_emails_amount
            ON payments.processed_emails(amount_cents);

        -- Full-text search for sender
        CREATE INDEX IF NOT EXISTS idx_processed_emails_sender_search
            ON payments.processed_emails USING gin(
                to_tsvector('english',
                    COALESCE(sender_name, '') || ' ' || COALESCE(sender_identifier, '')
                )
            );

        -- Drop old table after successful migration
        DROP TABLE IF EXISTS payments.processed_emails_old;

        RAISE NOTICE 'Migration complete!';
    ELSE
        RAISE NOTICE 'Schema already up to date.';
    END IF;
END $$;

COMMIT;
