-- =====================================================
-- SMART SCHEDULING SYSTEM - Phase 1 Migration
-- Created: 2024-12-20
-- Purpose: Add location fields, slot config, and chef tables
-- =====================================================

-- Transaction wrapper for safety
BEGIN;

-- =====================================================
-- PHASE 1A: Add location fields to existing bookings
-- =====================================================

-- Check if columns exist before adding (idempotent)
DO $$
BEGIN
    -- Add venue geocoding columns
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_schema = 'core' AND table_name = 'bookings' AND column_name = 'venue_lat'
    ) THEN
        ALTER TABLE core.bookings ADD COLUMN venue_lat DECIMAL(10,8);
        RAISE NOTICE 'Added venue_lat column';
    END IF;

    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_schema = 'core' AND table_name = 'bookings' AND column_name = 'venue_lng'
    ) THEN
        ALTER TABLE core.bookings ADD COLUMN venue_lng DECIMAL(11,8);
        RAISE NOTICE 'Added venue_lng column';
    END IF;

    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_schema = 'core' AND table_name = 'bookings' AND column_name = 'venue_address_normalized'
    ) THEN
        ALTER TABLE core.bookings ADD COLUMN venue_address_normalized TEXT;
        RAISE NOTICE 'Added venue_address_normalized column';
    END IF;

    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_schema = 'core' AND table_name = 'bookings' AND column_name = 'venue_geocoded_at'
    ) THEN
        ALTER TABLE core.bookings ADD COLUMN venue_geocoded_at TIMESTAMPTZ;
        RAISE NOTICE 'Added venue_geocoded_at column';
    END IF;

    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_schema = 'core' AND table_name = 'bookings' AND column_name = 'estimated_duration_minutes'
    ) THEN
        ALTER TABLE core.bookings ADD COLUMN estimated_duration_minutes INT DEFAULT 90;
        RAISE NOTICE 'Added estimated_duration_minutes column';
    END IF;

    -- Add preferred chef column
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_schema = 'core' AND table_name = 'bookings' AND column_name = 'preferred_chef_id'
    ) THEN
        ALTER TABLE core.bookings ADD COLUMN preferred_chef_id UUID;
        RAISE NOTICE 'Added preferred_chef_id column';
    END IF;

    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_schema = 'core' AND table_name = 'bookings' AND column_name = 'is_chef_requested'
    ) THEN
        ALTER TABLE core.bookings ADD COLUMN is_chef_requested BOOLEAN DEFAULT FALSE;
        RAISE NOTICE 'Added is_chef_requested column';
    END IF;
END $$;

-- Add column comments
COMMENT ON COLUMN core.bookings.venue_lat IS 'Latitude from Google Geocoding API';
COMMENT ON COLUMN core.bookings.venue_lng IS 'Longitude from Google Geocoding API';
COMMENT ON COLUMN core.bookings.venue_address_normalized IS 'Standardized address from Google Places';
COMMENT ON COLUMN core.bookings.venue_geocoded_at IS 'Timestamp when address was geocoded';
COMMENT ON COLUMN core.bookings.estimated_duration_minutes IS 'Event duration: 90-120 min based on party size';
COMMENT ON COLUMN core.bookings.preferred_chef_id IS 'Customer-requested specific chef';
COMMENT ON COLUMN core.bookings.is_chef_requested IS 'Whether customer specifically requested a chef';

-- Index for geospatial queries
CREATE INDEX IF NOT EXISTS idx_bookings_geo
ON core.bookings (venue_lat, venue_lng)
WHERE venue_lat IS NOT NULL;

-- Index for preferred chef lookups
CREATE INDEX IF NOT EXISTS idx_bookings_preferred_chef
ON core.bookings (preferred_chef_id)
WHERE preferred_chef_id IS NOT NULL;


-- =====================================================
-- PHASE 1D: Slot configuration table
-- =====================================================

CREATE TABLE IF NOT EXISTS ops.slot_configurations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    slot_name VARCHAR(20) NOT NULL UNIQUE,        -- '12PM', '3PM', '6PM', '9PM'
    slot_time TIME NOT NULL,                      -- 12:00, 15:00, 18:00, 21:00
    min_adjust_minutes INT DEFAULT -60,           -- Can start up to 60 min earlier
    max_adjust_minutes INT DEFAULT 60,            -- Can start up to 60 min later
    min_event_duration INT DEFAULT 90,            -- Minimum event length
    max_event_duration INT DEFAULT 120,           -- Maximum event length
    buffer_before_minutes INT DEFAULT 30,         -- Travel/setup buffer before event
    buffer_after_minutes INT DEFAULT 15,          -- Cleanup buffer after event
    max_bookings_per_slot INT DEFAULT 10,         -- Per slot across all chefs
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

COMMENT ON TABLE ops.slot_configurations IS 'Configuration for booking time slots with flexibility rules';

-- Insert default slots if not exist
INSERT INTO ops.slot_configurations
    (slot_name, slot_time, min_event_duration, max_event_duration)
VALUES
    ('12PM', '12:00:00', 90, 120),
    ('3PM', '15:00:00', 90, 120),
    ('6PM', '18:00:00', 90, 120),
    ('9PM', '21:00:00', 90, 120)
ON CONFLICT (slot_name) DO NOTHING;


-- =====================================================
-- PHASE 3A: Chef locations table
-- =====================================================

CREATE TABLE IF NOT EXISTS ops.chef_locations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    chef_id UUID NOT NULL REFERENCES ops.chefs(id) ON DELETE CASCADE,
    home_address_encrypted BYTEA,                 -- Encrypted for PII protection
    home_address_hint VARCHAR(100),               -- Non-sensitive hint (e.g., "Downtown LA")
    home_lat DECIMAL(10,8) NOT NULL,
    home_lng DECIMAL(11,8) NOT NULL,
    service_radius_km DECIMAL(5,2) DEFAULT 50.0,  -- Max travel distance
    is_primary BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

COMMENT ON TABLE ops.chef_locations IS 'Chef home/base locations for travel time optimization';

-- Unique constraint: one primary location per chef
CREATE UNIQUE INDEX IF NOT EXISTS idx_chef_locations_primary
ON ops.chef_locations (chef_id)
WHERE is_primary = TRUE;

-- Index for location lookups
CREATE INDEX IF NOT EXISTS idx_chef_locations_geo
ON ops.chef_locations (home_lat, home_lng);


-- =====================================================
-- PHASE 3C: Chef assignment tracking
-- =====================================================

-- Create assignment type enum if not exists
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'chef_assignment_type') THEN
        CREATE TYPE ops.chef_assignment_type AS ENUM (
            'auto',              -- System assigned
            'manual',            -- Staff/admin assigned
            'customer_requested' -- Customer specifically requested
        );
    END IF;
END $$;

CREATE TABLE IF NOT EXISTS ops.chef_assignments (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    booking_id UUID NOT NULL REFERENCES core.bookings(id) ON DELETE CASCADE,
    chef_id UUID NOT NULL REFERENCES ops.chefs(id),
    assigned_at TIMESTAMPTZ DEFAULT NOW(),
    assigned_by UUID REFERENCES identity.users(id),
    assignment_type VARCHAR(20) NOT NULL DEFAULT 'manual',
    travel_time_minutes INT,                      -- Calculated travel time
    travel_distance_km DECIMAL(8,2),              -- Calculated distance
    previous_booking_id UUID REFERENCES core.bookings(id), -- For travel chain tracking
    is_customer_requested BOOLEAN DEFAULT FALSE,
    customer_request_notes TEXT,
    efficiency_score DECIMAL(5,2),                -- 0-100 score
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),

    CONSTRAINT chk_assignment_type CHECK (
        assignment_type IN ('auto', 'manual', 'customer_requested')
    )
);

COMMENT ON TABLE ops.chef_assignments IS 'Tracks chef-to-booking assignments with travel optimization data';

-- One chef per booking
CREATE UNIQUE INDEX IF NOT EXISTS idx_chef_assignments_booking
ON ops.chef_assignments (booking_id);

-- Chef schedule lookup
CREATE INDEX IF NOT EXISTS idx_chef_assignments_chef_date
ON ops.chef_assignments (chef_id, assigned_at);


-- =====================================================
-- PHASE 4B: Travel time cache (Google Maps results)
-- =====================================================

CREATE TABLE IF NOT EXISTS ops.travel_time_cache (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    origin_lat DECIMAL(10,8) NOT NULL,
    origin_lng DECIMAL(11,8) NOT NULL,
    dest_lat DECIMAL(10,8) NOT NULL,
    dest_lng DECIMAL(11,8) NOT NULL,
    departure_hour INT NOT NULL CHECK (departure_hour BETWEEN 0 AND 23),
    day_of_week INT NOT NULL CHECK (day_of_week BETWEEN 0 AND 6),
    is_rush_hour BOOLEAN DEFAULT FALSE,
    base_duration_minutes INT NOT NULL,           -- Without traffic
    traffic_duration_minutes INT,                 -- With traffic
    distance_km DECIMAL(8,2) NOT NULL,
    google_polyline TEXT,                         -- Route for visualization
    cached_at TIMESTAMPTZ DEFAULT NOW(),
    expires_at TIMESTAMPTZ DEFAULT (NOW() + INTERVAL '24 hours')
);

COMMENT ON TABLE ops.travel_time_cache IS 'Cached Google Maps travel time results (24h TTL)';

-- Unique constraint for cache lookups (rounded to 3 decimal places ~110m precision)
CREATE UNIQUE INDEX IF NOT EXISTS idx_travel_cache_lookup
ON ops.travel_time_cache (
    ROUND(origin_lat::numeric, 3),
    ROUND(origin_lng::numeric, 3),
    ROUND(dest_lat::numeric, 3),
    ROUND(dest_lng::numeric, 3),
    departure_hour,
    day_of_week
);

-- Auto-cleanup expired cache entries
CREATE INDEX IF NOT EXISTS idx_travel_cache_expires
ON ops.travel_time_cache (expires_at);


-- =====================================================
-- PHASE 8A: Booking negotiation requests
-- =====================================================

-- Create negotiation status enum if not exists
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'negotiation_status') THEN
        CREATE TYPE core.negotiation_status AS ENUM (
            'pending',   -- Created, not yet sent
            'sent',      -- Notification sent to customer
            'accepted',  -- Customer agreed to shift
            'declined',  -- Customer declined
            'expired'    -- No response within timeframe
        );
    END IF;
END $$;

CREATE TABLE IF NOT EXISTS core.booking_negotiations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    existing_booking_id UUID NOT NULL REFERENCES core.bookings(id),
    new_booking_request_id UUID,                  -- Pending booking that needs the slot
    original_time TIME NOT NULL,
    proposed_time TIME NOT NULL,
    shift_direction VARCHAR(10) CHECK (shift_direction IN ('earlier', 'later')),
    shift_minutes INT NOT NULL,
    reason TEXT,                                  -- Explanation for customer
    incentive_offered TEXT,                       -- Optional: discount, gift, etc.
    status VARCHAR(20) DEFAULT 'pending',
    notification_method VARCHAR(20),              -- 'sms', 'email', 'both'
    notification_sent_at TIMESTAMPTZ,
    customer_response TEXT,
    responded_at TIMESTAMPTZ,
    expires_at TIMESTAMPTZ DEFAULT (NOW() + INTERVAL '24 hours'),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    created_by UUID REFERENCES identity.users(id),

    CONSTRAINT chk_negotiation_status CHECK (
        status IN ('pending', 'sent', 'accepted', 'declined', 'expired')
    )
);

COMMENT ON TABLE core.booking_negotiations IS 'Tracks requests to shift existing bookings for new customers';

CREATE INDEX IF NOT EXISTS idx_negotiations_booking
ON core.booking_negotiations (existing_booking_id, status);

CREATE INDEX IF NOT EXISTS idx_negotiations_pending
ON core.booking_negotiations (status, expires_at)
WHERE status IN ('pending', 'sent');


-- =====================================================
-- AUDIT TRAIL: Add trigger for assignment changes
-- =====================================================

-- Function to log chef assignment changes
CREATE OR REPLACE FUNCTION ops.log_chef_assignment_change()
RETURNS TRIGGER AS $$
BEGIN
    INSERT INTO audit.audit_log (
        table_name,
        record_id,
        action,
        old_values,
        new_values,
        changed_by
    ) VALUES (
        'chef_assignments',
        COALESCE(NEW.id, OLD.id),
        TG_OP,
        CASE WHEN TG_OP = 'DELETE' THEN to_jsonb(OLD) ELSE NULL END,
        CASE WHEN TG_OP != 'DELETE' THEN to_jsonb(NEW) ELSE NULL END,
        COALESCE(NEW.assigned_by, OLD.assigned_by)
    );
    RETURN COALESCE(NEW, OLD);
END;
$$ LANGUAGE plpgsql;

-- Apply trigger (drop first if exists)
DROP TRIGGER IF EXISTS trg_chef_assignment_audit ON ops.chef_assignments;
CREATE TRIGGER trg_chef_assignment_audit
AFTER INSERT OR UPDATE OR DELETE ON ops.chef_assignments
FOR EACH ROW EXECUTE FUNCTION ops.log_chef_assignment_change();


-- =====================================================
-- HELPER FUNCTION: Calculate event duration from guest count
-- =====================================================

CREATE OR REPLACE FUNCTION core.calculate_event_duration(guest_count INT)
RETURNS INT AS $$
BEGIN
    -- Duration based on party size:
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

COMMENT ON FUNCTION core.calculate_event_duration IS 'Calculate event duration (90-120 min) based on guest count';


-- =====================================================
-- HELPER FUNCTION: Check if time is rush hour
-- =====================================================

CREATE OR REPLACE FUNCTION ops.is_rush_hour(check_time TIMESTAMPTZ)
RETURNS BOOLEAN AS $$
DECLARE
    hour_of_day INT;
    day_of_week INT;
BEGIN
    hour_of_day := EXTRACT(HOUR FROM check_time);
    day_of_week := EXTRACT(DOW FROM check_time); -- 0=Sun, 6=Sat

    -- Rush hour: Mon-Fri (1-5), 3PM-7PM (15:00-19:00)
    RETURN day_of_week BETWEEN 1 AND 5
       AND hour_of_day BETWEEN 15 AND 18;
END;
$$ LANGUAGE plpgsql IMMUTABLE;

COMMENT ON FUNCTION ops.is_rush_hour IS 'Returns TRUE if time is weekday rush hour (Mon-Fri 3-7PM)';


-- =====================================================
-- HELPER FUNCTION: Get traffic multiplier
-- =====================================================

CREATE OR REPLACE FUNCTION ops.get_traffic_multiplier(check_time TIMESTAMPTZ)
RETURNS DECIMAL AS $$
BEGIN
    IF ops.is_rush_hour(check_time) THEN
        RETURN 1.5;  -- 50% longer during rush hour
    ELSE
        RETURN 1.0;
    END IF;
END;
$$ LANGUAGE plpgsql IMMUTABLE;

COMMENT ON FUNCTION ops.get_traffic_multiplier IS 'Returns 1.5 for rush hour, 1.0 otherwise';


-- =====================================================
-- TRIGGER: Auto-calculate event duration on booking insert/update
-- =====================================================

CREATE OR REPLACE FUNCTION core.auto_calculate_duration()
RETURNS TRIGGER AS $$
BEGIN
    -- Only calculate if not manually set or if guest count changed
    IF NEW.estimated_duration_minutes IS NULL OR
       (OLD IS NOT NULL AND OLD.guest_count != NEW.guest_count) THEN
        NEW.estimated_duration_minutes := core.calculate_event_duration(NEW.guest_count);
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trg_auto_duration ON core.bookings;
CREATE TRIGGER trg_auto_duration
BEFORE INSERT OR UPDATE ON core.bookings
FOR EACH ROW EXECUTE FUNCTION core.auto_calculate_duration();


-- =====================================================
-- VERIFY MIGRATION
-- =====================================================

DO $$
DECLARE
    col_count INT;
    table_count INT;
BEGIN
    -- Check booking columns
    SELECT COUNT(*) INTO col_count
    FROM information_schema.columns
    WHERE table_schema = 'core'
      AND table_name = 'bookings'
      AND column_name IN ('venue_lat', 'venue_lng', 'estimated_duration_minutes', 'preferred_chef_id');

    IF col_count >= 4 THEN
        RAISE NOTICE '✅ Booking location columns added successfully';
    ELSE
        RAISE WARNING '⚠️ Some booking columns missing';
    END IF;

    -- Check new tables
    SELECT COUNT(*) INTO table_count
    FROM information_schema.tables
    WHERE table_schema IN ('ops', 'core')
      AND table_name IN ('slot_configurations', 'chef_locations', 'chef_assignments', 'travel_time_cache', 'booking_negotiations');

    RAISE NOTICE '✅ Created % new tables', table_count;

    -- Check slot configurations
    SELECT COUNT(*) INTO col_count FROM ops.slot_configurations;
    RAISE NOTICE '✅ Slot configurations: % records', col_count;
END $$;

COMMIT;

-- =====================================================
-- ROLLBACK SCRIPT (if needed)
-- =====================================================
-- To rollback, run:
/*
BEGIN;

-- Drop tables in reverse order
DROP TABLE IF EXISTS core.booking_negotiations CASCADE;
DROP TABLE IF EXISTS ops.travel_time_cache CASCADE;
DROP TABLE IF EXISTS ops.chef_assignments CASCADE;
DROP TABLE IF EXISTS ops.chef_locations CASCADE;
DROP TABLE IF EXISTS ops.slot_configurations CASCADE;

-- Drop functions
DROP FUNCTION IF EXISTS core.calculate_event_duration CASCADE;
DROP FUNCTION IF EXISTS ops.is_rush_hour CASCADE;
DROP FUNCTION IF EXISTS ops.get_traffic_multiplier CASCADE;
DROP FUNCTION IF EXISTS core.auto_calculate_duration CASCADE;
DROP FUNCTION IF EXISTS ops.log_chef_assignment_change CASCADE;

-- Drop booking columns
ALTER TABLE core.bookings
    DROP COLUMN IF EXISTS venue_lat,
    DROP COLUMN IF EXISTS venue_lng,
    DROP COLUMN IF EXISTS venue_address_normalized,
    DROP COLUMN IF EXISTS venue_geocoded_at,
    DROP COLUMN IF EXISTS estimated_duration_minutes,
    DROP COLUMN IF EXISTS preferred_chef_id,
    DROP COLUMN IF EXISTS is_chef_requested;

-- Drop enums
DROP TYPE IF EXISTS ops.chef_assignment_type CASCADE;
DROP TYPE IF EXISTS core.negotiation_status CASCADE;

COMMIT;
*/
