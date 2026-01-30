-- =====================================================
-- Migration: Add customer_requested_time column
-- Created: 2025-01-31
-- Purpose: Store the customer's original requested time separately
--          from the slot-snapped time used for scheduling
--
-- Option C+E Hybrid Implementation:
-- - Customer picks ANY time via time picker
-- - System snaps to nearest slot for chef scheduling
-- - customer_requested_time = what customer requested (display)
-- - slot = snapped time used for scheduling & conflict detection
-- =====================================================

BEGIN;

-- Add customer_requested_time column to bookings table
-- This stores the customer's original time request for display purposes
-- The slot column continues to hold the system-snapped time for scheduling
ALTER TABLE core.bookings
ADD COLUMN IF NOT EXISTS customer_requested_time TIME;

-- Add comment explaining the column
COMMENT ON COLUMN core.bookings.customer_requested_time IS
'Customer''s originally requested event time. The slot column holds the system-snapped time used for chef scheduling and conflict detection. Added for Option C+E Hybrid implementation.';

-- Optional: Backfill existing bookings (set customer_requested_time = slot for existing records)
-- This ensures consistency for existing data
UPDATE core.bookings
SET customer_requested_time = slot
WHERE customer_requested_time IS NULL AND slot IS NOT NULL;

COMMIT;

-- =====================================================
-- ROLLBACK SCRIPT (keep as comment for emergency):
-- =====================================================
-- ALTER TABLE core.bookings DROP COLUMN IF EXISTS customer_requested_time;
