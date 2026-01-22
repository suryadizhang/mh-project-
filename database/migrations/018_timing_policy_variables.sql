-- =====================================================
-- Migration: 018_timing_policy_variables.sql
-- Created: 2025-01-30
-- Purpose: Add missing timing and policy variables to SSoT dynamic_variables table
-- Batch: 1.x (SSoT Completion)
-- =====================================================
--
-- This migration adds variables for:
-- 1. Timing deadlines (menu changes, guest count, reschedule)
-- 2. Service duration (event length, chef arrival)
-- 3. Policy rules (reschedule fees, free reschedule count)
-- 4. Contact information (business phone, email)
--
-- Related files:
-- - apps/backend/src/services/business_config_service.py
-- - apps/customer/src/hooks/usePricing.ts
-- - apps/customer/src/data/faqsData.ts (uses {{PLACEHOLDER}} syntax)
-- - .github/instructions/20-SINGLE_SOURCE_OF_TRUTH.instructions.md
--
-- =====================================================

BEGIN;

-- =====================================================
-- TIMING CATEGORY - Deadline/cutoff times
-- =====================================================

-- Menu changes not allowed within 12 hours of event (per faqsData.ts)
INSERT INTO dynamic_variables (category, key, value, display_name, description, is_active)
VALUES ('timing', 'menu_change_cutoff_hours', '12', 'Menu Change Cutoff (Hours)', 'Hours before event when menu changes are no longer allowed', true)
ON CONFLICT (category, key) DO UPDATE SET
    value = EXCLUDED.value,
    display_name = EXCLUDED.display_name,
    description = EXCLUDED.description,
    updated_at = NOW();

-- Guest count must be finalized 24 hours before event (per faqsData.ts)
INSERT INTO dynamic_variables (category, key, value, display_name, description, is_active)
VALUES ('timing', 'guest_count_finalize_hours', '24', 'Guest Count Finalize Deadline (Hours)', 'Hours before event when guest count must be finalized', true)
ON CONFLICT (category, key) DO UPDATE SET
    value = EXCLUDED.value,
    display_name = EXCLUDED.display_name,
    description = EXCLUDED.description,
    updated_at = NOW();

-- Free reschedule allowed with 24+ hours notice (per faqsData.ts)
INSERT INTO dynamic_variables (category, key, value, display_name, description, is_active)
VALUES ('timing', 'free_reschedule_hours', '24', 'Free Reschedule Notice (Hours)', 'Hours before event when free reschedule is still allowed', true)
ON CONFLICT (category, key) DO UPDATE SET
    value = EXCLUDED.value,
    display_name = EXCLUDED.display_name,
    description = EXCLUDED.description,
    updated_at = NOW();

-- =====================================================
-- SERVICE CATEGORY - Event duration and logistics
-- =====================================================

-- Standard service is 90 minutes (per BookingAgreementModal.tsx, faqsData.ts)
INSERT INTO dynamic_variables (category, key, value, display_name, description, is_active)
VALUES ('service', 'standard_duration_minutes', '90', 'Standard Service Duration (Minutes)', 'Standard hibachi service duration for typical party size', true)
ON CONFLICT (category, key) DO UPDATE SET
    value = EXCLUDED.value,
    display_name = EXCLUDED.display_name,
    description = EXCLUDED.description,
    updated_at = NOW();

-- Extended service for large parties (20+ guests) is up to 150 minutes
INSERT INTO dynamic_variables (category, key, value, display_name, description, is_active)
VALUES ('service', 'extended_duration_minutes', '150', 'Extended Service Duration (Minutes)', 'Maximum service duration for large parties (20+ guests)', true)
ON CONFLICT (category, key) DO UPDATE SET
    value = EXCLUDED.value,
    display_name = EXCLUDED.display_name,
    description = EXCLUDED.description,
    updated_at = NOW();

-- Chef arrives 15-30 minutes early for setup (per faqsData.ts)
INSERT INTO dynamic_variables (category, key, value, display_name, description, is_active)
VALUES ('service', 'chef_arrival_minutes_before', '20', 'Chef Arrival (Minutes Before)', 'How many minutes before event start the chef typically arrives', true)
ON CONFLICT (category, key) DO UPDATE SET
    value = EXCLUDED.value,
    display_name = EXCLUDED.display_name,
    description = EXCLUDED.description,
    updated_at = NOW();

-- =====================================================
-- POLICY CATEGORY - Fees and limits
-- =====================================================

-- Late reschedule fee is $200 (per faqsData.ts)
INSERT INTO dynamic_variables (category, key, value, display_name, description, is_active)
VALUES ('policy', 'reschedule_fee_cents', '20000', 'Late Reschedule Fee (Cents)', 'Fee charged for rescheduling within the free window', true)
ON CONFLICT (category, key) DO UPDATE SET
    value = EXCLUDED.value,
    display_name = EXCLUDED.display_name,
    description = EXCLUDED.description,
    updated_at = NOW();

-- One free reschedule allowed (per faqsData.ts)
INSERT INTO dynamic_variables (category, key, value, display_name, description, is_active)
VALUES ('policy', 'free_reschedule_count', '1', 'Free Reschedule Count', 'Number of free reschedules allowed per booking', true)
ON CONFLICT (category, key) DO UPDATE SET
    value = EXCLUDED.value,
    display_name = EXCLUDED.display_name,
    description = EXCLUDED.description,
    updated_at = NOW();

-- =====================================================
-- CONTACT CATEGORY - Business contact info
-- =====================================================

-- Business phone number (per faqsData.ts, contact page)
INSERT INTO dynamic_variables (category, key, value, display_name, description, is_active)
VALUES ('contact', 'business_phone', '"(916) 740-8768"', 'Business Phone Number', 'Primary customer contact phone number', true)
ON CONFLICT (category, key) DO UPDATE SET
    value = EXCLUDED.value,
    display_name = EXCLUDED.display_name,
    description = EXCLUDED.description,
    updated_at = NOW();

-- Business email (per faqsData.ts, contact page)
INSERT INTO dynamic_variables (category, key, value, display_name, description, is_active)
VALUES ('contact', 'business_email', '"cs@myhibachichef.com"', 'Business Email', 'Primary customer service email address', true)
ON CONFLICT (category, key) DO UPDATE SET
    value = EXCLUDED.value,
    display_name = EXCLUDED.display_name,
    description = EXCLUDED.description,
    updated_at = NOW();

-- =====================================================
-- Verification Query
-- =====================================================
-- Run this after migration to verify:
-- SELECT category, key, value, display_name
-- FROM dynamic_variables
-- WHERE category IN ('timing', 'service', 'policy', 'contact')
-- ORDER BY category, key;

COMMIT;

-- =====================================================
-- ROLLBACK SCRIPT (keep as comment for emergency)
-- =====================================================
-- BEGIN;
-- DELETE FROM dynamic_variables WHERE category = 'timing' AND key IN ('menu_change_cutoff_hours', 'guest_count_finalize_hours', 'free_reschedule_hours');
-- DELETE FROM dynamic_variables WHERE category = 'service' AND key IN ('standard_duration_minutes', 'extended_duration_minutes', 'chef_arrival_minutes_before');
-- DELETE FROM dynamic_variables WHERE category = 'policy' AND key IN ('reschedule_fee_cents', 'free_reschedule_count');
-- DELETE FROM dynamic_variables WHERE category = 'contact' AND key IN ('business_phone', 'business_email');
-- COMMIT;
