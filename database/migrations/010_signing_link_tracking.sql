-- =====================================================
-- Migration 010: Signing Link Tracking & Resend System
-- Created: 2025-01-30
-- Purpose: Add columns to track signing link sends/resends
--          and link signed_agreements to slot_holds
-- =====================================================

BEGIN;

-- =====================================================
-- 1. ADD LINK TRACKING COLUMNS TO slot_holds
-- =====================================================

-- Track when signing link was first sent
ALTER TABLE core.slot_holds
ADD COLUMN IF NOT EXISTS signing_link_sent_at TIMESTAMPTZ;

COMMENT ON COLUMN core.slot_holds.signing_link_sent_at IS
    'When the signing link was first sent to customer (SMS or email)';

-- Track when signing link was last resent (for multiple resends)
ALTER TABLE core.slot_holds
ADD COLUMN IF NOT EXISTS signing_link_resent_at TIMESTAMPTZ;

COMMENT ON COLUMN core.slot_holds.signing_link_resent_at IS
    'When the signing link was last resent (null if never resent)';

-- Count how many times link was sent (1 = initial, 2+ = resends)
ALTER TABLE core.slot_holds
ADD COLUMN IF NOT EXISTS signing_link_send_count INT NOT NULL DEFAULT 0;

COMMENT ON COLUMN core.slot_holds.signing_link_send_count IS
    'Total times signing link was sent (1=initial, 2+=resends). Rate limit at 5.';

-- Track what channels the link was sent via
ALTER TABLE core.slot_holds
ADD COLUMN IF NOT EXISTS signing_link_channels TEXT[] DEFAULT '{}';

COMMENT ON COLUMN core.slot_holds.signing_link_channels IS
    'Channels used to send link: sms, email. Array tracks all channels used.';

-- =====================================================
-- 2. ADD slot_hold_id REFERENCE TO signed_agreements
-- =====================================================

-- Link signed_agreements back to the slot_hold that initiated it
ALTER TABLE core.signed_agreements
ADD COLUMN IF NOT EXISTS slot_hold_id UUID;

-- Foreign key to slot_holds
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.table_constraints
        WHERE constraint_name = 'fk_signed_agreements_slot_hold'
    ) THEN
        ALTER TABLE core.signed_agreements
        ADD CONSTRAINT fk_signed_agreements_slot_hold
        FOREIGN KEY (slot_hold_id) REFERENCES core.slot_holds(id)
        ON DELETE SET NULL;
    END IF;
END $$;

COMMENT ON COLUMN core.signed_agreements.slot_hold_id IS
    'The slot hold that was active when this agreement was signed (before deposit)';

-- =====================================================
-- 3. ADD INDEX FOR slot_hold_id LOOKUPS
-- =====================================================

CREATE INDEX IF NOT EXISTS idx_signed_agreements_slot_hold
    ON core.signed_agreements(slot_hold_id)
    WHERE slot_hold_id IS NOT NULL;

-- =====================================================
-- 4. ADD COMPOSITE UNIQUE CONSTRAINT
-- =====================================================
-- Prevent duplicate agreements for same slot_hold + agreement_type
-- Customer can only sign each agreement type ONCE per hold

-- First check if constraint exists to avoid error
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.table_constraints
        WHERE constraint_name = 'uq_signed_agreements_slot_hold_type'
    ) THEN
        ALTER TABLE core.signed_agreements
        ADD CONSTRAINT uq_signed_agreements_slot_hold_type
        UNIQUE (slot_hold_id, agreement_type);
    END IF;
EXCEPTION
    WHEN unique_violation THEN
        RAISE NOTICE 'Duplicate agreements exist - constraint not added. Clean up data first.';
END $$;

-- =====================================================
-- 5. ADD INDEX FOR LINK SEND TRACKING QUERIES
-- =====================================================

-- Index for finding holds by send count (rate limiting)
CREATE INDEX IF NOT EXISTS idx_slot_holds_link_send_count
    ON core.slot_holds(signing_link_send_count)
    WHERE status = 'pending';

-- Index for finding recently sent links
CREATE INDEX IF NOT EXISTS idx_slot_holds_link_sent_at
    ON core.slot_holds(signing_link_sent_at)
    WHERE status = 'pending';

-- =====================================================
-- 6. CREATE FUNCTION TO TRACK LINK SENDS
-- =====================================================

CREATE OR REPLACE FUNCTION core.record_signing_link_sent(
    p_hold_id UUID,
    p_channel VARCHAR(20)  -- 'sms' or 'email'
)
RETURNS TABLE(
    send_count INT,
    first_sent_at TIMESTAMPTZ,
    last_sent_at TIMESTAMPTZ
) AS $$
DECLARE
    v_current_count INT;
    v_first_sent TIMESTAMPTZ;
    v_now TIMESTAMPTZ := NOW();
BEGIN
    -- Get current state
    SELECT signing_link_send_count, signing_link_sent_at
    INTO v_current_count, v_first_sent
    FROM core.slot_holds
    WHERE id = p_hold_id;

    IF NOT FOUND THEN
        RAISE EXCEPTION 'Slot hold not found: %', p_hold_id;
    END IF;

    -- Check rate limit (max 5 sends)
    IF v_current_count >= 5 THEN
        RAISE EXCEPTION 'Rate limit exceeded: Maximum 5 signing link sends per hold';
    END IF;

    -- Update the record
    UPDATE core.slot_holds
    SET
        signing_link_send_count = signing_link_send_count + 1,
        signing_link_sent_at = COALESCE(signing_link_sent_at, v_now),
        signing_link_resent_at = CASE
            WHEN signing_link_sent_at IS NOT NULL THEN v_now
            ELSE NULL
        END,
        signing_link_channels = ARRAY(
            SELECT DISTINCT unnest(
                array_cat(COALESCE(signing_link_channels, '{}'), ARRAY[p_channel])
            )
        )
    WHERE id = p_hold_id
    RETURNING
        signing_link_send_count,
        signing_link_sent_at,
        signing_link_resent_at
    INTO send_count, first_sent_at, last_sent_at;

    RETURN NEXT;
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION core.record_signing_link_sent IS
    'Record that a signing link was sent. Tracks count, timestamps, and channels. Rate limited to 5.';

-- =====================================================
-- 7. CREATE VIEW FOR HOLD STATUS WITH LINK INFO
-- =====================================================

CREATE OR REPLACE VIEW core.slot_holds_with_link_status AS
SELECT
    sh.id,
    sh.signing_token,
    sh.customer_email,
    sh.customer_name,
    sh.status,
    sh.created_at,
    sh.expires_at,
    sh.signing_deadline_at,
    sh.agreement_signed_at,
    sh.payment_deadline_at,
    -- Link tracking
    sh.signing_link_sent_at,
    sh.signing_link_resent_at,
    sh.signing_link_send_count,
    sh.signing_link_channels,
    -- Computed fields
    CASE
        WHEN sh.signing_link_sent_at IS NULL THEN 'not_sent'
        WHEN sh.signing_link_send_count = 1 THEN 'sent_once'
        WHEN sh.signing_link_send_count > 1 THEN 'resent'
    END AS link_status,
    CASE
        WHEN sh.signing_link_send_count >= 5 THEN true
        ELSE false
    END AS link_rate_limited,
    -- Time since last send
    EXTRACT(EPOCH FROM (NOW() - COALESCE(sh.signing_link_resent_at, sh.signing_link_sent_at))) AS seconds_since_last_send
FROM core.slot_holds sh;

COMMENT ON VIEW core.slot_holds_with_link_status IS
    'Slot holds with signing link tracking info for admin dashboards';

COMMIT;

-- =====================================================
-- ROLLBACK SCRIPT (keep as comment for emergency)
-- =====================================================
-- DROP VIEW IF EXISTS core.slot_holds_with_link_status;
-- DROP FUNCTION IF EXISTS core.record_signing_link_sent;
-- DROP INDEX IF EXISTS core.idx_slot_holds_link_sent_at;
-- DROP INDEX IF EXISTS core.idx_slot_holds_link_send_count;
-- DROP INDEX IF EXISTS core.idx_signed_agreements_slot_hold;
-- ALTER TABLE core.signed_agreements DROP CONSTRAINT IF EXISTS uq_signed_agreements_slot_hold_type;
-- ALTER TABLE core.signed_agreements DROP CONSTRAINT IF EXISTS fk_signed_agreements_slot_hold;
-- ALTER TABLE core.signed_agreements DROP COLUMN IF EXISTS slot_hold_id;
-- ALTER TABLE core.slot_holds DROP COLUMN IF EXISTS signing_link_channels;
-- ALTER TABLE core.slot_holds DROP COLUMN IF EXISTS signing_link_send_count;
-- ALTER TABLE core.slot_holds DROP COLUMN IF EXISTS signing_link_resent_at;
-- ALTER TABLE core.slot_holds DROP COLUMN IF EXISTS signing_link_sent_at;
