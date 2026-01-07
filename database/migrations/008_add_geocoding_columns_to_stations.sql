-- =====================================================
-- Migration 008: Add Geocoding Columns to Stations Table
-- Created: 2025-01-31
-- Author: Copilot Agent
-- Batch: 1
-- =====================================================
--
-- CONTEXT:
-- The Station model in stations.py defines 5 geocoding columns
-- that do NOT exist in production database. These columns are
-- actively used by:
--   - apps/backend/src/services/address_service.py (geocode_address)
--   - apps/backend/src/routers/v1/station_admin.py (station endpoints)
--
-- COLUMNS TO ADD:
--   1. lat - Latitude (Numeric 10,8) for GPS coordinates
--   2. lng - Longitude (Numeric 11,8) for GPS coordinates
--   3. geocoded_at - Timestamp when geocoding was performed
--   4. geocode_status - Status of geocoding ('pending', 'success', 'failed', 'skipped')
--   5. escalation_radius_miles - Custom escalation radius for this station
--
-- PURPOSE:
-- These columns support:
--   - Travel fee calculation based on venue distance from station
--   - Chef assignment optimization based on location
--   - Service area validation
--   - Escalation rules based on station coverage area
--
-- SAFETY:
-- - All columns are NULLABLE (no data backfill required)
-- - Uses IF NOT EXISTS for idempotent runs
-- - Includes rollback script at bottom
--
-- =====================================================

BEGIN;

-- =====================================================
-- Step 1: Add lat column (latitude coordinate)
-- =====================================================
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_schema = 'identity'
        AND table_name = 'stations'
        AND column_name = 'lat'
    ) THEN
        ALTER TABLE identity.stations
        ADD COLUMN lat NUMERIC(10, 8);

        COMMENT ON COLUMN identity.stations.lat IS
            'Latitude coordinate for station location. Used for travel fee and chef assignment calculations.';

        RAISE NOTICE 'Added column: lat';
    ELSE
        RAISE NOTICE 'Column lat already exists, skipping';
    END IF;
END $$;

-- =====================================================
-- Step 2: Add lng column (longitude coordinate)
-- =====================================================
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_schema = 'identity'
        AND table_name = 'stations'
        AND column_name = 'lng'
    ) THEN
        ALTER TABLE identity.stations
        ADD COLUMN lng NUMERIC(11, 8);

        COMMENT ON COLUMN identity.stations.lng IS
            'Longitude coordinate for station location. Used for travel fee and chef assignment calculations.';

        RAISE NOTICE 'Added column: lng';
    ELSE
        RAISE NOTICE 'Column lng already exists, skipping';
    END IF;
END $$;

-- =====================================================
-- Step 3: Add geocoded_at column (geocoding timestamp)
-- =====================================================
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_schema = 'identity'
        AND table_name = 'stations'
        AND column_name = 'geocoded_at'
    ) THEN
        ALTER TABLE identity.stations
        ADD COLUMN geocoded_at TIMESTAMP WITH TIME ZONE;

        COMMENT ON COLUMN identity.stations.geocoded_at IS
            'Timestamp when address was last geocoded. NULL if never geocoded.';

        RAISE NOTICE 'Added column: geocoded_at';
    ELSE
        RAISE NOTICE 'Column geocoded_at already exists, skipping';
    END IF;
END $$;

-- =====================================================
-- Step 4: Add geocode_status column (geocoding status)
-- =====================================================
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_schema = 'identity'
        AND table_name = 'stations'
        AND column_name = 'geocode_status'
    ) THEN
        ALTER TABLE identity.stations
        ADD COLUMN geocode_status VARCHAR(20) DEFAULT 'pending';

        COMMENT ON COLUMN identity.stations.geocode_status IS
            'Status of geocoding: pending, success, failed, skipped. Default is pending.';

        RAISE NOTICE 'Added column: geocode_status';
    ELSE
        RAISE NOTICE 'Column geocode_status already exists, skipping';
    END IF;
END $$;

-- =====================================================
-- Step 5: Add escalation_radius_miles column
-- =====================================================
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_schema = 'identity'
        AND table_name = 'stations'
        AND column_name = 'escalation_radius_miles'
    ) THEN
        ALTER TABLE identity.stations
        ADD COLUMN escalation_radius_miles INTEGER DEFAULT 50;

        COMMENT ON COLUMN identity.stations.escalation_radius_miles IS
            'Escalation radius in miles for this station. Events beyond this distance may escalate to other stations. Default is 50 miles.';

        RAISE NOTICE 'Added column: escalation_radius_miles';
    ELSE
        RAISE NOTICE 'Column escalation_radius_miles already exists, skipping';
    END IF;
END $$;

-- =====================================================
-- Step 6: Create index for geocoded stations lookup
-- =====================================================
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_indexes
        WHERE schemaname = 'identity'
        AND tablename = 'stations'
        AND indexname = 'idx_stations_geocoded'
    ) THEN
        CREATE INDEX idx_stations_geocoded
        ON identity.stations (geocode_status)
        WHERE geocode_status = 'success';

        RAISE NOTICE 'Created index: idx_stations_geocoded';
    ELSE
        RAISE NOTICE 'Index idx_stations_geocoded already exists, skipping';
    END IF;
END $$;

-- =====================================================
-- Step 7: Create spatial index for lat/lng queries
-- =====================================================
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_indexes
        WHERE schemaname = 'identity'
        AND tablename = 'stations'
        AND indexname = 'idx_stations_lat_lng'
    ) THEN
        CREATE INDEX idx_stations_lat_lng
        ON identity.stations (lat, lng)
        WHERE lat IS NOT NULL AND lng IS NOT NULL;

        RAISE NOTICE 'Created index: idx_stations_lat_lng';
    ELSE
        RAISE NOTICE 'Index idx_stations_lat_lng already exists, skipping';
    END IF;
END $$;

COMMIT;

-- =====================================================
-- Verification Query (run manually after migration)
-- =====================================================
-- SELECT column_name, data_type, is_nullable, column_default
-- FROM information_schema.columns
-- WHERE table_schema = 'identity'
-- AND table_name = 'stations'
-- AND column_name IN ('lat', 'lng', 'geocoded_at', 'geocode_status', 'escalation_radius_miles')
-- ORDER BY ordinal_position;

-- =====================================================
-- ROLLBACK SCRIPT (use only if migration needs to be reverted)
-- =====================================================
--
-- BEGIN;
--
-- DROP INDEX IF EXISTS identity.idx_stations_lat_lng;
-- DROP INDEX IF EXISTS identity.idx_stations_geocoded;
--
-- ALTER TABLE identity.stations DROP COLUMN IF EXISTS escalation_radius_miles;
-- ALTER TABLE identity.stations DROP COLUMN IF EXISTS geocode_status;
-- ALTER TABLE identity.stations DROP COLUMN IF EXISTS geocoded_at;
-- ALTER TABLE identity.stations DROP COLUMN IF EXISTS lng;
-- ALTER TABLE identity.stations DROP COLUMN IF EXISTS lat;
--
-- COMMIT;
--
-- =====================================================
