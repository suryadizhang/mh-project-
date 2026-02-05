-- Migration: Add booking_datetime computed column
-- Purpose: Bridge between model using date+slot and code expecting booking_datetime
-- Date: 2026-02-05
--
-- This adds a GENERATED ALWAYS AS column that computes booking_datetime from date + slot.
-- This allows existing code that queries booking_datetime to work without data redundancy.

BEGIN;

-- Add computed column (date + slot → timestamp)
-- Uses GENERATED ALWAYS AS STORED for performance (computed on insert/update, not on select)
ALTER TABLE core.bookings
ADD COLUMN IF NOT EXISTS booking_datetime TIMESTAMP WITH TIME ZONE
GENERATED ALWAYS AS (date + slot) STORED;

-- Add index for queries that filter/order by booking_datetime
CREATE INDEX IF NOT EXISTS ix_core_bookings_booking_datetime
ON core.bookings (booking_datetime);

-- Add comment for documentation
COMMENT ON COLUMN core.bookings.booking_datetime IS
'Computed column: date + slot combined into timestamp. Generated automatically.';

COMMIT;
