-- =====================================================
-- Migration: Upgrade & Addon Prices - SSoT
-- Created: 2025-02-07
-- Purpose: Add premium protein upgrade and addon prices to dynamic_variables
--          Enables admin to change menu upgrade/addon pricing via UI
-- =====================================================

BEGIN;

-- =====================================================
-- 1. PREMIUM PROTEIN UPGRADES (category: 'menu')
-- =====================================================
-- These are upgrades that replace one of the 2 included proteins

INSERT INTO public.dynamic_variables (category, key, value, display_name, description, unit, validation_rules)
VALUES
    ('menu', 'salmon_upgrade_cents', '{"amount": 500}', 'Salmon Upgrade Price', 'Premium upgrade price for Salmon (per person)', 'cents', '{"min": 0, "max": 5000, "type": "integer"}'),
    ('menu', 'scallops_upgrade_cents', '{"amount": 500}', 'Scallops Upgrade Price', 'Premium upgrade price for Scallops (per person)', 'cents', '{"min": 0, "max": 5000, "type": "integer"}'),
    ('menu', 'filet_mignon_upgrade_cents', '{"amount": 500}', 'Filet Mignon Upgrade Price', 'Premium upgrade price for Filet Mignon (per person)', 'cents', '{"min": 0, "max": 5000, "type": "integer"}'),
    ('menu', 'lobster_tail_upgrade_cents', '{"amount": 1500}', 'Lobster Tail Upgrade Price', 'Luxury upgrade price for Lobster Tail (per person)', 'cents', '{"min": 0, "max": 10000, "type": "integer"}'),
    ('menu', 'extra_protein_cents', '{"amount": 1000}', 'Extra Protein Price', 'Price for additional (3rd+) protein per person', 'cents', '{"min": 0, "max": 5000, "type": "integer"}')
ON CONFLICT (category, key) DO UPDATE SET
    value = EXCLUDED.value,
    display_name = EXCLUDED.display_name,
    description = EXCLUDED.description,
    unit = EXCLUDED.unit,
    validation_rules = EXCLUDED.validation_rules,
    updated_at = NOW();

-- =====================================================
-- 2. ADDON ITEMS (category: 'menu')
-- =====================================================
-- These are additional items that can be ordered

INSERT INTO public.dynamic_variables (category, key, value, display_name, description, unit, validation_rules)
VALUES
    ('menu', 'yakisoba_noodles_cents', '{"amount": 500}', 'Yakisoba Noodles Price', 'Price for Yakisoba Noodles addon (per person)', 'cents', '{"min": 0, "max": 3000, "type": "integer"}'),
    ('menu', 'extra_fried_rice_cents', '{"amount": 500}', 'Extra Fried Rice Price', 'Price for extra fried rice addon (per person)', 'cents', '{"min": 0, "max": 3000, "type": "integer"}'),
    ('menu', 'extra_vegetables_cents', '{"amount": 500}', 'Extra Vegetables Price', 'Price for extra vegetables addon (per person)', 'cents', '{"min": 0, "max": 3000, "type": "integer"}'),
    ('menu', 'edamame_cents', '{"amount": 500}', 'Edamame Price', 'Price for Edamame addon (per person)', 'cents', '{"min": 0, "max": 3000, "type": "integer"}'),
    ('menu', 'gyoza_cents', '{"amount": 1000}', 'Gyoza Price', 'Price for Gyoza dumplings addon (per person)', 'cents', '{"min": 0, "max": 3000, "type": "integer"}')
ON CONFLICT (category, key) DO UPDATE SET
    value = EXCLUDED.value,
    display_name = EXCLUDED.display_name,
    description = EXCLUDED.description,
    unit = EXCLUDED.unit,
    validation_rules = EXCLUDED.validation_rules,
    updated_at = NOW();

COMMIT;

-- =====================================================
-- VERIFICATION QUERY
-- =====================================================
-- Run this to verify the migration:
-- SELECT category, key, value, display_name FROM public.dynamic_variables WHERE category = 'menu' ORDER BY key;
