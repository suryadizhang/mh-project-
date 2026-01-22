-- =====================================================
-- Migration: Seed Dynamic Variables for Staging
-- Created: 2025-01-20
-- Purpose: Populate staging database with SSoT dynamic_variables
--          to match production configuration
-- =====================================================

-- NOTE: Staging has extended schema with display_name, unit, validation_rules columns

BEGIN;

-- =====================================================
-- 1. Seed Pricing Variables
-- =====================================================

-- Adult price: $55 (5500 cents)
INSERT INTO public.dynamic_variables (category, key, value, display_name, description, is_active)
VALUES ('pricing', 'adult_price_cents', '5500', 'Adult Price (cents)', 'Adult (13+) per-person price in cents', true)
ON CONFLICT (category, key) DO UPDATE SET
    value = EXCLUDED.value,
    display_name = EXCLUDED.display_name,
    description = EXCLUDED.description,
    updated_at = NOW();

-- Child price: $30 (3000 cents)
INSERT INTO public.dynamic_variables (category, key, value, display_name, description, is_active)
VALUES ('pricing', 'child_price_cents', '3000', 'Child Price (cents)', 'Child (6-12) per-person price in cents', true)
ON CONFLICT (category, key) DO UPDATE SET
    value = EXCLUDED.value,
    display_name = EXCLUDED.display_name,
    description = EXCLUDED.description,
    updated_at = NOW();

-- Child free under age: 5
INSERT INTO public.dynamic_variables (category, key, value, display_name, description, is_active)
VALUES ('pricing', 'child_free_under_age', '5', 'Child Free Under Age', 'Children under this age eat free', true)
ON CONFLICT (category, key) DO UPDATE SET
    value = EXCLUDED.value,
    display_name = EXCLUDED.display_name,
    description = EXCLUDED.description,
    updated_at = NOW();

-- Party minimum: $550 (55000 cents)
INSERT INTO public.dynamic_variables (category, key, value, display_name, description, is_active)
VALUES ('pricing', 'party_minimum_cents', '55000', 'Party Minimum (cents)', 'Minimum party total in cents (~10 adults)', true)
ON CONFLICT (category, key) DO UPDATE SET
    value = EXCLUDED.value,
    display_name = EXCLUDED.display_name,
    description = EXCLUDED.description,
    updated_at = NOW();

-- =====================================================
-- 2. Seed Deposit Variables
-- =====================================================

-- Deposit amount: $100 (10000 cents)
INSERT INTO public.dynamic_variables (category, key, value, display_name, description, is_active)
VALUES ('deposit', 'deposit_amount_cents', '10000', 'Deposit Amount (cents)', 'Fixed deposit amount in cents', true)
ON CONFLICT (category, key) DO UPDATE SET
    value = EXCLUDED.value,
    display_name = EXCLUDED.display_name,
    description = EXCLUDED.description,
    updated_at = NOW();

-- Deposit refundable days: 4 days
INSERT INTO public.dynamic_variables (category, key, value, display_name, description, is_active)
VALUES ('deposit', 'deposit_refundable_days', '4', 'Deposit Refundable Days', 'Days before event when deposit is still refundable', true)
ON CONFLICT (category, key) DO UPDATE SET
    value = EXCLUDED.value,
    display_name = EXCLUDED.display_name,
    description = EXCLUDED.description,
    updated_at = NOW();

-- =====================================================
-- 3. Seed Travel Variables
-- =====================================================

-- Free travel miles: 30
INSERT INTO public.dynamic_variables (category, key, value, display_name, description, is_active)
VALUES ('travel', 'travel_free_miles', '30', 'Free Travel Miles', 'First X miles are free', true)
ON CONFLICT (category, key) DO UPDATE SET
    value = EXCLUDED.value,
    display_name = EXCLUDED.display_name,
    description = EXCLUDED.description,
    updated_at = NOW();

-- Per mile rate: $2 (200 cents)
INSERT INTO public.dynamic_variables (category, key, value, display_name, description, is_active)
VALUES ('travel', 'travel_per_mile_cents', '200', 'Cost Per Mile (cents)', 'Cost per mile after free miles in cents', true)
ON CONFLICT (category, key) DO UPDATE SET
    value = EXCLUDED.value,
    display_name = EXCLUDED.display_name,
    description = EXCLUDED.description,
    updated_at = NOW();

-- =====================================================
-- 4. Seed Booking Variables
-- =====================================================

-- Minimum advance hours: 48
INSERT INTO public.dynamic_variables (category, key, value, display_name, description, is_active)
VALUES ('booking', 'min_advance_hours', '48', 'Min Advance Hours', 'Minimum hours in advance to book', true)
ON CONFLICT (category, key) DO UPDATE SET
    value = EXCLUDED.value,
    display_name = EXCLUDED.display_name,
    description = EXCLUDED.description,
    updated_at = NOW();

-- =====================================================
-- 5. Grant Permissions to Application Users
-- =====================================================
-- CRITICAL: Application database users need SELECT permission to read config
-- Without this, business_config_service.py silently falls back to environment variables

-- Staging user permissions
DO $$
BEGIN
    -- Check if user exists before granting
    IF EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'myhibachi_staging_user') THEN
        EXECUTE 'GRANT SELECT, INSERT, UPDATE ON TABLE public.dynamic_variables TO myhibachi_staging_user';
        RAISE NOTICE '✅ Granted permissions to myhibachi_staging_user';
    END IF;
END $$;

-- Production user permissions (if running on production)
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'myhibachi_user') THEN
        EXECUTE 'GRANT SELECT, INSERT, UPDATE ON TABLE public.dynamic_variables TO myhibachi_user';
        RAISE NOTICE '✅ Granted permissions to myhibachi_user';
    END IF;
END $$;

-- =====================================================
-- 6. Verify the seed data
-- =====================================================
DO $$
DECLARE
    var_count INTEGER;
BEGIN
    SELECT COUNT(*) INTO var_count FROM public.dynamic_variables WHERE is_active = true;
    RAISE NOTICE '✅ Seeded % active dynamic_variables', var_count;
END $$;

COMMIT;

-- =====================================================
-- Verification Query (run after migration)
-- =====================================================
-- SELECT category, key, value, display_name FROM public.dynamic_variables ORDER BY category, key;

-- =====================================================
-- Permission Fix Applied: January 2025
-- =====================================================
-- Issue: business_config_service.py was returning source="environment"
--        instead of source="database_dynamic_variables"
-- Root Cause: Database users lacked SELECT permission on dynamic_variables
-- Solution: Added GRANT statements above to fix automatically
--
-- Manual fix if needed:
--   GRANT SELECT, INSERT, UPDATE ON TABLE public.dynamic_variables TO <db_user>;
-- =====================================================
