-- =====================================================
-- Migration 007b: Add cancellation workflow columns and indexes
-- Run AFTER 007a (enum value must be committed first)
-- =====================================================

BEGIN;

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

-- Index for finding bookings with pending cancellation requests
CREATE INDEX IF NOT EXISTS idx_bookings_cancellation_pending
    ON core.bookings (status, cancellation_requested_at)
    WHERE status = 'cancellation_requested';
COMMENT ON INDEX core.idx_bookings_cancellation_pending IS 'Optimizes queries for pending cancellation requests';

-- Index for cancellation audit queries
CREATE INDEX IF NOT EXISTS idx_bookings_cancelled_at
    ON core.bookings (cancelled_at DESC)
    WHERE cancelled_at IS NOT NULL;
COMMENT ON INDEX core.idx_bookings_cancelled_at IS 'Optimizes queries for cancelled bookings by date';

COMMIT;

-- Verification
SELECT 'Cancellation columns added successfully' AS status;
