-- =====================================================
-- Migration 009: Slot Holds Auto-Cancel System
-- Created: 2025-01-30
-- Purpose: Add columns for two-phase hold expiration tracking
--          Phase 1: 2 hours to sign agreement
--          Phase 2: 4 hours to pay deposit (after signing)
--          1-hour warning before each deadline
-- =====================================================

-- =====================================================
-- 1. ADD AGREEMENT SIGNING TRACKING
-- =====================================================

-- When the agreement was signed (starts Phase 2 countdown)
ALTER TABLE core.slot_holds
ADD COLUMN IF NOT EXISTS agreement_signed_at TIMESTAMPTZ;

COMMENT ON COLUMN core.slot_holds.agreement_signed_at IS
    'Timestamp when customer signed the agreement. Triggers 4-hour deposit deadline.';

-- Track signed agreement reference
ALTER TABLE core.slot_holds
ADD COLUMN IF NOT EXISTS signed_agreement_id UUID;

-- Foreign key to signed_agreements (deferred to allow flexibility)
-- Note: Can't add FK if signed_agreements doesn't exist yet
DO $$
BEGIN
    IF EXISTS (
        SELECT 1 FROM information_schema.tables
        WHERE table_schema = 'core' AND table_name = 'signed_agreements'
    ) THEN
        -- Add FK only if it doesn't exist
        IF NOT EXISTS (
            SELECT 1 FROM information_schema.table_constraints
            WHERE constraint_name = 'fk_slot_holds_signed_agreement'
        ) THEN
            ALTER TABLE core.slot_holds
            ADD CONSTRAINT fk_slot_holds_signed_agreement
            FOREIGN KEY (signed_agreement_id) REFERENCES core.signed_agreements(id);
        END IF;
    END IF;
END $$;

COMMENT ON COLUMN core.slot_holds.signed_agreement_id IS
    'Reference to the signed agreement record';

-- =====================================================
-- 2. ADD DEPOSIT PAYMENT TRACKING
-- =====================================================

-- When the deposit was paid (completes the hold → booking conversion)
ALTER TABLE core.slot_holds
ADD COLUMN IF NOT EXISTS deposit_paid_at TIMESTAMPTZ;

COMMENT ON COLUMN core.slot_holds.deposit_paid_at IS
    'Timestamp when deposit was paid. Hold is then converted to booking.';

-- Track payment reference (Stripe, Venmo, Zelle)
ALTER TABLE core.slot_holds
ADD COLUMN IF NOT EXISTS deposit_payment_method VARCHAR(20);

COMMENT ON COLUMN core.slot_holds.deposit_payment_method IS
    'How deposit was paid: stripe, venmo, zelle';

ALTER TABLE core.slot_holds
ADD COLUMN IF NOT EXISTS deposit_payment_reference VARCHAR(255);

COMMENT ON COLUMN core.slot_holds.deposit_payment_reference IS
    'Payment reference ID (Stripe payment_intent, Venmo/Zelle confirmation)';

-- =====================================================
-- 3. ADD WARNING NOTIFICATION TRACKING
-- =====================================================

-- Prevent duplicate warning notifications
ALTER TABLE core.slot_holds
ADD COLUMN IF NOT EXISTS signing_warning_sent_at TIMESTAMPTZ;

COMMENT ON COLUMN core.slot_holds.signing_warning_sent_at IS
    '1-hour warning sent before 2-hour signing deadline';

ALTER TABLE core.slot_holds
ADD COLUMN IF NOT EXISTS payment_warning_sent_at TIMESTAMPTZ;

COMMENT ON COLUMN core.slot_holds.payment_warning_sent_at IS
    '1-hour warning sent before 4-hour payment deadline (after signing)';

-- =====================================================
-- 4. ADD DEADLINE TRACKING COLUMNS
-- =====================================================

-- Signing deadline (calculated: created_at + 2 hours)
ALTER TABLE core.slot_holds
ADD COLUMN IF NOT EXISTS signing_deadline_at TIMESTAMPTZ;

COMMENT ON COLUMN core.slot_holds.signing_deadline_at IS
    'Deadline to sign agreement (created_at + 2 hours). Auto-cancel if missed.';

-- Payment deadline (calculated: agreement_signed_at + 4 hours)
ALTER TABLE core.slot_holds
ADD COLUMN IF NOT EXISTS payment_deadline_at TIMESTAMPTZ;

COMMENT ON COLUMN core.slot_holds.payment_deadline_at IS
    'Deadline to pay deposit (agreement_signed_at + 4 hours). Auto-cancel if missed.';

-- =====================================================
-- 5. UPDATE STATUS ENUM VALUES
-- =====================================================
-- Current statuses: pending, converted, expired, cancelled
-- Add new statuses for better tracking

-- Create a type-safe way to track auto-cancel reasons
ALTER TABLE core.slot_holds
ADD COLUMN IF NOT EXISTS cancellation_reason VARCHAR(50);

COMMENT ON COLUMN core.slot_holds.cancellation_reason IS
    'Why the hold was cancelled: signing_timeout, payment_timeout, user_cancelled, admin_cancelled';

-- =====================================================
-- 6. BACKFILL SIGNING DEADLINE FOR EXISTING RECORDS
-- =====================================================

-- Set signing_deadline_at for existing pending holds
UPDATE core.slot_holds
SET signing_deadline_at = created_at + INTERVAL '2 hours'
WHERE signing_deadline_at IS NULL
  AND status = 'pending';

-- =====================================================
-- 7. ADD INDEXES FOR CELERY BEAT QUERIES
-- =====================================================

-- Index for finding holds approaching signing deadline
CREATE INDEX IF NOT EXISTS idx_slot_holds_signing_deadline
    ON core.slot_holds(signing_deadline_at)
    WHERE status = 'pending' AND agreement_signed_at IS NULL;

-- Index for finding holds approaching payment deadline
CREATE INDEX IF NOT EXISTS idx_slot_holds_payment_deadline
    ON core.slot_holds(payment_deadline_at)
    WHERE status = 'pending' AND agreement_signed_at IS NOT NULL AND deposit_paid_at IS NULL;

-- Index for warning queries (1 hour before deadline)
CREATE INDEX IF NOT EXISTS idx_slot_holds_signing_warning
    ON core.slot_holds(signing_deadline_at, signing_warning_sent_at)
    WHERE status = 'pending' AND agreement_signed_at IS NULL;

CREATE INDEX IF NOT EXISTS idx_slot_holds_payment_warning
    ON core.slot_holds(payment_deadline_at, payment_warning_sent_at)
    WHERE status = 'pending' AND agreement_signed_at IS NOT NULL AND deposit_paid_at IS NULL;

-- =====================================================
-- 8. CREATE TRIGGER TO AUTO-SET DEADLINES
-- =====================================================

-- Function to set signing_deadline_at on insert
CREATE OR REPLACE FUNCTION core.set_slot_hold_signing_deadline()
RETURNS TRIGGER AS $$
BEGIN
    -- Set 2-hour signing deadline on creation
    IF NEW.signing_deadline_at IS NULL THEN
        NEW.signing_deadline_at := NEW.created_at + INTERVAL '2 hours';
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Trigger on insert
DROP TRIGGER IF EXISTS trg_slot_holds_set_signing_deadline ON core.slot_holds;
CREATE TRIGGER trg_slot_holds_set_signing_deadline
    BEFORE INSERT ON core.slot_holds
    FOR EACH ROW
    EXECUTE FUNCTION core.set_slot_hold_signing_deadline();

-- Function to set payment_deadline_at when agreement is signed
CREATE OR REPLACE FUNCTION core.set_slot_hold_payment_deadline()
RETURNS TRIGGER AS $$
BEGIN
    -- When agreement_signed_at is set, calculate 4-hour payment deadline
    IF OLD.agreement_signed_at IS NULL AND NEW.agreement_signed_at IS NOT NULL THEN
        NEW.payment_deadline_at := NEW.agreement_signed_at + INTERVAL '4 hours';
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Trigger on update
DROP TRIGGER IF EXISTS trg_slot_holds_set_payment_deadline ON core.slot_holds;
CREATE TRIGGER trg_slot_holds_set_payment_deadline
    BEFORE UPDATE ON core.slot_holds
    FOR EACH ROW
    EXECUTE FUNCTION core.set_slot_hold_payment_deadline();

-- =====================================================
-- SUMMARY:
-- New columns added to core.slot_holds:
--   - agreement_signed_at: When customer signed
--   - signed_agreement_id: FK to signed_agreements
--   - deposit_paid_at: When deposit was paid
--   - deposit_payment_method: stripe/venmo/zelle
--   - deposit_payment_reference: Payment ID
--   - signing_warning_sent_at: Track 1-hour warning
--   - payment_warning_sent_at: Track 1-hour warning
--   - signing_deadline_at: 2 hours from creation
--   - payment_deadline_at: 4 hours from signing
--   - cancellation_reason: Why hold was cancelled
-- =====================================================
