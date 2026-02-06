-- Migration: 029_add_default_chef_availability.sql
-- Purpose: Add default chef(s) and availability records so bookings can work
-- 
-- How it works:
-- 1. Creates 1 "Virtual Chef" per active station (placeholder until real chefs assigned)
-- 2. Sets up availability for all 7 days of the week for standard slots (12PM, 3PM, 6PM, 9PM)
-- 3. When a slot is booked, it counts against the available capacity
-- 
-- The availability check logic:
-- - Counts bookings for a slot/date
-- - Counts available chefs for that day/time
-- - If bookings < available_chefs, slot is available
--
-- Run: sudo -u postgres psql -d myhibachi_production -f 029_add_default_chef_availability.sql

BEGIN;

\echo '=============================================='
\echo 'MIGRATION 029: Add Default Chef Availability'
\echo '=============================================='

-- Create day_of_week type if not exists (needed for chef_availability)
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'day_of_week') THEN
        CREATE TYPE day_of_week AS ENUM ('monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday');
    END IF;
END $$;

-- Create chef_specialty type if not exists
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'chef_specialty') THEN
        CREATE TYPE chef_specialty AS ENUM ('hibachi', 'sushi', 'teppanyaki', 'general');
    END IF;
END $$;

-- Create chef_status type if not exists
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'chef_status') THEN
        CREATE TYPE chef_status AS ENUM ('active', 'inactive', 'on_leave', 'terminated');
    END IF;
END $$;

\echo '📋 Step 1: Creating default "Virtual Chef" for each active station...'

-- Insert a default virtual chef for each active station
-- This chef represents "available capacity" 
INSERT INTO ops.chefs (
    id,
    first_name,
    last_name,
    email,
    phone,
    specialty,
    years_experience,
    status,
    is_active,
    rating,
    total_bookings,
    completed_bookings
)
SELECT 
    gen_random_uuid(),
    'Virtual Chef',
    s.code,  -- Use station code as last name for identification
    'virtual-' || s.code || '@myhibachichef.com',
    '(000) 000-0000',
    'HIBACHI'::chef_specialty,
    1,
    'ACTIVE'::chef_status,
    true,
    5.0,
    0,
    0
FROM identity.stations s
WHERE s.status = 'active'
  AND NOT EXISTS (
    SELECT 1 FROM ops.chefs c 
    WHERE c.email = 'virtual-' || s.code || '@myhibachichef.com'
  );

\echo '📋 Step 2: Creating availability records for all days and slots...'

-- Insert availability for each chef for all 7 days of week
-- Covering standard slot times: 12PM, 3PM, 6PM, 9PM (with buffer for adjustment)
WITH chef_info AS (
    SELECT id as chef_id 
    FROM ops.chefs 
    WHERE first_name = 'Virtual Chef' AND is_active = true
),
days AS (
    SELECT unnest(ARRAY['MONDAY', 'TUESDAY', 'WEDNESDAY', 'THURSDAY', 'FRIDAY', 'SATURDAY', 'SUNDAY']::day_of_week[]) as day
),
slots AS (
    -- Define time ranges that cover each slot's adjustment window (±60 min)
    SELECT '11:00:00'::time as start_time, '14:00:00'::time as end_time  -- Covers 12PM slot
    UNION ALL
    SELECT '14:00:00'::time, '17:00:00'::time  -- Covers 3PM slot  
    UNION ALL
    SELECT '17:00:00'::time, '20:00:00'::time  -- Covers 6PM slot
    UNION ALL
    SELECT '20:00:00'::time, '23:00:00'::time  -- Covers 9PM slot
)
INSERT INTO ops.chef_availability (id, chef_id, day_of_week, start_time, end_time, is_available)
SELECT 
    gen_random_uuid(),
    ci.chef_id,
    d.day,
    s.start_time,
    s.end_time,
    true
FROM chef_info ci
CROSS JOIN days d
CROSS JOIN slots s
WHERE NOT EXISTS (
    -- Don't insert duplicates
    SELECT 1 FROM ops.chef_availability ca
    WHERE ca.chef_id = ci.chef_id 
      AND ca.day_of_week = d.day 
      AND ca.start_time = s.start_time
);

\echo '📋 Step 3: Verification...'

-- Show what was created
SELECT 'Virtual Chefs Created:' as info;
SELECT id, first_name, last_name, email, status, is_active 
FROM ops.chefs 
WHERE first_name = 'Virtual Chef';

SELECT 'Availability Records Created:' as info;
SELECT 
    c.last_name as station_code,
    ca.day_of_week,
    ca.start_time,
    ca.end_time,
    ca.is_available
FROM ops.chef_availability ca
JOIN ops.chefs c ON c.id = ca.chef_id
WHERE c.first_name = 'Virtual Chef'
ORDER BY c.last_name, 
    CASE ca.day_of_week 
        WHEN 'MONDAY' THEN 1 
        WHEN 'TUESDAY' THEN 2 
        WHEN 'WEDNESDAY' THEN 3 
        WHEN 'THURSDAY' THEN 4 
        WHEN 'FRIDAY' THEN 5 
        WHEN 'SATURDAY' THEN 6 
        WHEN 'SUNDAY' THEN 7 
    END,
    ca.start_time
LIMIT 20;

SELECT 'Total availability records:' as info, COUNT(*) as count FROM ops.chef_availability;

\echo ''
\echo '=============================================='
\echo '✅ MIGRATION COMPLETE'
\echo ''
\echo 'How capacity works now:'
\echo '- 1 Virtual Chef per station = 1 booking capacity per slot'
\echo '- When a slot is booked, it counts against this chef''s availability'
\echo '- If slot has 1 booking and 1 chef available, slot becomes full'
\echo '- To increase capacity: Add more chefs OR increase long_advance_slot_capacity in SSoT'
\echo '=============================================='

COMMIT;
