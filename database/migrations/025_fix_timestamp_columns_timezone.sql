-- Migration: Fix timestamp columns to use consistent timezone-aware timestamps
-- Purpose: Align all timestamp columns in core.bookings to use 'timestamp with time zone'
-- This fixes the asyncpg error: "can't subtract offset-naive and offset-aware datetimes"
-- 
-- Industry Standard: All timestamp columns should be timestamptz (timestamp with time zone)
-- This ensures proper handling across different timezones and Python datetime objects
--
-- Created: 2025-02-05
-- Author: AI Agent

BEGIN;

-- Convert deadline columns from 'timestamp without time zone' to 'timestamp with time zone'
-- These columns track deposit deadlines and should be timezone-aware

ALTER TABLE core.bookings 
    ALTER COLUMN customer_deposit_deadline TYPE timestamp with time zone 
    USING customer_deposit_deadline AT TIME ZONE 'UTC';

ALTER TABLE core.bookings 
    ALTER COLUMN internal_deadline TYPE timestamp with time zone 
    USING internal_deadline AT TIME ZONE 'UTC';

ALTER TABLE core.bookings 
    ALTER COLUMN deposit_deadline TYPE timestamp with time zone 
    USING deposit_deadline AT TIME ZONE 'UTC';

ALTER TABLE core.bookings 
    ALTER COLUMN deposit_confirmed_at TYPE timestamp with time zone 
    USING deposit_confirmed_at AT TIME ZONE 'UTC';

ALTER TABLE core.bookings 
    ALTER COLUMN held_at TYPE timestamp with time zone 
    USING held_at AT TIME ZONE 'UTC';

-- Add comments documenting the change
COMMENT ON COLUMN core.bookings.customer_deposit_deadline IS 'Customer-facing deposit deadline (2 hours) - timezone-aware UTC';
COMMENT ON COLUMN core.bookings.internal_deadline IS 'Internal enforcement deadline (24 hours grace) - timezone-aware UTC';
COMMENT ON COLUMN core.bookings.deposit_deadline IS 'Legacy deposit deadline for backward compatibility - timezone-aware UTC';
COMMENT ON COLUMN core.bookings.deposit_confirmed_at IS 'When deposit was confirmed - timezone-aware UTC';
COMMENT ON COLUMN core.bookings.held_at IS 'When booking was put on hold - timezone-aware UTC';

COMMIT;

-- Verification query (run after migration):
-- SELECT column_name, data_type 
-- FROM information_schema.columns 
-- WHERE table_schema='core' AND table_name='bookings' 
-- AND column_name IN ('customer_deposit_deadline', 'internal_deadline', 'deposit_deadline', 'deposit_confirmed_at', 'held_at');
