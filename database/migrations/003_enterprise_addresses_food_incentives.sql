-- =====================================================
-- ENTERPRISE ADDRESS SYSTEM + FOOD INCENTIVES
-- Created: 2024-12-20
-- Purpose: Enterprise-grade address management (Uber/DoorDash pattern)
--          + Food-based negotiation incentives
-- =====================================================

-- Transaction wrapper for safety
BEGIN;

-- =====================================================
-- PART A: Enterprise Addresses Table
-- Pattern: Uber/DoorDash/Lyft - Separate reusable address table
-- Benefits: Cache geocoding, customer saved addresses, reusable
-- =====================================================

CREATE TABLE IF NOT EXISTS core.addresses (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Raw input (what customer typed)
    raw_address TEXT NOT NULL,

    -- Google normalized components
    formatted_address TEXT,             -- Full Google-normalized address
    street_number VARCHAR(20),
    street_name VARCHAR(255),
    unit_number VARCHAR(50),            -- Apt, Suite, Unit
    city VARCHAR(100),
    state VARCHAR(50),
    zip_code VARCHAR(10),
    country VARCHAR(50) DEFAULT 'USA',

    -- Geocoding (from Google)
    lat DECIMAL(10,8),
    lng DECIMAL(11,8),
    google_place_id VARCHAR(255),       -- For faster future lookups
    geocode_status VARCHAR(20) DEFAULT 'pending',  -- pending, success, failed, partial
    geocoded_at TIMESTAMPTZ,
    geocode_provider VARCHAR(50) DEFAULT 'google', -- google, here, mapbox

    -- Location metadata
    timezone VARCHAR(50),               -- America/Los_Angeles
    is_residential BOOLEAN DEFAULT TRUE,
    location_type VARCHAR(50),          -- ROOFTOP, RANGE_INTERPOLATED, etc.

    -- Customer ownership (optional - for saved addresses)
    customer_id UUID REFERENCES core.customers(id) ON DELETE CASCADE,
    address_label VARCHAR(50),          -- 'Home', 'Work', 'Mom\'s House', 'Party Venue'
    is_default BOOLEAN DEFAULT FALSE,

    -- Service area check
    is_serviceable BOOLEAN DEFAULT TRUE,
    service_station_id UUID,            -- Nearest station
    distance_to_station_km DECIMAL(8,2),

    -- Audit
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Indexes for address lookups
CREATE INDEX IF NOT EXISTS idx_addresses_geocode
ON core.addresses (lat, lng)
WHERE lat IS NOT NULL;

CREATE INDEX IF NOT EXISTS idx_addresses_customer
ON core.addresses (customer_id)
WHERE customer_id IS NOT NULL;

CREATE INDEX IF NOT EXISTS idx_addresses_place_id
ON core.addresses (google_place_id)
WHERE google_place_id IS NOT NULL;

CREATE INDEX IF NOT EXISTS idx_addresses_zip
ON core.addresses (zip_code);

-- Unique constraint: same raw address + customer = one entry
CREATE UNIQUE INDEX IF NOT EXISTS idx_addresses_unique_customer
ON core.addresses (customer_id, LOWER(raw_address))
WHERE customer_id IS NOT NULL;

COMMENT ON TABLE core.addresses IS 'Enterprise address management - Uber/DoorDash pattern. Caches geocoding, enables saved customer addresses.';


-- =====================================================
-- PART B: Add address FK to bookings
-- =====================================================

DO $$
BEGIN
    -- Add venue_address_id FK to bookings
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_schema = 'core' AND table_name = 'bookings' AND column_name = 'venue_address_id'
    ) THEN
        ALTER TABLE core.bookings ADD COLUMN venue_address_id UUID REFERENCES core.addresses(id);
        RAISE NOTICE 'Added venue_address_id column to bookings';
    END IF;
END $$;

CREATE INDEX IF NOT EXISTS idx_bookings_venue_address
ON core.bookings (venue_address_id)
WHERE venue_address_id IS NOT NULL;


-- =====================================================
-- PART C: Customer Preferences for Negotiation (Option C)
-- =====================================================

DO $$
BEGIN
    -- Contact preference for shift requests
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_schema = 'core' AND table_name = 'customers' AND column_name = 'contact_preference'
    ) THEN
        ALTER TABLE core.customers ADD COLUMN contact_preference VARCHAR(20) DEFAULT 'any';
        RAISE NOTICE 'Added contact_preference column';
    END IF;

    -- Whether customer is okay with AI-assisted contact
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_schema = 'core' AND table_name = 'customers' AND column_name = 'ai_contact_ok'
    ) THEN
        ALTER TABLE core.customers ADD COLUMN ai_contact_ok BOOLEAN DEFAULT TRUE;
        RAISE NOTICE 'Added ai_contact_ok column';
    END IF;

    -- Flexibility score (0-10, calculated from history)
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_schema = 'core' AND table_name = 'customers' AND column_name = 'flexibility_score'
    ) THEN
        ALTER TABLE core.customers ADD COLUMN flexibility_score DECIMAL(3,1) DEFAULT 5.0;
        RAISE NOTICE 'Added flexibility_score column';
    END IF;

    -- Total negotiation requests received
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_schema = 'core' AND table_name = 'customers' AND column_name = 'negotiation_requests_count'
    ) THEN
        ALTER TABLE core.customers ADD COLUMN negotiation_requests_count INT DEFAULT 0;
        RAISE NOTICE 'Added negotiation_requests_count column';
    END IF;

    -- Total accepted negotiations
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_schema = 'core' AND table_name = 'customers' AND column_name = 'negotiations_accepted_count'
    ) THEN
        ALTER TABLE core.customers ADD COLUMN negotiations_accepted_count INT DEFAULT 0;
        RAISE NOTICE 'Added negotiations_accepted_count column';
    END IF;
END $$;

COMMENT ON COLUMN core.customers.contact_preference IS 'Preferred contact method: sms, phone, email, any';
COMMENT ON COLUMN core.customers.ai_contact_ok IS 'Whether customer consents to AI-assisted communication';
COMMENT ON COLUMN core.customers.flexibility_score IS 'Historical flexibility score 0-10 (higher = more flexible)';


-- =====================================================
-- PART D: Food Incentives for Negotiations
-- =====================================================

-- Create incentive types enum (cheapest first: noodles, then appetizers)
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'food_incentive_type') THEN
        CREATE TYPE food_incentive_type AS ENUM (
            'none',                 -- No incentive needed
            'free_noodles',         -- Free yakisoba noodles (CHEAPEST - $3 cost)
            'free_appetizer'        -- Free edamame OR gyoza (customer chooses)
        );
        RAISE NOTICE 'Created food_incentive_type enum';
    END IF;
END $$;

-- Incentive configuration table
CREATE TABLE IF NOT EXISTS ops.negotiation_incentives (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Shift threshold
    min_shift_minutes INT NOT NULL,     -- Minimum shift to qualify
    max_shift_minutes INT NOT NULL,     -- Maximum shift for this tier

    -- Incentive offered
    incentive_type food_incentive_type NOT NULL,
    incentive_description TEXT NOT NULL,

    -- Cost tracking
    actual_cost_usd DECIMAL(8,2) NOT NULL,      -- What it costs us
    perceived_value_usd DECIMAL(8,2) NOT NULL,  -- What customer perceives

    -- Active
    is_active BOOLEAN DEFAULT TRUE,
    priority INT DEFAULT 0,             -- Higher = offered first

    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Insert default incentive tiers (NO cash, NO protein - only noodles and appetizers)
-- Matches actual shift options: ±30 min or ±60 min
INSERT INTO ops.negotiation_incentives
    (min_shift_minutes, max_shift_minutes, incentive_type, incentive_description, actual_cost_usd, perceived_value_usd, priority)
VALUES
    -- ±30 min shift: Free yakisoba noodles for everyone (CHEAPEST option)
    (30, 30, 'free_noodles', 'Free yakisoba noodles for your entire party!', 3.00, 8.00, 1),

    -- ±60 min shift: Free appetizer - customer chooses edamame OR gyoza
    (60, 60, 'free_appetizer', 'Choose free edamame or gyoza for your party!', 5.00, 12.00, 2)
ON CONFLICT DO NOTHING;

COMMENT ON TABLE ops.negotiation_incentives IS 'Food-based incentives for time shift negotiations. No cash discounts - only food rewards.';


-- =====================================================
-- PART E: Update booking_negotiations table for food incentives
-- =====================================================

DO $$
BEGIN
    -- Change incentive column type (if exists as numeric, convert to text)
    IF EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_schema = 'core' AND table_name = 'booking_negotiations'
        AND column_name = 'incentive_offered'
    ) THEN
        -- Add new column for food incentive
        IF NOT EXISTS (
            SELECT 1 FROM information_schema.columns
            WHERE table_schema = 'core' AND table_name = 'booking_negotiations'
            AND column_name = 'food_incentive_type'
        ) THEN
            ALTER TABLE core.booking_negotiations
            ADD COLUMN food_incentive_type VARCHAR(50);
            RAISE NOTICE 'Added food_incentive_type column';
        END IF;

        -- Add description column
        IF NOT EXISTS (
            SELECT 1 FROM information_schema.columns
            WHERE table_schema = 'core' AND table_name = 'booking_negotiations'
            AND column_name = 'food_incentive_description'
        ) THEN
            ALTER TABLE core.booking_negotiations
            ADD COLUMN food_incentive_description TEXT;
            RAISE NOTICE 'Added food_incentive_description column';
        END IF;
    END IF;

    -- Add channel tracking (how was negotiation sent)
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_schema = 'core' AND table_name = 'booking_negotiations'
        AND column_name = 'contact_channel'
    ) THEN
        ALTER TABLE core.booking_negotiations
        ADD COLUMN contact_channel VARCHAR(30);
        RAISE NOTICE 'Added contact_channel column';
    END IF;

    -- Add who handled it (agent ID or 'ai' or 'auto')
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_schema = 'core' AND table_name = 'booking_negotiations'
        AND column_name = 'handled_by'
    ) THEN
        ALTER TABLE core.booking_negotiations
        ADD COLUMN handled_by VARCHAR(100);
        RAISE NOTICE 'Added handled_by column';
    END IF;

    -- Add response time tracking
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_schema = 'core' AND table_name = 'booking_negotiations'
        AND column_name = 'response_time_minutes'
    ) THEN
        ALTER TABLE core.booking_negotiations
        ADD COLUMN response_time_minutes INT;
        RAISE NOTICE 'Added response_time_minutes column';
    END IF;
END $$;

COMMENT ON COLUMN core.booking_negotiations.food_incentive_type IS 'Type of food incentive offered: free_appetizer, free_noodles, protein_upgrade, etc.';
COMMENT ON COLUMN core.booking_negotiations.contact_channel IS 'Channel used: sms, email, phone, ai_chat, live_agent';
COMMENT ON COLUMN core.booking_negotiations.handled_by IS 'Who handled: agent UUID, ''ai'', or ''auto''';


-- =====================================================
-- PART F: Helper function to get incentive for shift amount
-- =====================================================

CREATE OR REPLACE FUNCTION get_negotiation_incentive(shift_minutes INT)
RETURNS TABLE (
    incentive_type TEXT,
    incentive_description TEXT,
    actual_cost DECIMAL,
    perceived_value DECIMAL
) AS $$
BEGIN
    RETURN QUERY
    SELECT
        ni.incentive_type::TEXT,
        ni.incentive_description,
        ni.actual_cost_usd,
        ni.perceived_value_usd
    FROM ops.negotiation_incentives ni
    WHERE ni.is_active = TRUE
      AND ABS(shift_minutes) >= ni.min_shift_minutes
      AND ABS(shift_minutes) <= ni.max_shift_minutes
    ORDER BY ni.priority DESC
    LIMIT 1;
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION get_negotiation_incentive IS 'Get the appropriate food incentive for a given shift amount in minutes';


-- =====================================================
-- PART G: Function to update customer flexibility score
-- =====================================================

CREATE OR REPLACE FUNCTION update_customer_flexibility_score(
    p_customer_id UUID,
    p_accepted BOOLEAN
) RETURNS DECIMAL AS $$
DECLARE
    v_total INT;
    v_accepted INT;
    v_new_score DECIMAL(3,1);
BEGIN
    -- Update counts
    IF p_accepted THEN
        UPDATE core.customers
        SET negotiation_requests_count = negotiation_requests_count + 1,
            negotiations_accepted_count = negotiations_accepted_count + 1,
            updated_at = NOW()
        WHERE id = p_customer_id;
    ELSE
        UPDATE core.customers
        SET negotiation_requests_count = negotiation_requests_count + 1,
            updated_at = NOW()
        WHERE id = p_customer_id;
    END IF;

    -- Calculate new score
    SELECT negotiation_requests_count, negotiations_accepted_count
    INTO v_total, v_accepted
    FROM core.customers WHERE id = p_customer_id;

    IF v_total > 0 THEN
        v_new_score := ROUND((v_accepted::DECIMAL / v_total) * 10, 1);
    ELSE
        v_new_score := 5.0;  -- Default neutral score
    END IF;

    -- Update score
    UPDATE core.customers
    SET flexibility_score = v_new_score
    WHERE id = p_customer_id;

    RETURN v_new_score;
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION update_customer_flexibility_score IS 'Update customer flexibility score after a negotiation response';


-- Commit transaction
COMMIT;

-- =====================================================
-- VERIFICATION QUERIES (run after migration)
-- =====================================================
-- SELECT * FROM core.addresses LIMIT 5;
-- SELECT * FROM ops.negotiation_incentives;
-- SELECT get_negotiation_incentive(45);
-- SELECT column_name FROM information_schema.columns WHERE table_name = 'customers' AND column_name LIKE '%flex%';
