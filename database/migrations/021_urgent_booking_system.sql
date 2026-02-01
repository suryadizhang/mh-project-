-- =====================================================
-- Migration: 021_urgent_booking_system.sql
-- Created: 2026-01-22
-- Purpose: Urgent Booking System with Chef Assignment Alerts
--
-- Features:
--   1. is_urgent flag for bookings within 7 days of event
--   2. days_until_event calculated using venue timezone
--   3. Chef assignment alert tracking
--   4. 365-day maximum advance booking
--
-- Related:
--   - services/scheduling/urgent_booking_service.py
--   - workers/chef_assignment_alerts.py
--   - 20-SINGLE_SOURCE_OF_TRUTH.instructions.md
-- =====================================================

BEGIN;

-- =====================================================
-- SECTION 1: Add Urgent Booking Columns to core.bookings
-- =====================================================

-- Add is_urgent flag (TRUE if event within 7 days AND no chef assigned)
ALTER TABLE core.bookings ADD COLUMN IF NOT EXISTS
    is_urgent BOOLEAN NOT NULL DEFAULT FALSE;

COMMENT ON COLUMN core.bookings.is_urgent IS
    'TRUE when event is within 7 days AND chef_id IS NULL. Updated daily by urgency job.';

-- Add days_until_event (calculated using venue timezone)
ALTER TABLE core.bookings ADD COLUMN IF NOT EXISTS
    days_until_event INTEGER;

COMMENT ON COLUMN core.bookings.days_until_event IS
    'Days until event date from current date in venue timezone. NULL for completed/cancelled. Updated daily.';

-- Add booking_window classification
ALTER TABLE core.bookings ADD COLUMN IF NOT EXISTS
    booking_window VARCHAR(20) DEFAULT 'standard';

COMMENT ON COLUMN core.bookings.booking_window IS
    'Booking lead time category: urgent (0-7d), standard (8-30d), advance (31-90d), long_term (91-365d)';

-- Add urgency alert tracking (for FAILPROOF chef assignment)
ALTER TABLE core.bookings ADD COLUMN IF NOT EXISTS
    urgency_alert_sent_at TIMESTAMPTZ;

COMMENT ON COLUMN core.bookings.urgency_alert_sent_at IS
    'Timestamp when first urgency alert was sent (chef needed for booking within 7 days)';

ALTER TABLE core.bookings ADD COLUMN IF NOT EXISTS
    urgency_alert_count INTEGER DEFAULT 0;

COMMENT ON COLUMN core.bookings.urgency_alert_count IS
    'Number of urgency alerts sent for this booking. Escalates after 3 alerts.';

ALTER TABLE core.bookings ADD COLUMN IF NOT EXISTS
    urgency_escalated_at TIMESTAMPTZ;

COMMENT ON COLUMN core.bookings.urgency_escalated_at IS
    'Timestamp when booking was escalated to Super Admin (after 3 unanswered alerts)';

-- =====================================================
-- SECTION 2: Add Dynamic Variables for Booking Limits
-- =====================================================

-- Max advance booking days (365 days = 1 year)
INSERT INTO dynamic_variables (category, key, value, display_name, description, is_active)
VALUES
    ('booking', 'max_advance_days', '365', 'Max Advance Booking Days',
     'Maximum number of days in advance a customer can book. Default: 365 (1 year)', TRUE)
ON CONFLICT (category, key) DO UPDATE SET value = EXCLUDED.value, display_name = EXCLUDED.display_name, description = EXCLUDED.description;

-- Urgent window threshold (7 days)
INSERT INTO dynamic_variables (category, key, value, display_name, description, is_active)
VALUES
    ('booking', 'urgent_window_days', '7', 'Urgent Booking Window (Days)',
     'Bookings within this many days of event date are marked urgent if no chef assigned. Default: 7', TRUE)
ON CONFLICT (category, key) DO UPDATE SET value = EXCLUDED.value, display_name = EXCLUDED.display_name, description = EXCLUDED.description;

-- Standard window threshold (8-30 days)
INSERT INTO dynamic_variables (category, key, value, display_name, description, is_active)
VALUES
    ('booking', 'standard_window_days', '30', 'Standard Booking Window (Days)',
     'Bookings 8-30 days ahead are standard window. Default: 30', TRUE)
ON CONFLICT (category, key) DO UPDATE SET value = EXCLUDED.value, display_name = EXCLUDED.display_name, description = EXCLUDED.description;

-- Advance window threshold (31-90 days)
INSERT INTO dynamic_variables (category, key, value, display_name, description, is_active)
VALUES
    ('booking', 'advance_window_days', '90', 'Advance Booking Window (Days)',
     'Bookings 31-90 days ahead are advance window. Default: 90', TRUE)
ON CONFLICT (category, key) DO UPDATE SET value = EXCLUDED.value, display_name = EXCLUDED.display_name, description = EXCLUDED.description;

-- =====================================================
-- SECTION 3: Chef Assignment Alert Configuration
-- =====================================================

-- Alert intervals (in hours)
INSERT INTO dynamic_variables (category, key, value, display_name, description, is_active)
VALUES
    ('alerts', 'chef_assignment_alert_interval_hours', '4', 'Chef Assignment Alert Interval (Hours)',
     'Hours between chef assignment reminder alerts. Default: 4 hours', TRUE)
ON CONFLICT (category, key) DO UPDATE SET value = EXCLUDED.value, display_name = EXCLUDED.display_name, description = EXCLUDED.description;

-- Max alerts before escalation
INSERT INTO dynamic_variables (category, key, value, display_name, description, is_active)
VALUES
    ('alerts', 'chef_assignment_max_alerts', '3', 'Max Alerts Before Escalation',
     'Maximum alerts to Station Manager before escalating to Super Admin. Default: 3', TRUE)
ON CONFLICT (category, key) DO UPDATE SET value = EXCLUDED.value, display_name = EXCLUDED.display_name, description = EXCLUDED.description;

-- Critical threshold (days before event when alerts become critical)
INSERT INTO dynamic_variables (category, key, value, display_name, description, is_active)
VALUES
    ('alerts', 'chef_assignment_critical_days', '3', 'Critical Alert Days',
     'Days before event when chef assignment becomes CRITICAL priority. Default: 3 days', TRUE)
ON CONFLICT (category, key) DO UPDATE SET value = EXCLUDED.value, display_name = EXCLUDED.display_name, description = EXCLUDED.description;

-- =====================================================
-- SECTION 4: Chef Assignment Audit Log Table
-- =====================================================

CREATE TABLE IF NOT EXISTS ops.chef_assignment_alerts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Booking reference
    booking_id UUID NOT NULL REFERENCES core.bookings(id) ON DELETE CASCADE,

    -- Alert details
    alert_type VARCHAR(20) NOT NULL, -- 'reminder', 'urgent', 'critical', 'escalation'
    alert_level INTEGER NOT NULL DEFAULT 1, -- 1, 2, 3 (escalation)

    -- Recipients
    sent_to_user_id UUID REFERENCES identity.users(id),
    sent_to_email VARCHAR(255),
    sent_to_phone VARCHAR(20),

    -- Delivery tracking
    email_sent_at TIMESTAMPTZ,
    sms_sent_at TIMESTAMPTZ,
    email_delivered BOOLEAN DEFAULT FALSE,
    sms_delivered BOOLEAN DEFAULT FALSE,

    -- Booking context at time of alert
    days_until_event INTEGER,
    event_date DATE NOT NULL,
    event_slot TIME NOT NULL,
    station_id UUID NOT NULL,

    -- Response tracking
    acknowledged_at TIMESTAMPTZ,
    acknowledged_by UUID REFERENCES identity.users(id),
    chef_assigned_after_alert BOOLEAN DEFAULT FALSE,

    -- Metadata
    alert_metadata JSONB,
    error_message TEXT,

    -- Timestamps
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    -- Indexes for performance
    CONSTRAINT fk_alert_booking FOREIGN KEY (booking_id) REFERENCES core.bookings(id)
);

CREATE INDEX IF NOT EXISTS idx_chef_assignment_alerts_booking
    ON ops.chef_assignment_alerts(booking_id);
CREATE INDEX IF NOT EXISTS idx_chef_assignment_alerts_station
    ON ops.chef_assignment_alerts(station_id);
CREATE INDEX IF NOT EXISTS idx_chef_assignment_alerts_date
    ON ops.chef_assignment_alerts(event_date);
CREATE INDEX IF NOT EXISTS idx_chef_assignment_alerts_unacked
    ON ops.chef_assignment_alerts(acknowledged_at) WHERE acknowledged_at IS NULL;

COMMENT ON TABLE ops.chef_assignment_alerts IS
    'FAILPROOF audit trail of all chef assignment alerts. Every alert is logged for compliance and debugging.';

-- =====================================================
-- SECTION 5: Indexes for Urgent Booking Queries
-- =====================================================

-- Index for urgent bookings (fast dashboard queries)
CREATE INDEX IF NOT EXISTS idx_bookings_urgent
    ON core.bookings(is_urgent)
    WHERE is_urgent = TRUE AND deleted_at IS NULL;

-- Index for chef assignment needed
CREATE INDEX IF NOT EXISTS idx_bookings_needs_chef
    ON core.bookings(chef_id, date, status)
    WHERE chef_id IS NULL AND deleted_at IS NULL AND status NOT IN ('cancelled', 'completed', 'no_show');

-- Index for days until event queries
CREATE INDEX IF NOT EXISTS idx_bookings_days_until
    ON core.bookings(days_until_event, is_urgent)
    WHERE deleted_at IS NULL AND status NOT IN ('cancelled', 'completed', 'no_show');

-- Index for booking window filtering
CREATE INDEX IF NOT EXISTS idx_bookings_window
    ON core.bookings(booking_window, station_id)
    WHERE deleted_at IS NULL;

-- =====================================================
-- SECTION 6: Stored Function to Update Urgency
-- (Optional: Can be triggered by cron job instead)
-- =====================================================

CREATE OR REPLACE FUNCTION update_booking_urgency()
RETURNS void AS $$
DECLARE
    urgent_window_days INTEGER := 7;
    booking_rec RECORD;
BEGIN
    -- Get urgent window from dynamic_variables if exists
    SELECT value::INTEGER INTO urgent_window_days
    FROM dynamic_variables
    WHERE category = 'booking' AND key = 'urgent_window_days' AND is_active = TRUE;

    -- Update all active bookings
    FOR booking_rec IN
        SELECT b.id, b.date, s.timezone
        FROM core.bookings b
        JOIN identity.stations s ON b.station_id = s.id
        WHERE b.deleted_at IS NULL
        AND b.status NOT IN ('cancelled', 'completed', 'no_show')
    LOOP
        -- Calculate days until event using station timezone
        UPDATE core.bookings
        SET
            days_until_event = booking_rec.date - (NOW() AT TIME ZONE COALESCE(booking_rec.timezone, 'America/Los_Angeles'))::DATE,
            is_urgent = (
                booking_rec.date - (NOW() AT TIME ZONE COALESCE(booking_rec.timezone, 'America/Los_Angeles'))::DATE <= urgent_window_days
                AND chef_id IS NULL
            ),
            booking_window = CASE
                WHEN booking_rec.date - (NOW() AT TIME ZONE COALESCE(booking_rec.timezone, 'America/Los_Angeles'))::DATE <= 7 THEN 'urgent'
                WHEN booking_rec.date - (NOW() AT TIME ZONE COALESCE(booking_rec.timezone, 'America/Los_Angeles'))::DATE <= 30 THEN 'standard'
                WHEN booking_rec.date - (NOW() AT TIME ZONE COALESCE(booking_rec.timezone, 'America/Los_Angeles'))::DATE <= 90 THEN 'advance'
                ELSE 'long_term'
            END,
            updated_at = NOW()
        WHERE id = booking_rec.id;
    END LOOP;

    RAISE NOTICE 'Updated urgency for all active bookings using station timezones';
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION update_booking_urgency() IS
    'Updates is_urgent, days_until_event, and booking_window for all active bookings using venue timezone. Run daily at midnight.';

-- =====================================================
-- SECTION 7: Initial Data Update (Run Once)
-- =====================================================

-- Set initial values for existing bookings
UPDATE core.bookings b
SET
    days_until_event = b.date - CURRENT_DATE,
    is_urgent = (
        b.date - CURRENT_DATE <= 7
        AND b.chef_id IS NULL
    ),
    booking_window = CASE
        WHEN b.date - CURRENT_DATE <= 7 THEN 'urgent'
        WHEN b.date - CURRENT_DATE <= 30 THEN 'standard'
        WHEN b.date - CURRENT_DATE <= 90 THEN 'advance'
        ELSE 'long_term'
    END
WHERE b.deleted_at IS NULL
AND b.status NOT IN ('cancelled', 'completed', 'no_show');

-- =====================================================
-- SECTION 8: Verification Queries (For Manual Testing)
-- =====================================================

-- Uncomment to verify after running migration:
-- SELECT COUNT(*) as total_urgent FROM core.bookings WHERE is_urgent = TRUE;
-- SELECT booking_window, COUNT(*) FROM core.bookings WHERE deleted_at IS NULL GROUP BY booking_window;
-- SELECT * FROM dynamic_variables WHERE category IN ('booking', 'alerts') ORDER BY category, key;

COMMIT;

-- =====================================================
-- ROLLBACK SCRIPT (Keep as comment for emergency)
-- =====================================================
/*
BEGIN;

-- Remove columns
ALTER TABLE core.bookings DROP COLUMN IF EXISTS is_urgent;
ALTER TABLE core.bookings DROP COLUMN IF EXISTS days_until_event;
ALTER TABLE core.bookings DROP COLUMN IF EXISTS booking_window;
ALTER TABLE core.bookings DROP COLUMN IF EXISTS urgency_alert_sent_at;
ALTER TABLE core.bookings DROP COLUMN IF EXISTS urgency_alert_count;
ALTER TABLE core.bookings DROP COLUMN IF EXISTS urgency_escalated_at;

-- Remove function
DROP FUNCTION IF EXISTS update_booking_urgency();

-- Remove alerts table
DROP TABLE IF EXISTS ops.chef_assignment_alerts;

-- Remove dynamic variables
DELETE FROM dynamic_variables WHERE category = 'booking' AND key IN ('max_advance_days', 'urgent_window_days', 'standard_window_days', 'advance_window_days');
DELETE FROM dynamic_variables WHERE category = 'alerts' AND key LIKE 'chef_assignment_%';

-- Remove indexes
DROP INDEX IF EXISTS core.idx_bookings_urgent;
DROP INDEX IF EXISTS core.idx_bookings_needs_chef;
DROP INDEX IF EXISTS core.idx_bookings_days_until;
DROP INDEX IF EXISTS core.idx_bookings_window;

COMMIT;
*/
