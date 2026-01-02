-- =====================================================
-- Migration: Cancellation Workflow (2-Step Approval)
-- Created: 2025-01-30
-- Purpose: Add cancellation workflow fields to bookings table
--          Supporting Option A: 2-step self-approval with slot held until approved
-- =====================================================
--
-- WORKFLOW:
-- 1. Request cancellation -> Status: CANCELLATION_REQUESTED (slot HELD)
-- 2a. Approve -> Status: CANCELLED (slot RELEASED)
-- 2b. Reject -> Status: reverts to previous (slot still HELD)
--
-- WHY: Hibachi slots are limited. Once released, another customer can
-- immediately book it. This workflow allows review before releasing.
-- =====================================================

BEGIN;

-- =====================================================
-- STEP 1: Add CANCELLATION_REQUESTED to booking_status enum
-- =====================================================

-- Check if the enum value already exists before adding
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_enum
        WHERE enumlabel = 'cancellation_requested'
        AND enumtypid = 'booking_status'::regtype
    ) THEN
        ALTER TYPE booking_status ADD VALUE 'cancellation_requested';
        RAISE NOTICE 'Added cancellation_requested to booking_status enum';
    ELSE
        RAISE NOTICE 'cancellation_requested already exists in booking_status enum';
    END IF;
EXCEPTION
    WHEN undefined_object THEN
        -- If booking_status enum doesn't exist, create it with all values
        CREATE TYPE booking_status AS ENUM (
            'pending',
            'confirmed',
            'deposit_paid',
            'in_progress',
            'completed',
            'cancelled',
            'no_show',
            'rescheduled',
            'cancellation_requested'
        );
        RAISE NOTICE 'Created booking_status enum with cancellation_requested';
END $$;

-- =====================================================
-- STEP 2: Add cancellation tracking fields
-- =====================================================

-- Previous status (for revert on rejection)
ALTER TABLE core.bookings
    ADD COLUMN IF NOT EXISTS previous_status VARCHAR(50);
COMMENT ON COLUMN core.bookings.previous_status IS 'Status before cancellation request - used for revert on rejection';

-- Cancellation request fields
ALTER TABLE core.bookings
    ADD COLUMN IF NOT EXISTS cancellation_requested_at TIMESTAMPTZ;
COMMENT ON COLUMN core.bookings.cancellation_requested_at IS 'When cancellation was requested';

ALTER TABLE core.bookings
    ADD COLUMN IF NOT EXISTS cancellation_requested_by VARCHAR(200);
COMMENT ON COLUMN core.bookings.cancellation_requested_by IS 'Who requested the cancellation (name or email)';

ALTER TABLE core.bookings
    ADD COLUMN IF NOT EXISTS cancellation_reason TEXT;
COMMENT ON COLUMN core.bookings.cancellation_reason IS 'Reason provided when requesting cancellation';

-- Cancellation approval fields
ALTER TABLE core.bookings
    ADD COLUMN IF NOT EXISTS cancelled_at TIMESTAMPTZ;
COMMENT ON COLUMN core.bookings.cancelled_at IS 'When cancellation was approved/finalized';

ALTER TABLE core.bookings
    ADD COLUMN IF NOT EXISTS cancelled_by VARCHAR(200);
COMMENT ON COLUMN core.bookings.cancelled_by IS 'Who approved the cancellation (name or email)';

ALTER TABLE core.bookings
    ADD COLUMN IF NOT EXISTS cancellation_approved_reason TEXT;
COMMENT ON COLUMN core.bookings.cancellation_approved_reason IS 'Reason provided when approving cancellation';

-- Cancellation rejection fields
ALTER TABLE core.bookings
    ADD COLUMN IF NOT EXISTS cancellation_rejected_at TIMESTAMPTZ;
COMMENT ON COLUMN core.bookings.cancellation_rejected_at IS 'When cancellation request was rejected';

ALTER TABLE core.bookings
    ADD COLUMN IF NOT EXISTS cancellation_rejected_by VARCHAR(200);
COMMENT ON COLUMN core.bookings.cancellation_rejected_by IS 'Who rejected the cancellation (name or email)';

ALTER TABLE core.bookings
    ADD COLUMN IF NOT EXISTS cancellation_rejection_reason TEXT;
COMMENT ON COLUMN core.bookings.cancellation_rejection_reason IS 'Reason provided when rejecting cancellation';

-- =====================================================
-- STEP 3: Create indexes for cancellation workflow queries
-- =====================================================

-- Index for finding bookings with pending cancellation requests
CREATE INDEX IF NOT EXISTS idx_bookings_cancellation_pending
    ON core.bookings (status, cancellation_requested_at)
    WHERE status = 'cancellation_requested';
COMMENT ON INDEX core.idx_bookings_cancellation_pending IS 'Optimizes queries for pending cancellation requests';

-- Index for cancellation audit queries (who cancelled what when)
CREATE INDEX IF NOT EXISTS idx_bookings_cancelled_at
    ON core.bookings (cancelled_at DESC)
    WHERE cancelled_at IS NOT NULL;
COMMENT ON INDEX core.idx_bookings_cancelled_at IS 'Optimizes queries for cancelled bookings by date';

-- =====================================================
-- STEP 4: Verify the partial unique index still works correctly
-- =====================================================
-- The existing idx_booking_date_slot_active index uses:
-- WHERE status != 'cancelled' AND deleted_at IS NULL
--
-- With cancellation_requested status:
-- - CANCELLATION_REQUESTED keeps slot HELD (not cancelled)
-- - Only CANCELLED releases the slot
-- This is the correct behavior for our workflow!
-- =====================================================

COMMIT;

-- =====================================================
-- VERIFICATION QUERIES (run manually to confirm)
-- =====================================================
-- SELECT enumlabel FROM pg_enum WHERE enumtypid = 'booking_status'::regtype;
--
-- SELECT column_name, data_type, is_nullable
-- FROM information_schema.columns
-- WHERE table_schema = 'core' AND table_name = 'bookings'
-- AND column_name LIKE '%cancel%' OR column_name = 'previous_status';
-- =====================================================

-- =====================================================
-- ROLLBACK SCRIPT (keep as comment for emergency)
-- =====================================================
-- BEGIN;
-- ALTER TABLE core.bookings DROP COLUMN IF EXISTS previous_status;
-- ALTER TABLE core.bookings DROP COLUMN IF EXISTS cancellation_requested_at;
-- ALTER TABLE core.bookings DROP COLUMN IF EXISTS cancellation_requested_by;
-- ALTER TABLE core.bookings DROP COLUMN IF EXISTS cancellation_reason;
-- ALTER TABLE core.bookings DROP COLUMN IF EXISTS cancelled_at;
-- ALTER TABLE core.bookings DROP COLUMN IF EXISTS cancelled_by;
-- ALTER TABLE core.bookings DROP COLUMN IF EXISTS cancellation_approved_reason;
-- ALTER TABLE core.bookings DROP COLUMN IF EXISTS cancellation_rejected_at;
-- ALTER TABLE core.bookings DROP COLUMN IF EXISTS cancellation_rejected_by;
-- ALTER TABLE core.bookings DROP COLUMN IF EXISTS cancellation_rejection_reason;
-- DROP INDEX IF EXISTS core.idx_bookings_cancellation_pending;
-- DROP INDEX IF EXISTS core.idx_bookings_cancelled_at;
-- -- Note: Cannot remove enum values in PostgreSQL without recreating the type
-- COMMIT;
