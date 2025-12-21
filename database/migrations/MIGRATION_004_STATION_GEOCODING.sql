-- ============================================================================
-- MIGRATION 004: Add Geocoding Columns to Stations
-- ============================================================================
-- Purpose: Enable distance-based service area calculations
--          Support multi-station nearest-station lookup
--
-- Business Requirements:
-- - Station lat/lng for distance calculations to customer addresses
-- - Service area radius in miles (default 150, >150 requires escalation)
-- - Nearest station lookup for travel fee calculation
--
-- Run: After MIGRATION_003_ENTERPRISE_ADDRESSES_FOOD_INCENTIVES.sql
-- ============================================================================

-- Check current state
SELECT 'BEFORE MIGRATION: Checking current stations table columns' AS status;
SELECT column_name, data_type
FROM information_schema.columns
WHERE table_schema = 'identity' AND table_name = 'stations'
ORDER BY ordinal_position;

-- ============================================================================
-- STEP 1: Add Geocoding Columns to Stations
-- ============================================================================

-- Add latitude column
ALTER TABLE identity.stations
ADD COLUMN IF NOT EXISTS lat DECIMAL(10, 8) NULL;

COMMENT ON COLUMN identity.stations.lat IS 'Latitude of station headquarters (from geocoding station address)';

-- Add longitude column
ALTER TABLE identity.stations
ADD COLUMN IF NOT EXISTS lng DECIMAL(11, 8) NULL;

COMMENT ON COLUMN identity.stations.lng IS 'Longitude of station headquarters (from geocoding station address)';

-- Add geocoding metadata
ALTER TABLE identity.stations
ADD COLUMN IF NOT EXISTS geocoded_at TIMESTAMPTZ NULL;

COMMENT ON COLUMN identity.stations.geocoded_at IS 'When station address was last geocoded';

ALTER TABLE identity.stations
ADD COLUMN IF NOT EXISTS geocode_status VARCHAR(20) DEFAULT 'pending';

COMMENT ON COLUMN identity.stations.geocode_status IS 'Geocoding status: pending, success, failed';

-- ============================================================================
-- STEP 2: Update Service Area Radius Default
-- ============================================================================

-- Update default service_area_radius to 150 miles (business rule)
-- Note: service_area_radius column already exists, just update default value
ALTER TABLE identity.stations
ALTER COLUMN service_area_radius SET DEFAULT 150;

COMMENT ON COLUMN identity.stations.service_area_radius IS 'Service radius in miles. Default 150. Distances >150 require human escalation.';

-- Add escalation threshold column for beyond-radius handling
ALTER TABLE identity.stations
ADD COLUMN IF NOT EXISTS escalation_radius_miles INTEGER DEFAULT 150;

COMMENT ON COLUMN identity.stations.escalation_radius_miles IS 'Miles beyond which bookings require human escalation. Default 150.';

-- ============================================================================
-- STEP 3: Create Geospatial Index for Nearest Station Lookups
-- ============================================================================

CREATE INDEX IF NOT EXISTS idx_stations_geo
ON identity.stations (lat, lng)
WHERE lat IS NOT NULL AND lng IS NOT NULL;

-- ============================================================================
-- STEP 4: Seed Fremont Station (First Station)
-- ============================================================================

-- Insert or update Fremont station with actual business address
INSERT INTO identity.stations (
    id,
    name,
    code,
    display_name,
    address,
    city,
    state,
    postal_code,
    phone,
    email,
    country,
    timezone,
    status,
    service_area_radius,
    escalation_radius_miles,
    lat,
    lng,
    geocode_status,
    geocoded_at,
    settings,
    max_concurrent_bookings,
    booking_lead_time_hours
) VALUES (
    gen_random_uuid(),
    'Fremont Station',
    'CA-FREMONT-001',
    'My Hibachi - Fremont, CA (Main)',
    '47481 Towhee St',
    'Fremont',
    'CA',
    '94539',
    '+19167408768',
    'cs@myhibachichef.com',
    'US',
    'America/Los_Angeles',
    'active',
    150,  -- 150 mile radius
    150,  -- Escalation at 150 miles
    37.5485,   -- Fremont, CA latitude (approximate for 47481 Towhee St)
    -121.9886, -- Fremont, CA longitude (approximate)
    'success',
    NOW(),
    '{"is_primary": true}'::json,
    10,
    24
)
ON CONFLICT (code) DO UPDATE SET
    name = EXCLUDED.name,
    display_name = EXCLUDED.display_name,
    address = EXCLUDED.address,
    city = EXCLUDED.city,
    state = EXCLUDED.state,
    postal_code = EXCLUDED.postal_code,
    phone = EXCLUDED.phone,
    email = EXCLUDED.email,
    timezone = EXCLUDED.timezone,
    service_area_radius = EXCLUDED.service_area_radius,
    escalation_radius_miles = EXCLUDED.escalation_radius_miles,
    lat = EXCLUDED.lat,
    lng = EXCLUDED.lng,
    geocode_status = EXCLUDED.geocode_status,
    geocoded_at = EXCLUDED.geocoded_at,
    settings = EXCLUDED.settings,
    updated_at = NOW();

-- Delete placeholder Texas stations (if they exist from old test data)
DELETE FROM identity.stations
WHERE code IN ('HOU', 'DFW', 'AUS')
  AND city IS NULL;

-- ============================================================================
-- VERIFICATION
-- ============================================================================

SELECT 'AFTER MIGRATION: Verifying station data' AS status;

SELECT
    id,
    code,
    name,
    display_name,
    city,
    state,
    lat,
    lng,
    service_area_radius,
    escalation_radius_miles,
    geocode_status
FROM identity.stations
WHERE status = 'active'
ORDER BY code;

-- Verify new columns exist
SELECT 'COLUMN CHECK: New columns added' AS status;
SELECT column_name, data_type, column_default
FROM information_schema.columns
WHERE table_schema = 'identity'
  AND table_name = 'stations'
  AND column_name IN ('lat', 'lng', 'geocoded_at', 'geocode_status', 'escalation_radius_miles')
ORDER BY column_name;

SELECT 'MIGRATION 004 COMPLETE' AS status;
