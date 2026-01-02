-- =====================================================
-- Migration 007a: Add CANCELLATION_REQUESTED enum value
-- Must run SEPARATELY before 007b due to PostgreSQL limitation
-- =====================================================

-- Add the enum value (runs outside transaction by default)
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
        RAISE NOTICE 'booking_status enum does not exist yet';
END $$;
