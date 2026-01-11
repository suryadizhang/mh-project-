-- =====================================================
-- Migration: Processed Payment Emails Tracking
-- Created: 2026-01-10
-- Purpose: Track processed payment notification emails to prevent
--          duplicate processing and enable audit trail.
--          Works regardless of email read/unread status in Gmail.
-- =====================================================

BEGIN;

-- Create schema if not exists
CREATE SCHEMA IF NOT EXISTS payments;

-- Table to track all processed payment emails
CREATE TABLE IF NOT EXISTS payments.processed_emails (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Email identification (unique per provider)
    email_provider VARCHAR(50) NOT NULL,  -- 'gmail', 'outlook', etc.
    email_account VARCHAR(255) NOT NULL,  -- 'myhibachichef@gmail.com'
    email_message_id VARCHAR(500) NOT NULL,  -- IMAP message ID or Message-ID header
    email_uid VARCHAR(100),  -- IMAP UID (more stable than sequence number)

    -- Payment provider detection
    payment_provider VARCHAR(50) NOT NULL,  -- 'venmo', 'zelle', 'stripe', 'paypal', 'bank_of_america'

    -- Parsed payment details
    amount_cents INTEGER NOT NULL,  -- Amount in cents to avoid floating point issues
    currency VARCHAR(10) DEFAULT 'USD',
    sender_name VARCHAR(255),  -- Who sent the payment
    sender_identifier VARCHAR(255),  -- Email, phone, or username
    transaction_id VARCHAR(255),  -- Provider's transaction ID if available

    -- Email metadata
    email_subject TEXT,
    email_from VARCHAR(500),
    email_date TIMESTAMPTZ,  -- When the email was sent
    email_body_preview TEXT,  -- First 500 chars for debugging

    -- Matching results
    matched_booking_id UUID REFERENCES core.bookings(id) ON DELETE SET NULL,
    matched_customer_id UUID REFERENCES core.customers(id) ON DELETE SET NULL,
    match_confidence VARCHAR(20) DEFAULT 'none',  -- 'exact', 'high', 'medium', 'low', 'none'
    match_method VARCHAR(50),  -- 'phone_exact', 'email_exact', 'amount_match', 'manual'

    -- Processing status
    processing_status VARCHAR(50) NOT NULL DEFAULT 'processed',
    -- 'processed' - Successfully parsed
    -- 'matched' - Matched to a booking
    -- 'applied' - Payment applied to booking
    -- 'failed' - Processing failed
    -- 'duplicate' - Duplicate payment detected
    -- 'manual_review' - Needs human review

    processing_notes TEXT,  -- Error messages or notes

    -- Actions taken
    payment_record_created BOOLEAN DEFAULT false,
    payment_record_id UUID,  -- Reference to payments table if created
    notification_sent BOOLEAN DEFAULT false,
    notification_sent_at TIMESTAMPTZ,

    -- Audit trail
    processed_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    processed_by VARCHAR(100) DEFAULT 'payment_email_monitor',  -- System or user

    -- Prevent duplicate processing
    UNIQUE(email_account, email_message_id)
);

-- Indexes for common queries
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

-- Full-text search on sender info
CREATE INDEX IF NOT EXISTS idx_processed_emails_sender_search
    ON payments.processed_emails USING gin(to_tsvector('english', coalesce(sender_name, '') || ' ' || coalesce(sender_identifier, '')));

COMMENT ON TABLE payments.processed_emails IS 'Tracks all payment notification emails processed by PaymentEmailMonitor. Prevents duplicate processing and provides audit trail for financial reconciliation.';

-- View for unmatched payments (need manual review)
CREATE OR REPLACE VIEW payments.unmatched_payment_emails AS
SELECT
    pe.id,
    pe.payment_provider,
    pe.amount_cents / 100.0 AS amount_dollars,
    pe.sender_name,
    pe.sender_identifier,
    pe.email_subject,
    pe.email_date,
    pe.processing_status,
    pe.processing_notes
FROM payments.processed_emails pe
WHERE pe.matched_booking_id IS NULL
AND pe.processing_status NOT IN ('duplicate', 'failed')
ORDER BY pe.email_date DESC;

COMMENT ON VIEW payments.unmatched_payment_emails IS 'Payment emails that could not be automatically matched to a booking. Requires manual review.';

-- View for recent payment activity
CREATE OR REPLACE VIEW payments.recent_payment_emails AS
SELECT
    pe.id,
    pe.payment_provider,
    pe.amount_cents / 100.0 AS amount_dollars,
    pe.sender_name,
    pe.email_date,
    pe.processing_status,
    pe.match_confidence,
    b.id AS booking_id,
    c.first_name || ' ' || c.last_name AS customer_name
FROM payments.processed_emails pe
LEFT JOIN core.bookings b ON pe.matched_booking_id = b.id
LEFT JOIN core.customers c ON pe.matched_customer_id = c.id
WHERE pe.email_date > NOW() - INTERVAL '30 days'
ORDER BY pe.email_date DESC;

COMMENT ON VIEW payments.recent_payment_emails IS 'Last 30 days of processed payment emails with booking/customer info.';

COMMIT;

-- =====================================================
-- ROLLBACK SCRIPT (keep as comment for emergency):
-- =====================================================
-- DROP VIEW IF EXISTS payments.recent_payment_emails;
-- DROP VIEW IF EXISTS payments.unmatched_payment_emails;
-- DROP TABLE IF EXISTS payments.processed_emails;
-- DROP SCHEMA IF EXISTS payments;
