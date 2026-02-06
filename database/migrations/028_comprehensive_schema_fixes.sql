-- Migration: 028_comprehensive_schema_fixes.sql
-- Description: Comprehensive fixes for schema/permission issues discovered 2026-02-05
-- Applied: Production 2026-02-05
--
-- Issues Found & Fixed:
-- 1. Missing permissions on 5 core tables
-- 2. Missing booking columns (customer_requested_time, booking_datetime, party_toddlers, urgency fields)
-- 3. Station missing geocoding data (CA-FREMONT-001)

-- ============================================================================
-- PART 1: Fix Missing Table Permissions for myhibachi_user
-- ============================================================================
-- These tables were created after initial setup and didn't inherit proper grants

GRANT SELECT, INSERT, UPDATE, DELETE ON core.booking_negotiations TO myhibachi_user;
GRANT SELECT, INSERT, UPDATE, DELETE ON core.refunds TO myhibachi_user;
GRANT SELECT, INSERT, UPDATE, DELETE ON core.stripe_payments TO myhibachi_user;
GRANT SELECT, INSERT, UPDATE, DELETE ON core.travel_fee_configurations TO myhibachi_user;
GRANT SELECT, INSERT, UPDATE, DELETE ON core.webhook_events TO myhibachi_user;
GRANT SELECT, INSERT, UPDATE, DELETE ON core.addresses TO myhibachi_user;

-- Grant on all sequences to prevent INSERT failures
GRANT USAGE ON ALL SEQUENCES IN SCHEMA core TO myhibachi_user;
GRANT USAGE ON ALL SEQUENCES IN SCHEMA identity TO myhibachi_user;
GRANT USAGE ON ALL SEQUENCES IN SCHEMA audit TO myhibachi_user;
GRANT USAGE ON ALL SEQUENCES IN SCHEMA communications TO myhibachi_user;

-- Set default privileges for future tables (prevent recurrence)
ALTER DEFAULT PRIVILEGES IN SCHEMA core GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO myhibachi_user;
ALTER DEFAULT PRIVILEGES IN SCHEMA identity GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO myhibachi_user;
ALTER DEFAULT PRIVILEGES IN SCHEMA audit GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO myhibachi_user;
ALTER DEFAULT PRIVILEGES IN SCHEMA communications GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO myhibachi_user;

ALTER DEFAULT PRIVILEGES IN SCHEMA core GRANT USAGE ON SEQUENCES TO myhibachi_user;
ALTER DEFAULT PRIVILEGES IN SCHEMA identity GRANT USAGE ON SEQUENCES TO myhibachi_user;

-- ============================================================================
-- PART 2: Add Missing Booking Columns
-- ============================================================================
-- SQLAlchemy model had columns that didn't exist in production database

-- Time handling
ALTER TABLE core.bookings ADD COLUMN IF NOT EXISTS customer_requested_time TIME;
ALTER TABLE core.bookings ADD COLUMN IF NOT EXISTS booking_datetime TIMESTAMPTZ;

-- Party composition
ALTER TABLE core.bookings ADD COLUMN IF NOT EXISTS party_toddlers INTEGER DEFAULT 0;

-- Urgency tracking
ALTER TABLE core.bookings ADD COLUMN IF NOT EXISTS is_urgent BOOLEAN DEFAULT FALSE;
ALTER TABLE core.bookings ADD COLUMN IF NOT EXISTS days_until_event INTEGER;
ALTER TABLE core.bookings ADD COLUMN IF NOT EXISTS booking_window VARCHAR(50);
ALTER TABLE core.bookings ADD COLUMN IF NOT EXISTS urgency_alert_sent_at TIMESTAMPTZ;
ALTER TABLE core.bookings ADD COLUMN IF NOT EXISTS urgency_alert_count INTEGER DEFAULT 0;
ALTER TABLE core.bookings ADD COLUMN IF NOT EXISTS urgency_escalated_at TIMESTAMPTZ;

-- ============================================================================
-- PART 3: Fix Station Geocoding
-- ============================================================================
-- Station existed but was missing geocoding coordinates

UPDATE identity.stations
SET
    lat = 37.48306910,
    lng = -121.91847240,
    geocode_status = 'success',
    geocoded_at = CURRENT_TIMESTAMP
WHERE code = 'CA-FREMONT-001'
  AND (lat IS NULL OR lng IS NULL);

-- ============================================================================
-- VERIFICATION QUERIES (run manually to verify)
-- ============================================================================
--
-- Check permissions:
-- SELECT schemaname || '.' || tablename AS table_name,
--        has_table_privilege('myhibachi_user', schemaname || '.' || tablename, 'SELECT') AS can_select
-- FROM pg_tables WHERE schemaname IN ('core', 'identity', 'audit', 'communications');
--
-- Check booking columns:
-- SELECT column_name FROM information_schema.columns
-- WHERE table_schema = 'core' AND table_name = 'bookings' ORDER BY column_name;
--
-- Check station geocoding:
-- SELECT code, name, lat, lng, geocode_status FROM identity.stations;
