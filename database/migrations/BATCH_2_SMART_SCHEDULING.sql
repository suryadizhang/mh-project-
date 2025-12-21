-- ============================================================================
-- BATCH 2: SMART SCHEDULING SYSTEM MIGRATION
-- ============================================================================
-- Created: 2024-12-20
-- Purpose: Add location tracking, chef optimization, and scheduling features
-- 
-- IMPORTANT: Run on STAGING first, then PRODUCTION after verification
-- ============================================================================

-- ============================================================================
-- PHASE 1: BOOKING LOCATION ENHANCEMENTS
-- ============================================================================

-- Add geocoded location to bookings (for travel time calculation)
ALTER TABLE core.bookings 
    ADD COLUMN IF NOT EXISTS venue_lat DECIMAL(10, 8),
    ADD COLUMN IF NOT EXISTS venue_lng DECIMAL(11, 8),
    ADD COLUMN IF NOT EXISTS venue_address_normalized TEXT;

-- Add event duration (calculated based on party size: 90-120 min)
ALTER TABLE core.bookings 
    ADD COLUMN IF NOT EXISTS event_duration_minutes INTEGER DEFAULT 90;

-- Add preferred chef (customer can request specific chef)
ALTER TABLE core.bookings 
    ADD COLUMN IF NOT EXISTS preferred_chef_id UUID REFERENCES ops.chefs(id),
    ADD COLUMN IF NOT EXISTS is_chef_preference_required BOOLEAN DEFAULT FALSE;

-- Add adjustment tracking (if slot time was shifted from standard)
ALTER TABLE core.bookings 
    ADD COLUMN IF NOT EXISTS adjusted_slot_time TIME,
    ADD COLUMN IF NOT EXISTS adjustment_reason TEXT;

COMMENT ON COLUMN core.bookings.venue_lat IS 'Latitude of event venue for travel time calculation';
COMMENT ON COLUMN core.bookings.venue_lng IS 'Longitude of event venue for travel time calculation';
COMMENT ON COLUMN core.bookings.venue_address_normalized IS 'Normalized address from Google Places API';
COMMENT ON COLUMN core.bookings.event_duration_minutes IS 'Event duration in minutes (90-120 based on party size)';
COMMENT ON COLUMN core.bookings.preferred_chef_id IS 'Customer-requested chef (highest priority for assignment)';
COMMENT ON COLUMN core.bookings.is_chef_preference_required IS 'If true, booking fails if preferred chef unavailable';
COMMENT ON COLUMN core.bookings.adjusted_slot_time IS 'Actual start time if different from standard slot';
COMMENT ON COLUMN core.bookings.adjustment_reason IS 'Reason for slot adjustment (travel time, customer request, etc.)';

-- ============================================================================
-- PHASE 1: CHEF LOCATION TABLE
-- ============================================================================

CREATE TABLE IF NOT EXISTS ops.chef_locations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    chef_id UUID NOT NULL REFERENCES ops.chefs(id) ON DELETE CASCADE,
    
    -- Home/base location
    home_address TEXT,
    home_lat DECIMAL(10, 8),
    home_lng DECIMAL(11, 8),
    
    -- Preferences
    preferred_radius_km DECIMAL(6, 2) DEFAULT 50,
    max_radius_km DECIMAL(6, 2) DEFAULT 100,
    
    -- Audit
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    
    UNIQUE(chef_id)
);

COMMENT ON TABLE ops.chef_locations IS 'Chef home locations for travel time optimization';
COMMENT ON COLUMN ops.chef_locations.preferred_radius_km IS 'Preferred max travel distance (soft limit)';
COMMENT ON COLUMN ops.chef_locations.max_radius_km IS 'Absolute max travel distance (hard limit)';

-- ============================================================================
-- PHASE 1: SLOT CONFIGURATION TABLE
-- ============================================================================

CREATE TABLE IF NOT EXISTS ops.slot_configurations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    
    -- Slot identification
    slot_name VARCHAR(10) NOT NULL,           -- '12PM', '3PM', '6PM', '9PM'
    base_time TIME NOT NULL,                   -- 12:00, 15:00, 18:00, 21:00
    
    -- Adjustment limits
    min_adjust_minutes INTEGER DEFAULT -30,    -- How early can start (negative = earlier)
    max_adjust_minutes INTEGER DEFAULT 60,     -- How late can start
    
    -- Event duration limits
    min_event_duration INTEGER DEFAULT 90,     -- Minimum event length
    max_event_duration INTEGER DEFAULT 120,    -- Maximum event length
    
    -- Configuration
    is_active BOOLEAN DEFAULT TRUE,
    station_id UUID REFERENCES identity.stations(id),  -- Per-station override
    
    -- Audit
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    
    UNIQUE(slot_name, COALESCE(station_id, '00000000-0000-0000-0000-000000000000'::uuid))
);

COMMENT ON TABLE ops.slot_configurations IS 'Time slot configuration with adjustment flexibility';
COMMENT ON COLUMN ops.slot_configurations.min_adjust_minutes IS 'Earliest adjustment (negative = before base time)';
COMMENT ON COLUMN ops.slot_configurations.max_adjust_minutes IS 'Latest adjustment (positive = after base time)';

-- Insert default slot configurations
INSERT INTO ops.slot_configurations (slot_name, base_time, min_adjust_minutes, max_adjust_minutes) VALUES
    ('12PM', '12:00:00', 0, 60),       -- 12PM: 12:00-13:00 (no earlier than noon)
    ('3PM', '15:00:00', -30, 60),      -- 3PM: 14:30-16:00
    ('6PM', '18:00:00', -60, 60),      -- 6PM: 17:00-19:00
    ('9PM', '21:00:00', -60, 30)       -- 9PM: 20:00-21:30 (limited late extension)
ON CONFLICT DO NOTHING;

-- ============================================================================
-- PHASE 3: TRAVEL TIME CACHE TABLE
-- ============================================================================

CREATE TABLE IF NOT EXISTS ops.travel_time_cache (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    
    -- Location pair (rounded for cache efficiency)
    origin_lat DECIMAL(10, 8) NOT NULL,
    origin_lng DECIMAL(11, 8) NOT NULL,
    dest_lat DECIMAL(10, 8) NOT NULL,
    dest_lng DECIMAL(11, 8) NOT NULL,
    
    -- Time context
    departure_hour INTEGER,                    -- 0-23
    day_of_week INTEGER,                       -- 0=Sun, 6=Sat
    is_rush_hour BOOLEAN DEFAULT FALSE,
    
    -- Travel data
    base_duration_minutes INTEGER NOT NULL,    -- Without traffic
    traffic_duration_minutes INTEGER,          -- With traffic (from Google)
    distance_km DECIMAL(8, 2),
    route_summary TEXT,                        -- "via I-95 N"
    
    -- Cache management
    cached_at TIMESTAMPTZ DEFAULT NOW(),
    expires_at TIMESTAMPTZ DEFAULT (NOW() + INTERVAL '7 days'),
    hit_count INTEGER DEFAULT 0                -- Track usage
);

COMMENT ON TABLE ops.travel_time_cache IS 'Cached Google Maps travel times to reduce API calls';

-- Create index for fast cache lookups (rounded coordinates)
CREATE INDEX IF NOT EXISTS idx_travel_cache_lookup ON ops.travel_time_cache (
    ROUND(origin_lat::numeric, 2),
    ROUND(origin_lng::numeric, 2),
    ROUND(dest_lat::numeric, 2),
    ROUND(dest_lng::numeric, 2),
    departure_hour
) WHERE expires_at > NOW();

-- ============================================================================
-- PHASE 5: CHEF ASSIGNMENT TRACKING TABLE
-- ============================================================================

CREATE TABLE IF NOT EXISTS ops.chef_assignments (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    
    -- Core assignment
    booking_id UUID NOT NULL REFERENCES core.bookings(id) ON DELETE CASCADE,
    chef_id UUID NOT NULL REFERENCES ops.chefs(id),
    
    -- Assignment metadata
    assigned_at TIMESTAMPTZ DEFAULT NOW(),
    assigned_by UUID REFERENCES identity.users(id),
    assignment_type VARCHAR(20) NOT NULL DEFAULT 'manual',
        -- 'customer_requested', 'auto_optimized', 'manual', 'reassigned'
    
    -- Travel chain tracking (for optimization)
    previous_booking_id UUID REFERENCES core.bookings(id),
    travel_time_minutes INTEGER,
    travel_distance_km DECIMAL(8, 2),
    
    -- Optimization metadata
    optimization_score DECIMAL(5, 2),          -- 0-100 efficiency score
    alternatives_considered INTEGER,            -- How many chefs evaluated
    
    -- Notes
    notes TEXT,
    
    -- Audit
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    
    UNIQUE(booking_id)  -- One assignment per booking
);

COMMENT ON TABLE ops.chef_assignments IS 'Tracks chef assignments with optimization data';
COMMENT ON COLUMN ops.chef_assignments.optimization_score IS 'Efficiency score (0-100) based on travel, workload, skills';
COMMENT ON COLUMN ops.chef_assignments.previous_booking_id IS 'Previous booking in chef schedule (for travel chain)';

-- ============================================================================
-- PHASE 6: BOOKING NEGOTIATION TABLE
-- ============================================================================

CREATE TABLE IF NOT EXISTS core.booking_negotiations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    
    -- Booking references
    existing_booking_id UUID NOT NULL REFERENCES core.bookings(id),
    requesting_booking_id UUID REFERENCES core.bookings(id),  -- New booking needing slot
    
    -- Time shift proposal
    original_time TIME NOT NULL,
    proposed_time TIME NOT NULL,
    shift_minutes INTEGER NOT NULL,            -- +30 = later, -30 = earlier
    
    -- Request details
    reason TEXT,
    status VARCHAR(20) NOT NULL DEFAULT 'pending',
        -- 'pending', 'sent', 'accepted', 'declined', 'expired', 'cancelled'
    
    -- Communication tracking
    notification_method VARCHAR(20),           -- 'sms', 'email', 'both'
    notification_sent_at TIMESTAMPTZ,
    reminder_sent_at TIMESTAMPTZ,
    customer_response_at TIMESTAMPTZ,
    expires_at TIMESTAMPTZ,
    
    -- Incentive (optional)
    incentive_offered TEXT,                    -- "10% off next booking"
    incentive_accepted BOOLEAN,
    
    -- Audit
    created_by UUID REFERENCES identity.users(id),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

COMMENT ON TABLE core.booking_negotiations IS 'Polite requests to shift existing booking times';
COMMENT ON COLUMN core.booking_negotiations.shift_minutes IS 'Time shift: positive=later, negative=earlier';

-- ============================================================================
-- INDEXES FOR PERFORMANCE
-- ============================================================================

-- Booking location index (for nearby chef search)
CREATE INDEX IF NOT EXISTS idx_bookings_venue_location 
    ON core.bookings(venue_lat, venue_lng) 
    WHERE venue_lat IS NOT NULL AND deleted_at IS NULL;

-- Chef assignments by chef and date (for schedule queries)
CREATE INDEX IF NOT EXISTS idx_chef_assignments_chef_date 
    ON ops.chef_assignments(chef_id, assigned_at);

-- Booking assignments by booking (for quick lookup)
CREATE INDEX IF NOT EXISTS idx_chef_assignments_booking 
    ON ops.chef_assignments(booking_id);

-- Negotiations by status (for pending notifications)
CREATE INDEX IF NOT EXISTS idx_negotiations_status 
    ON core.booking_negotiations(status, expires_at)
    WHERE status IN ('pending', 'sent');

-- ============================================================================
-- VERIFICATION QUERIES
-- ============================================================================

-- Verify columns were added to bookings
DO $$
BEGIN
    RAISE NOTICE 'Verifying booking columns...';
    
    IF EXISTS (SELECT 1 FROM information_schema.columns 
               WHERE table_schema = 'core' 
               AND table_name = 'bookings' 
               AND column_name = 'venue_lat') THEN
        RAISE NOTICE '✅ venue_lat column exists';
    ELSE
        RAISE WARNING '❌ venue_lat column missing';
    END IF;
    
    IF EXISTS (SELECT 1 FROM information_schema.columns 
               WHERE table_schema = 'core' 
               AND table_name = 'bookings' 
               AND column_name = 'preferred_chef_id') THEN
        RAISE NOTICE '✅ preferred_chef_id column exists';
    ELSE
        RAISE WARNING '❌ preferred_chef_id column missing';
    END IF;
END $$;

-- Verify new tables
DO $$
BEGIN
    RAISE NOTICE 'Verifying new tables...';
    
    IF EXISTS (SELECT 1 FROM information_schema.tables 
               WHERE table_schema = 'ops' AND table_name = 'chef_locations') THEN
        RAISE NOTICE '✅ ops.chef_locations table exists';
    END IF;
    
    IF EXISTS (SELECT 1 FROM information_schema.tables 
               WHERE table_schema = 'ops' AND table_name = 'slot_configurations') THEN
        RAISE NOTICE '✅ ops.slot_configurations table exists';
    END IF;
    
    IF EXISTS (SELECT 1 FROM information_schema.tables 
               WHERE table_schema = 'ops' AND table_name = 'travel_time_cache') THEN
        RAISE NOTICE '✅ ops.travel_time_cache table exists';
    END IF;
    
    IF EXISTS (SELECT 1 FROM information_schema.tables 
               WHERE table_schema = 'ops' AND table_name = 'chef_assignments') THEN
        RAISE NOTICE '✅ ops.chef_assignments table exists';
    END IF;
    
    IF EXISTS (SELECT 1 FROM information_schema.tables 
               WHERE table_schema = 'core' AND table_name = 'booking_negotiations') THEN
        RAISE NOTICE '✅ core.booking_negotiations table exists';
    END IF;
END $$;

-- Show slot configurations
SELECT slot_name, base_time, min_adjust_minutes, max_adjust_minutes 
FROM ops.slot_configurations ORDER BY base_time;

-- ============================================================================
-- ROLLBACK SCRIPT (if needed)
-- ============================================================================
/*
-- To rollback this migration, run:

-- Drop new tables
DROP TABLE IF EXISTS core.booking_negotiations CASCADE;
DROP TABLE IF EXISTS ops.chef_assignments CASCADE;
DROP TABLE IF EXISTS ops.travel_time_cache CASCADE;
DROP TABLE IF EXISTS ops.slot_configurations CASCADE;
DROP TABLE IF EXISTS ops.chef_locations CASCADE;

-- Remove booking columns
ALTER TABLE core.bookings 
    DROP COLUMN IF EXISTS venue_lat,
    DROP COLUMN IF EXISTS venue_lng,
    DROP COLUMN IF EXISTS venue_address_normalized,
    DROP COLUMN IF EXISTS event_duration_minutes,
    DROP COLUMN IF EXISTS preferred_chef_id,
    DROP COLUMN IF EXISTS is_chef_preference_required,
    DROP COLUMN IF EXISTS adjusted_slot_time,
    DROP COLUMN IF EXISTS adjustment_reason;
*/
