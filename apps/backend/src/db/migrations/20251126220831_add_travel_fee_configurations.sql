-- Migration: Add travel_fee_configurations table
-- Created: 2025-11-26 22:08:31
-- Purpose: Enable dynamic, station-based travel fee management

-- ============================================================================
-- TABLE: travel_fee_configurations
-- ============================================================================

CREATE TABLE IF NOT EXISTS core.travel_fee_configurations (
    -- Primary Key
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Foreign Keys
    station_id UUID NOT NULL UNIQUE REFERENCES identity.stations(id) ON DELETE CASCADE,

    -- Station Location (for distance calculation)
    station_name VARCHAR(100) NOT NULL,
    station_address TEXT NOT NULL,
    station_city VARCHAR(100) NOT NULL,
    station_state VARCHAR(50) NOT NULL,
    station_postal_code VARCHAR(20) NOT NULL,
    station_latitude NUMERIC(10, 7),  -- Geocoded latitude
    station_longitude NUMERIC(10, 7),  -- Geocoded longitude

    -- Travel Fee Rules
    free_miles NUMERIC(6, 2) NOT NULL DEFAULT 30.00,  -- Miles included free
    price_per_mile NUMERIC(6, 2) NOT NULL DEFAULT 2.00,  -- Rate per mile beyond free
    max_service_distance NUMERIC(6, 2),  -- Max distance (NULL = unlimited)

    -- Status
    is_active BOOLEAN NOT NULL DEFAULT true,

    -- Additional Settings
    settings JSONB NOT NULL DEFAULT '{}',
    notes TEXT,
    display_order INTEGER NOT NULL DEFAULT 0,

    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),

    -- Constraints
    CONSTRAINT travel_fee_free_miles_non_negative CHECK (free_miles >= 0),
    CONSTRAINT travel_fee_price_per_mile_non_negative CHECK (price_per_mile >= 0),
    CONSTRAINT travel_fee_max_distance_valid CHECK (
        max_service_distance IS NULL OR max_service_distance >= free_miles
    )
);

-- ============================================================================
-- INDEXES
-- ============================================================================

CREATE INDEX IF NOT EXISTS idx_travel_fee_station_id
    ON core.travel_fee_configurations(station_id);

CREATE INDEX IF NOT EXISTS idx_travel_fee_is_active
    ON core.travel_fee_configurations(is_active);

-- ============================================================================
-- COMMENTS
-- ============================================================================

COMMENT ON TABLE core.travel_fee_configurations IS
'Station-based travel fee configuration for dynamic pricing';

COMMENT ON COLUMN core.travel_fee_configurations.free_miles IS
'Miles included free (e.g., 30.00)';

COMMENT ON COLUMN core.travel_fee_configurations.price_per_mile IS
'Rate per mile beyond free miles (e.g., 2.00 = $2/mile)';

COMMENT ON COLUMN core.travel_fee_configurations.max_service_distance IS
'Maximum service distance in miles (NULL = unlimited)';

COMMENT ON COLUMN core.travel_fee_configurations.settings IS
'Additional travel fee settings (zone pricing, time-based, etc.)';

COMMENT ON COLUMN core.travel_fee_configurations.notes IS
'Admin notes (e.g., "Main station - covers Bay Area")';

-- ============================================================================
-- SEED DATA: Fremont Station (Main)
-- ============================================================================

-- Check if identity.stations table has any stations
-- If yes, insert travel fee config for the first station
-- If no, we'll need to create a station first

DO $$
DECLARE
    v_station_id UUID;
    v_station_exists BOOLEAN;
BEGIN
    -- Check if any station exists
    SELECT EXISTS(SELECT 1 FROM identity.stations LIMIT 1) INTO v_station_exists;

    IF v_station_exists THEN
        -- Get the first active station
        SELECT id INTO v_station_id
        FROM identity.stations
        WHERE status = 'active'
        ORDER BY created_at ASC
        LIMIT 1;

        -- Insert travel fee config if station found
        IF v_station_id IS NOT NULL THEN
            INSERT INTO core.travel_fee_configurations (
                station_id,
                station_name,
                station_address,
                station_city,
                station_state,
                station_postal_code,
                free_miles,
                price_per_mile,
                is_active,
                notes,
                display_order
            ) VALUES (
                v_station_id,
                'Fremont Station (Main)',
                '47481 Towhee St',
                'Fremont',
                'CA',
                '94539',
                30.00,
                2.00,
                true,
                'Main station covering Bay Area and Sacramento regions. First 30 miles free, then $2 per mile.',
                1
            )
            ON CONFLICT (station_id) DO NOTHING;

            RAISE NOTICE 'Travel fee configuration created for station ID: %', v_station_id;
        ELSE
            RAISE NOTICE 'No active station found - travel fee config not created';
        END IF;
    ELSE
        RAISE NOTICE 'No stations exist - travel fee config will be created when first station is added';
    END IF;
END $$;

-- ============================================================================
-- ROLLBACK INSTRUCTIONS
-- ============================================================================

-- To rollback this migration:
-- DROP TABLE IF EXISTS core.travel_fee_configurations CASCADE;
