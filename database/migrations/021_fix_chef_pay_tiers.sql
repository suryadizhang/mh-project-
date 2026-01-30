-- =====================================================
-- Migration: Fix Chef Pay Tiers
-- Created: 2025-01-31
-- Purpose: Change from base×multiplier to fixed rates per tier
-- =====================================================
--
-- CORRECTION: The original 020_chef_pay_system.sql used a WRONG approach:
--   - Single base rate ($13/adult, $6.50/kid)
--   - Then multiplied by tier: 80% (new), 100% (chef), 115% (senior)
--
-- CORRECT approach (this migration):
--   - Each tier has its OWN fixed rates
--   - Junior Chef: $10/adult, $5/kid, $0/toddler
--   - Chef: $12/adult, $6/kid, $0/toddler
--   - Senior Chef: $13/adult, $6.50/kid, $0/toddler
--   - Station Manager: $15/adult, $7.50/kid, $0/toddler (NEW)
--   - Travel fee: 100% goes to chef (unchanged)
--
-- =====================================================

BEGIN;

-- =====================================================
-- PART 1: Add station_manager to pay_rate_class enum
-- =====================================================

-- PostgreSQL doesn't support INSERT into existing enum easily,
-- so we need to use ALTER TYPE ... ADD VALUE
ALTER TYPE public.pay_rate_class ADD VALUE IF NOT EXISTS 'station_manager' AFTER 'senior_chef';

-- Rename 'new_chef' to 'junior_chef' for clarity
-- Note: PostgreSQL doesn't support renaming enum values, so we'll use the existing value
-- and just update the display names in dynamic_variables

COMMENT ON TYPE public.pay_rate_class IS 'Chef pay rate classification: junior/new_chef ($10/adult), chef ($12/adult), senior_chef ($13/adult), station_manager ($15/adult)';

-- =====================================================
-- PART 2: Update chef_earnings table comment
-- =====================================================

COMMENT ON TABLE ops.chef_earnings IS 'Detailed earnings breakdown per event. Uses fixed per-tier rates (NOT multipliers). Junior=$10/adult, Chef=$12/adult, Senior=$13/adult, Manager=$15/adult. Travel=100% to chef.';

-- =====================================================
-- PART 3: Remove old multiplier variables (WRONG approach)
-- =====================================================

-- Delete the old multiplier-based variables
DELETE FROM public.dynamic_variables
WHERE category = 'chef_pay'
AND key IN ('chef_pay_mult_new', 'chef_pay_mult_chef', 'chef_pay_mult_senior',
            'chef_pay_adult_cents', 'chef_pay_kid_cents', 'chef_pay_toddler_cents');

-- =====================================================
-- PART 4: Insert NEW per-tier rate variables (CORRECT approach)
-- =====================================================

-- Junior Chef (formerly new_chef) rates: $10/adult, $5/kid
INSERT INTO public.dynamic_variables (category, key, value, display_name, description, is_active)
VALUES
    ('chef_pay', 'junior_adult_cents', '1000', 'Junior Chef - Per Adult (cents)', 'Junior chef pay per adult guest. $10.00 = 1000 cents.', true),
    ('chef_pay', 'junior_kid_cents', '500', 'Junior Chef - Per Child (cents)', 'Junior chef pay per child (6-12). $5.00 = 500 cents.', true),
    ('chef_pay', 'junior_toddler_cents', '0', 'Junior Chef - Per Toddler (cents)', 'Junior chef pay per toddler (under 5). $0.00 = 0 cents.', true)
ON CONFLICT (category, key) DO UPDATE SET
    value = EXCLUDED.value,
    display_name = EXCLUDED.display_name,
    description = EXCLUDED.description;

-- Chef (standard) rates: $12/adult, $6/kid
INSERT INTO public.dynamic_variables (category, key, value, display_name, description, is_active)
VALUES
    ('chef_pay', 'chef_adult_cents', '1200', 'Chef - Per Adult (cents)', 'Standard chef pay per adult guest. $12.00 = 1200 cents.', true),
    ('chef_pay', 'chef_kid_cents', '600', 'Chef - Per Child (cents)', 'Standard chef pay per child (6-12). $6.00 = 600 cents.', true),
    ('chef_pay', 'chef_toddler_cents', '0', 'Chef - Per Toddler (cents)', 'Standard chef pay per toddler (under 5). $0.00 = 0 cents.', true)
ON CONFLICT (category, key) DO UPDATE SET
    value = EXCLUDED.value,
    display_name = EXCLUDED.display_name,
    description = EXCLUDED.description;

-- Senior Chef rates: $13/adult, $6.50/kid
INSERT INTO public.dynamic_variables (category, key, value, display_name, description, is_active)
VALUES
    ('chef_pay', 'senior_adult_cents', '1300', 'Senior Chef - Per Adult (cents)', 'Senior chef pay per adult guest. $13.00 = 1300 cents.', true),
    ('chef_pay', 'senior_kid_cents', '650', 'Senior Chef - Per Child (cents)', 'Senior chef pay per child (6-12). $6.50 = 650 cents.', true),
    ('chef_pay', 'senior_toddler_cents', '0', 'Senior Chef - Per Toddler (cents)', 'Senior chef pay per toddler (under 5). $0.00 = 0 cents.', true)
ON CONFLICT (category, key) DO UPDATE SET
    value = EXCLUDED.value,
    display_name = EXCLUDED.display_name,
    description = EXCLUDED.description;

-- Station Manager rates: $15/adult, $7.50/kid (when cooking as backup)
INSERT INTO public.dynamic_variables (category, key, value, display_name, description, is_active)
VALUES
    ('chef_pay', 'manager_adult_cents', '1500', 'Station Manager - Per Adult (cents)', 'Station manager pay per adult when cooking as backup. $15.00 = 1500 cents.', true),
    ('chef_pay', 'manager_kid_cents', '750', 'Station Manager - Per Child (cents)', 'Station manager pay per child when cooking as backup. $7.50 = 750 cents.', true),
    ('chef_pay', 'manager_toddler_cents', '0', 'Station Manager - Per Toddler (cents)', 'Station manager pay per toddler. $0.00 = 0 cents.', true)
ON CONFLICT (category, key) DO UPDATE SET
    value = EXCLUDED.value,
    display_name = EXCLUDED.display_name,
    description = EXCLUDED.description;

-- Travel fee percentage (keep - this is correct at 100%)
INSERT INTO public.dynamic_variables (category, key, value, display_name, description, is_active)
VALUES
    ('chef_pay', 'travel_pct', '100', 'Chef Travel Fee %', 'Percentage of travel fee that goes to chef. 100 = 100% (full travel fee).', true)
ON CONFLICT (category, key) DO UPDATE SET
    value = EXCLUDED.value,
    display_name = EXCLUDED.display_name,
    description = EXCLUDED.description;

-- =====================================================
-- PART 5: Update chef_earnings column comment
-- =====================================================

COMMENT ON COLUMN ops.chef_earnings.rate_multiplier IS 'DEPRECATED - No longer used. Each tier has fixed rates. Kept for backwards compatibility, always set to 1.00.';

COMMIT;

-- =====================================================
-- VERIFICATION QUERIES
-- =====================================================

-- Verify new SSoT variables
-- SELECT category, key, value, display_name FROM public.dynamic_variables
-- WHERE category = 'chef_pay' ORDER BY key;

-- Expected output:
-- chef_adult_cents        | 1200 | Chef - Per Adult
-- chef_kid_cents          | 600  | Chef - Per Child
-- chef_toddler_cents      | 0    | Chef - Per Toddler
-- junior_adult_cents      | 1000 | Junior Chef - Per Adult
-- junior_kid_cents        | 500  | Junior Chef - Per Child
-- junior_toddler_cents    | 0    | Junior Chef - Per Toddler
-- manager_adult_cents     | 1500 | Station Manager - Per Adult
-- manager_kid_cents       | 750  | Station Manager - Per Child
-- manager_toddler_cents   | 0    | Station Manager - Per Toddler
-- senior_adult_cents      | 1300 | Senior Chef - Per Adult
-- senior_kid_cents        | 650  | Senior Chef - Per Child
-- senior_toddler_cents    | 0    | Senior Chef - Per Toddler
-- travel_pct              | 100  | Chef Travel Fee %

-- Verify enum has station_manager
-- SELECT unnest(enum_range(NULL::pay_rate_class));

-- =====================================================
-- ROLLBACK SCRIPT
-- =====================================================
-- BEGIN;
-- -- Delete new per-tier variables
-- DELETE FROM public.dynamic_variables WHERE category = 'chef_pay';
-- -- Note: Cannot remove enum value in PostgreSQL, station_manager will remain
-- -- Re-insert old multiplier variables if needed
-- COMMIT;
