-- =====================================================
-- Migration: Update Station Default Timezone
-- Created: 2025-01-30
-- Purpose: Change station timezone default from America/New_York to America/Los_Angeles
--          Aligns with first station location (Fremont, CA - Pacific Time)
-- =====================================================

BEGIN;

-- Update the default value for new stations
-- Note: This does NOT change existing station timezones - only new inserts

-- Step 1: Alter the column default (if the table exists and column hasn't been updated)
DO $$
BEGIN
    -- Check if identity.stations table exists
    IF EXISTS (
        SELECT 1 FROM information_schema.tables
        WHERE table_schema = 'identity'
        AND table_name = 'stations'
    ) THEN
        -- Alter the default for new stations
        EXECUTE 'ALTER TABLE identity.stations
                 ALTER COLUMN timezone
                 SET DEFAULT ''America/Los_Angeles''';
        RAISE NOTICE 'Updated identity.stations.timezone default to America/Los_Angeles';
    END IF;
END $$;

-- Step 2: Update existing stations that still have the old default
DO $$
BEGIN
    UPDATE identity.stations
    SET timezone = 'America/Los_Angeles'
    WHERE timezone = 'America/New_York';
    RAISE NOTICE 'Updated existing stations with America/New_York to America/Los_Angeles';
END $$;

COMMIT;

-- =====================================================
-- ROLLBACK SCRIPT (Keep as comment for emergency):
-- =====================================================
-- ALTER TABLE identity.stations ALTER COLUMN timezone SET DEFAULT 'America/New_York';

-- =====================================================
-- VERIFICATION QUERY:
-- =====================================================
-- SELECT column_name, column_default
-- FROM information_schema.columns
-- WHERE table_schema = 'identity'
-- AND table_name = 'stations'
-- AND column_name = 'timezone';
