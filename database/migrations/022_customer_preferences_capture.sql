-- =====================================================
-- Migration: 022_customer_preferences_capture.sql
-- Created: 2025-01-25
-- Purpose: Unified customer preferences capture system
--          - Chef request tracking (for bonus)
--          - Allergen/dietary capture (for safety)
--          - Special instructions
-- =====================================================

BEGIN;

-- =====================================================
-- SECTION 1: Chef Request Tracking (for bonus pay)
-- =====================================================

-- Add chef request tracking columns to bookings
ALTER TABLE core.bookings ADD COLUMN IF NOT EXISTS
    chef_was_requested BOOLEAN DEFAULT false;

COMMENT ON COLUMN core.bookings.chef_was_requested IS
    'True if customer voluntarily requested a specific chef (triggers bonus pay)';

ALTER TABLE core.bookings ADD COLUMN IF NOT EXISTS
    requested_chef_id UUID REFERENCES ops.chefs(id) ON DELETE SET NULL;

COMMENT ON COLUMN core.bookings.requested_chef_id IS
    'The chef that was specifically requested by customer (may differ from assigned chef)';

ALTER TABLE core.bookings ADD COLUMN IF NOT EXISTS
    chef_request_source VARCHAR(30);

COMMENT ON COLUMN core.bookings.chef_request_source IS
    'How the chef request was captured: online_form, phone, text, ai_chat, returning_customer, email';

-- =====================================================
-- SECTION 2: Allergen & Dietary Capture (for safety)
-- =====================================================

-- Check if allergen columns already exist (from earlier migrations)
DO $$
BEGIN
    -- allergen_disclosure (free text)
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_schema = 'core'
        AND table_name = 'bookings'
        AND column_name = 'allergen_disclosure'
    ) THEN
        ALTER TABLE core.bookings ADD COLUMN allergen_disclosure TEXT;
        COMMENT ON COLUMN core.bookings.allergen_disclosure IS
            'Free text description of allergens/dietary needs not covered by common list';
    END IF;

    -- common_allergens (JSONB array)
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_schema = 'core'
        AND table_name = 'bookings'
        AND column_name = 'common_allergens'
    ) THEN
        ALTER TABLE core.bookings ADD COLUMN common_allergens JSONB DEFAULT '[]'::jsonb;
        COMMENT ON COLUMN core.bookings.common_allergens IS
            'Array of common allergen codes: shellfish, soy, eggs, dairy, sesame, nuts, gluten, fish';
    END IF;

    -- allergen_confirmed
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_schema = 'core'
        AND table_name = 'bookings'
        AND column_name = 'allergen_confirmed'
    ) THEN
        ALTER TABLE core.bookings ADD COLUMN allergen_confirmed BOOLEAN DEFAULT false;
        COMMENT ON COLUMN core.bookings.allergen_confirmed IS
            'True if allergen info was explicitly confirmed with customer';
    END IF;

    -- allergen_confirmed_at
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_schema = 'core'
        AND table_name = 'bookings'
        AND column_name = 'allergen_confirmed_at'
    ) THEN
        ALTER TABLE core.bookings ADD COLUMN allergen_confirmed_at TIMESTAMPTZ;
        COMMENT ON COLUMN core.bookings.allergen_confirmed_at IS
            'When allergen info was confirmed with customer';
    END IF;

    -- allergen_confirmed_method
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_schema = 'core'
        AND table_name = 'bookings'
        AND column_name = 'allergen_confirmed_method'
    ) THEN
        ALTER TABLE core.bookings ADD COLUMN allergen_confirmed_method VARCHAR(20);
        COMMENT ON COLUMN core.bookings.allergen_confirmed_method IS
            'How allergen info was confirmed: online, sms, phone, email, in_person';
    END IF;

    -- allergen_confirmed_by (which staff member)
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_schema = 'core'
        AND table_name = 'bookings'
        AND column_name = 'allergen_confirmed_by'
    ) THEN
        ALTER TABLE core.bookings ADD COLUMN allergen_confirmed_by UUID REFERENCES identity.users(id);
        COMMENT ON COLUMN core.bookings.allergen_confirmed_by IS
            'Staff member who confirmed allergen info with customer';
    END IF;
END $$;

-- =====================================================
-- SECTION 3: Common Allergens Reference Table
-- =====================================================

CREATE TABLE IF NOT EXISTS core.common_allergens (
    id SERIAL PRIMARY KEY,
    code VARCHAR(30) NOT NULL UNIQUE,
    display_name VARCHAR(100) NOT NULL,
    icon VARCHAR(10),
    chef_action TEXT,  -- What chef should do for this allergen
    display_order INT DEFAULT 0,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

COMMENT ON TABLE core.common_allergens IS
    'Reference table of common allergens with cooking instructions for chefs';

-- Seed common allergens (idempotent)
INSERT INTO core.common_allergens (code, display_name, icon, chef_action, display_order) VALUES
    ('shellfish', 'Shellfish (shrimp, crab, lobster)', '🦐', 'Cook shrimp/calamari LAST on separate section of grill. Use separate utensils.', 1),
    ('fish', 'Fish', '🐟', 'Cook fish on clean section of grill. Use separate utensils.', 2),
    ('soy', 'Soy', '🫘', 'Use TAMARI or coconut aminos instead of regular soy sauce.', 3),
    ('gluten', 'Wheat/Gluten', '🌾', 'Use TAMARI (gluten-free soy sauce). Avoid yakisoba and gyoza.', 4),
    ('sesame', 'Sesame', '🌱', 'Skip sesame seeds and sesame oil. Use alternative oil.', 5),
    ('eggs', 'Eggs', '🥚', 'Make fried rice WITHOUT egg for this guest.', 6),
    ('dairy', 'Dairy/Milk', '🥛', 'We use dairy-free butter by default - confirm with customer.', 7),
    ('nuts', 'Peanuts/Tree Nuts', '🥜', 'We are 100% nut-free facility. Confirm no cross-contact from customer-provided items.', 8),
    ('msg', 'MSG Sensitivity', '⚠️', 'No MSG added. Standard hibachi has no MSG.', 9)
ON CONFLICT (code) DO UPDATE SET
    display_name = EXCLUDED.display_name,
    icon = EXCLUDED.icon,
    chef_action = EXCLUDED.chef_action,
    display_order = EXCLUDED.display_order;

-- =====================================================
-- SECTION 4: SSoT Dynamic Variables
-- =====================================================

-- Requested Chef Bonus Percentage
INSERT INTO dynamic_variables (category, key, value, display_name, description, is_active)
VALUES ('chef_pay', 'requested_chef_bonus_pct', '10', 'Requested Chef Bonus %',
        'Bonus percentage when customer requests specific chef (applied to base order value only, excludes travel/upgrades/add-ons)', true)
ON CONFLICT (category, key) DO UPDATE SET
    display_name = EXCLUDED.display_name,
    description = EXCLUDED.description;

-- =====================================================
-- SECTION 5: Indexes for Performance
-- =====================================================

-- Index for finding bookings with chef requests (for bonus reporting)
CREATE INDEX IF NOT EXISTS idx_bookings_chef_requested
    ON core.bookings(chef_was_requested)
    WHERE chef_was_requested = true;

-- Index for finding bookings with allergens (for prep summaries)
CREATE INDEX IF NOT EXISTS idx_bookings_has_allergens
    ON core.bookings(allergen_confirmed)
    WHERE allergen_confirmed = true;

-- Index for requested chef lookup
CREATE INDEX IF NOT EXISTS idx_bookings_requested_chef
    ON core.bookings(requested_chef_id)
    WHERE requested_chef_id IS NOT NULL;

COMMIT;

-- =====================================================
-- VERIFICATION QUERIES (run after migration)
-- =====================================================

-- Check new columns exist:
-- SELECT column_name, data_type, column_default
-- FROM information_schema.columns
-- WHERE table_schema = 'core' AND table_name = 'bookings'
-- AND column_name IN ('chef_was_requested', 'requested_chef_id', 'chef_request_source',
--                     'allergen_disclosure', 'common_allergens', 'allergen_confirmed');

-- Check common_allergens table:
-- SELECT * FROM core.common_allergens ORDER BY display_order;

-- Check dynamic variable:
-- SELECT * FROM dynamic_variables WHERE category = 'chef_pay' AND key = 'requested_chef_bonus_pct';
