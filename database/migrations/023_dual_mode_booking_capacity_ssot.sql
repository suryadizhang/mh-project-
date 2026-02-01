-- =====================================================
-- Migration: Dual-Mode Booking Capacity SSoT Variables
-- Created: 2026-01-28
-- Purpose: Add SSoT variables for dual-mode availability checking
--          - chef_availability_window_days: Threshold between short/long-term (default 14)
--          - long_advance_slot_capacity: Capacity for bookings beyond the window (default 0)
-- =====================================================

BEGIN;

-- =====================================================
-- Add new SSoT variables for dual-mode booking capacity
-- =====================================================

-- Chef availability window (default 14 days)
-- Bookings within this window use actual chef availability from ChefAvailability table
-- Bookings beyond this window use long_advance_slot_capacity
INSERT INTO dynamic_variables (category, key, value, display_name, description, is_active)
VALUES (
    'booking',
    'chef_availability_window_days',
    '14',
    'Chef Availability Window (days)',
    'Number of days ahead where actual chef availability is used. Beyond this, SSoT slot capacity applies. Default 14 days (2 weeks).',
    true
)
ON CONFLICT (category, key) DO UPDATE SET
    value = EXCLUDED.value,
    display_name = EXCLUDED.display_name,
    description = EXCLUDED.description;

-- Long-advance slot capacity (default 1 = allow 1 booking per slot for advance bookings)
-- This controls how many bookings per slot are allowed for dates beyond chef_availability_window_days
-- Capacity = number of available CHEFS per slot. Chefs get assigned later when they fill availability.
INSERT INTO dynamic_variables (category, key, value, display_name, description, is_active)
VALUES (
    'booking',
    'long_advance_slot_capacity',
    '1',
    'Long-Advance Slot Capacity',
    'Number of bookings allowed per slot for dates beyond the chef availability window. Represents available chef capacity. Chefs are assigned later when they fill their availability. Admin can adjust to control advance booking volume.',
    true
)
ON CONFLICT (category, key) DO UPDATE SET
    value = EXCLUDED.value,
    display_name = EXCLUDED.display_name,
    description = EXCLUDED.description;

COMMIT;

-- =====================================================
-- Verification Query
-- =====================================================
-- Run this to verify the new variables are inserted:
-- SELECT category, key, value, display_name, description
-- FROM dynamic_variables
-- WHERE category = 'booking'
-- AND key IN ('chef_availability_window_days', 'long_advance_slot_capacity');

-- =====================================================
-- ROLLBACK (if needed)
-- =====================================================
-- DELETE FROM dynamic_variables
-- WHERE category = 'booking'
-- AND key IN ('chef_availability_window_days', 'long_advance_slot_capacity');
