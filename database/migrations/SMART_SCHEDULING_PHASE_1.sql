-- ============================================================================
-- SMART SCHEDULING SYSTEM - PHASE 1 DATABASE MIGRATION
-- Created: 2024-12-21
-- Purpose: Add location fields, slot configurations, and travel time cache
-- Batch: Batch 1 (Core Booking + Security)
-- ============================================================================

-- ============================================================================
-- PHASE 1A: Add location fields to existing bookings
-- ============================================================================

-- Add geocoding columns to bookings for venue location tracking
ALTER TABLE core.bookings
ADD COLUMN IF NOT EXISTS venue_lat DECIMAL(10,8),
ADD COLUMN IF NOT EXISTS venue_lng DECIMAL(11,8),
ADD COLUMN IF NOT EXISTS venue_address_normalized TEXT,
ADD COLUMN IF NOT EXISTS venue_geocoded_at TIMESTAMPTZ,
ADD COLUMN IF NOT EXISTS estimated_duration_minutes INT DEFAULT 90;

-- Comments for context
COMMENT ON COLUMN core.bookings.venue_lat IS 'Latitude from Google Geocoding API';
COMMENT ON COLUMN core.bookings.venue_lng IS 'Longitude from Google Geocoding API';
COMMENT ON COLUMN core.bookings.venue_address_normalized IS 'Standardized address from Google';
COMMENT ON COLUMN core.bookings.venue_geocoded_at IS 'Timestamp when venue was geocoded';
COMMENT ON COLUMN core.bookings.estimated_duration_minutes IS 'Event duration: 90-120 min based on party size';

-- Index for geospatial queries (only on rows with coordinates)
CREATE INDEX IF NOT EXISTS idx_bookings_geo
ON core.bookings (venue_lat, venue_lng)
WHERE venue_lat IS NOT NULL;


-- ============================================================================
-- PHASE 1D: Slot configuration table
-- ============================================================================

-- Create ops schema if it doesn't exist
CREATE SCHEMA IF NOT EXISTS ops;

CREATE TABLE IF NOT EXISTS ops.slot_configurations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Slot Identity
    slot_name VARCHAR(20) NOT NULL,        -- '12PM', '3PM', '6PM', '9PM'
    slot_time TIME NOT NULL,               -- 12:00, 15:00, 18:00, 21:00

    -- Flexibility Settings
    min_adjust_minutes INT DEFAULT -60,    -- Can start up to 60 min earlier
    max_adjust_minutes INT DEFAULT 60,     -- Can start up to 60 min later
    preferred_adjust_minutes INT DEFAULT 30, -- Preferred adjustment range ±30 min

    -- Duration Constraints
    min_event_duration INT DEFAULT 90,     -- Minimum event length (small party)
    max_event_duration INT DEFAULT 120,    -- Maximum event length (large party)

    -- Buffer Times
    buffer_before_minutes INT DEFAULT 30,  -- Travel/setup buffer before event
    buffer_after_minutes INT DEFAULT 15,   -- Cleanup buffer after event

    -- Capacity Settings
    max_bookings_per_slot INT DEFAULT 10,  -- Per slot across all chefs (system-wide)

    -- Status
    is_active BOOLEAN DEFAULT TRUE,

    -- Timestamps
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),

    -- Unique constraint on slot name
    UNIQUE(slot_name)
);

-- Insert default 4 slots (12PM, 3PM, 6PM, 9PM)
INSERT INTO ops.slot_configurations
    (slot_name, slot_time, min_event_duration, max_event_duration)
VALUES
    ('12PM', '12:00:00', 90, 120),
    ('3PM', '15:00:00', 90, 120),
    ('6PM', '18:00:00', 90, 120),
    ('9PM', '21:00:00', 90, 120)
ON CONFLICT (slot_name) DO NOTHING;

COMMENT ON TABLE ops.slot_configurations IS 'Configurable time slots for booking (default: 12PM, 3PM, 6PM, 9PM)';
COMMENT ON COLUMN ops.slot_configurations.min_adjust_minutes IS 'Maximum earlier adjustment allowed (negative value)';
COMMENT ON COLUMN ops.slot_configurations.max_adjust_minutes IS 'Maximum later adjustment allowed (positive value)';
COMMENT ON COLUMN ops.slot_configurations.preferred_adjust_minutes IS 'Preferred adjustment range (±30 min by default)';


-- ============================================================================
-- PHASE 4B: Travel time cache table (for Google Maps API results)
-- ============================================================================

CREATE TABLE IF NOT EXISTS ops.travel_time_cache (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Origin coordinates (chef location or station)
    origin_lat DECIMAL(10,8) NOT NULL,
    origin_lng DECIMAL(11,8) NOT NULL,

    -- Destination coordinates (venue)
    dest_lat DECIMAL(10,8) NOT NULL,
    dest_lng DECIMAL(11,8) NOT NULL,

    -- Time context
    departure_hour INT NOT NULL CHECK (departure_hour BETWEEN 0 AND 23),
    day_of_week INT NOT NULL CHECK (day_of_week BETWEEN 0 AND 6),
    is_rush_hour BOOLEAN DEFAULT FALSE,

    -- Travel data from Google Maps Distance Matrix API
    distance_meters INT NOT NULL,          -- Distance in meters
    distance_miles DECIMAL(8,2) NOT NULL,  -- Distance in miles (for travel fee)
    base_duration_minutes INT NOT NULL,    -- Duration without traffic
    traffic_duration_minutes INT,          -- Duration with traffic (rush hour)

    -- Cache metadata
    cached_at TIMESTAMPTZ DEFAULT NOW(),
    expires_at TIMESTAMPTZ DEFAULT (NOW() + INTERVAL '7 days'),
    api_response_status VARCHAR(20) DEFAULT 'OK',

    -- Constraints
    CONSTRAINT valid_distance CHECK (distance_meters > 0),
    CONSTRAINT valid_duration CHECK (base_duration_minutes > 0)
);

-- Unique constraint for cache lookups (rounded to ~100m precision)
CREATE UNIQUE INDEX IF NOT EXISTS idx_travel_cache_lookup
ON ops.travel_time_cache (
    ROUND(origin_lat::numeric, 3),
    ROUND(origin_lng::numeric, 3),
    ROUND(dest_lat::numeric, 3),
    ROUND(dest_lng::numeric, 3),
    departure_hour,
    day_of_week
);

-- Index for cache cleanup (expire old entries)
CREATE INDEX IF NOT EXISTS idx_travel_cache_expires
ON ops.travel_time_cache (expires_at);

COMMENT ON TABLE ops.travel_time_cache IS 'Cache for Google Maps Distance Matrix API results - expires after 7 days';
COMMENT ON COLUMN ops.travel_time_cache.distance_miles IS 'Distance in miles for travel fee calculation ($2/mile after 30 free miles)';
COMMENT ON COLUMN ops.travel_time_cache.traffic_duration_minutes IS 'Duration with traffic - used for rush hour (3-7PM weekday) scheduling';


-- ============================================================================
-- PHASE 3A: Chef locations table (for travel optimization)
-- ============================================================================

CREATE TABLE IF NOT EXISTS ops.chef_locations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Foreign key to chef
    chef_id UUID NOT NULL REFERENCES ops.chefs(id) ON DELETE CASCADE,

    -- Location data (home base)
    home_address_encrypted BYTEA,          -- Encrypted for PII protection
    home_lat DECIMAL(10,8) NOT NULL,
    home_lng DECIMAL(11,8) NOT NULL,

    -- Service area
    service_radius_miles DECIMAL(5,2) DEFAULT 50.0,  -- Max distance willing to travel

    -- Location settings
    is_primary BOOLEAN DEFAULT TRUE,       -- Primary home location
    location_type VARCHAR(20) DEFAULT 'home' CHECK (
        location_type IN ('home', 'office', 'temporary')
    ),

    -- Timestamps
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),

    -- Only one primary location per chef
    UNIQUE(chef_id, is_primary) -- Partial: only when is_primary = TRUE
);

-- Index for location lookups
CREATE INDEX IF NOT EXISTS idx_chef_locations_geo
ON ops.chef_locations (home_lat, home_lng);

CREATE INDEX IF NOT EXISTS idx_chef_locations_chef_id
ON ops.chef_locations (chef_id);

COMMENT ON TABLE ops.chef_locations IS 'Chef home base locations for travel time optimization';
COMMENT ON COLUMN ops.chef_locations.service_radius_miles IS 'Maximum distance chef is willing to travel (default 50 miles)';


-- ============================================================================
-- PHASE 3C: Chef assignment tracking
-- ============================================================================

CREATE TABLE IF NOT EXISTS ops.chef_assignments (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Booking reference
    booking_id UUID NOT NULL REFERENCES core.bookings(id) ON DELETE CASCADE,

    -- Chef reference
    chef_id UUID NOT NULL REFERENCES ops.chefs(id),

    -- Assignment metadata
    assigned_at TIMESTAMPTZ DEFAULT NOW(),
    assigned_by UUID REFERENCES identity.users(id),  -- Staff/admin who assigned

    -- Assignment type
    assignment_type VARCHAR(20) NOT NULL CHECK (
        assignment_type IN ('auto', 'manual', 'customer_requested')
    ),

    -- Travel info (cached from Google Maps at assignment time)
    travel_time_minutes INT,
    travel_distance_miles DECIMAL(8,2),

    -- Chain info (for multi-booking days)
    previous_booking_id UUID REFERENCES core.bookings(id),
    next_booking_id UUID REFERENCES core.bookings(id),

    -- Customer preference
    is_customer_requested BOOLEAN DEFAULT FALSE,
    customer_request_notes TEXT,

    -- Scoring (for optimization tracking)
    assignment_score DECIMAL(5,2),  -- Score from chef optimizer (0-100)

    -- Timestamps
    created_at TIMESTAMPTZ DEFAULT NOW(),

    -- One chef per booking
    UNIQUE(booking_id)
);

CREATE INDEX IF NOT EXISTS idx_chef_assignments_chef_date
ON ops.chef_assignments (chef_id, assigned_at);

CREATE INDEX IF NOT EXISTS idx_chef_assignments_booking
ON ops.chef_assignments (booking_id);

COMMENT ON TABLE ops.chef_assignments IS 'Track chef assignments to bookings with travel info and optimization scores';
COMMENT ON COLUMN ops.chef_assignments.assignment_type IS 'auto = system optimized, manual = staff override, customer_requested = specific chef requested';


-- ============================================================================
-- PHASE 8A: Booking negotiation requests
-- ============================================================================

CREATE TABLE IF NOT EXISTS core.booking_negotiations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Booking references
    existing_booking_id UUID NOT NULL REFERENCES core.bookings(id),
    new_booking_request_id UUID,  -- Pending booking that needs the slot (optional)

    -- Time change request
    original_time TIME NOT NULL,
    proposed_time TIME NOT NULL,
    shift_direction VARCHAR(10) CHECK (shift_direction IN ('earlier', 'later')),
    shift_minutes INT NOT NULL,

    -- Request details
    reason TEXT,
    incentive_offered TEXT,  -- e.g., "10% discount on your next booking"

    -- Status tracking
    status VARCHAR(20) DEFAULT 'pending' CHECK (
        status IN ('pending', 'sent', 'accepted', 'declined', 'expired', 'cancelled')
    ),

    -- Communication
    notification_method VARCHAR(20),  -- 'sms', 'email', 'both'
    notification_sent_at TIMESTAMPTZ,
    notification_message TEXT,

    -- Response
    customer_response TEXT,
    responded_at TIMESTAMPTZ,

    -- Expiration
    expires_at TIMESTAMPTZ DEFAULT (NOW() + INTERVAL '24 hours'),

    -- Audit
    created_at TIMESTAMPTZ DEFAULT NOW(),
    created_by UUID REFERENCES identity.users(id),

    -- Constraints
    CONSTRAINT valid_shift CHECK (shift_minutes > 0 AND shift_minutes <= 120)
);

CREATE INDEX IF NOT EXISTS idx_negotiations_booking
ON core.booking_negotiations (existing_booking_id, status);

CREATE INDEX IF NOT EXISTS idx_negotiations_status
ON core.booking_negotiations (status) WHERE status IN ('pending', 'sent');

COMMENT ON TABLE core.booking_negotiations IS 'Track requests to existing customers to shift their booking time for scheduling optimization';
COMMENT ON COLUMN core.booking_negotiations.incentive_offered IS 'Optional incentive offered to customer for shifting (e.g., discount, free add-on)';


-- ============================================================================
-- FUNCTION: Calculate event duration based on guest count
-- ============================================================================

CREATE OR REPLACE FUNCTION ops.calculate_event_duration(guest_count INT)
RETURNS INT AS $$
BEGIN
    -- Duration rules:
    -- 1-10 guests: 90 minutes
    -- 11-20 guests: 100 minutes
    -- 21-30 guests: 110 minutes
    -- 31+ guests: 120 minutes
    IF guest_count <= 10 THEN
        RETURN 90;
    ELSIF guest_count <= 20 THEN
        RETURN 100;
    ELSIF guest_count <= 30 THEN
        RETURN 110;
    ELSE
        RETURN 120;
    END IF;
END;
$$ LANGUAGE plpgsql IMMUTABLE;

COMMENT ON FUNCTION ops.calculate_event_duration(INT) IS 'Calculate hibachi event duration based on party size (90-120 minutes)';


-- ============================================================================
-- TRIGGER: Auto-set estimated_duration_minutes on booking insert/update
-- ============================================================================

CREATE OR REPLACE FUNCTION core.set_booking_duration()
RETURNS TRIGGER AS $$
BEGIN
    -- Calculate total guests (adults + children from party composition)
    -- Note: Adjust field names based on actual booking schema
    IF NEW.estimated_duration_minutes IS NULL THEN
        NEW.estimated_duration_minutes := ops.calculate_event_duration(
            COALESCE((NEW.party_composition->>'adults')::INT, 0) +
            COALESCE((NEW.party_composition->>'children')::INT, 0)
        );
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Only create trigger if it doesn't exist
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_trigger WHERE tgname = 'trg_set_booking_duration'
    ) THEN
        CREATE TRIGGER trg_set_booking_duration
        BEFORE INSERT OR UPDATE ON core.bookings
        FOR EACH ROW
        EXECUTE FUNCTION core.set_booking_duration();
    END IF;
END;
$$;


-- ============================================================================
-- VERIFICATION QUERIES
-- ============================================================================

-- Verify new columns added to bookings
SELECT column_name, data_type, is_nullable
FROM information_schema.columns
WHERE table_schema = 'core'
  AND table_name = 'bookings'
  AND column_name IN ('venue_lat', 'venue_lng', 'venue_address_normalized', 'estimated_duration_minutes')
ORDER BY column_name;

-- Verify new tables created
SELECT schemaname, tablename
FROM pg_tables
WHERE schemaname IN ('core', 'ops')
  AND tablename IN ('slot_configurations', 'travel_time_cache', 'chef_locations', 'chef_assignments', 'booking_negotiations')
ORDER BY schemaname, tablename;

-- Verify slot configurations inserted
SELECT slot_name, slot_time, min_event_duration, max_event_duration
FROM ops.slot_configurations
ORDER BY slot_time;
