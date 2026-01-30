-- =====================================================
-- Migration: 020_chef_pay_system.sql
-- Created: 2025-01-30
-- Purpose: Comprehensive chef pay rate system
--
-- Features:
-- 1. Add party_toddlers to core.bookings
-- 2. Add pay_rate_class and seniority_level to ops.chefs
-- 3. Create ops.chef_scores table for individual score history
-- 4. Create ops.chef_earnings table for earnings breakdown
-- 5. Add chef pay SSoT variables to dynamic_variables
--
-- User Decisions Applied:
-- - Pay Rate Classes: NEW_CHEF (80%), CHEF (100%), SENIOR_CHEF (115%)
-- - Seniority Levels: JUNIOR, STANDARD, SENIOR, EXPERT (performance-based)
-- - Event Split: Headcount-based ONLY (not pay-rate based)
-- - Travel Fee: 100% goes to chef
-- - Score Storage: Individual history (admin views all, manually assigns level)
-- - Chef Dashboard: NO pay visibility (admin/station manager only)
-- =====================================================

BEGIN;

-- =====================================================
-- PART 1: Add party_toddlers to core.bookings
-- =====================================================

ALTER TABLE core.bookings
    ADD COLUMN IF NOT EXISTS party_toddlers INTEGER NOT NULL DEFAULT 0;

-- Add check constraint for non-negative party_toddlers
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint
        WHERE conname = 'check_party_toddlers_non_negative'
    ) THEN
        ALTER TABLE core.bookings
            ADD CONSTRAINT check_party_toddlers_non_negative
            CHECK (party_toddlers >= 0);
    END IF;
END $$;

COMMENT ON COLUMN core.bookings.party_toddlers IS 'Number of toddlers (under free age threshold, e.g., 5). Free - $0 chef pay.';

-- =====================================================
-- PART 2: Create enums for chef pay system
-- =====================================================

-- Pay Rate Class enum (determines pay multiplier)
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'pay_rate_class') THEN
        CREATE TYPE public.pay_rate_class AS ENUM (
            'new_chef',      -- 80% of base rate (probationary)
            'chef',          -- 100% standard rate
            'senior_chef'    -- 115% premium rate
        );
    END IF;
END $$;

COMMENT ON TYPE public.pay_rate_class IS 'Chef pay rate class determining percentage multiplier. Managed by super admin via SSoT.';

-- Seniority Level enum (performance-based, manually assigned by admin)
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'chef_seniority_level') THEN
        CREATE TYPE public.chef_seniority_level AS ENUM (
            'junior',        -- Entry level
            'standard',      -- Normal performance
            'senior',        -- High performer
            'expert'         -- Top performer
        );
    END IF;
END $$;

COMMENT ON TYPE public.chef_seniority_level IS 'Chef seniority level for display and assignment priority. Manually assigned by admin based on score history.';

-- Earnings Status enum (for chef_earnings table)
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'earnings_status') THEN
        CREATE TYPE public.earnings_status AS ENUM (
            'pending',       -- Event not yet completed
            'calculated',    -- Auto-calculated after event
            'adjusted',      -- Manually adjusted by admin
            'paid',          -- Payment processed
            'disputed'       -- Under review
        );
    END IF;
END $$;

COMMENT ON TYPE public.earnings_status IS 'Status of chef earnings record. Tracks payment lifecycle.';

-- =====================================================
-- PART 3: Add columns to ops.chefs
-- =====================================================

-- Add pay_rate_class column
ALTER TABLE ops.chefs
    ADD COLUMN IF NOT EXISTS pay_rate_class public.pay_rate_class NOT NULL DEFAULT 'new_chef';

COMMENT ON COLUMN ops.chefs.pay_rate_class IS 'Pay rate multiplier class: new_chef=80%, chef=100%, senior_chef=115%. Managed by super admin.';

-- Add seniority_level column
ALTER TABLE ops.chefs
    ADD COLUMN IF NOT EXISTS seniority_level public.chef_seniority_level NOT NULL DEFAULT 'junior';

COMMENT ON COLUMN ops.chefs.seniority_level IS 'Seniority level based on performance. Manually assigned by admin based on score history.';

-- Create indexes for efficient querying
CREATE INDEX IF NOT EXISTS idx_ops_chefs_pay_rate_class ON ops.chefs (pay_rate_class);
CREATE INDEX IF NOT EXISTS idx_ops_chefs_seniority_level ON ops.chefs (seniority_level);

-- =====================================================
-- PART 4: Create ops.chef_scores table (individual score history)
-- =====================================================

CREATE TABLE IF NOT EXISTS ops.chef_scores (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Foreign key to chef
    chef_id UUID NOT NULL REFERENCES ops.chefs(id) ON DELETE CASCADE,

    -- Rater information
    rater_type VARCHAR(50) NOT NULL, -- 'customer', 'station_manager', 'admin', 'system'
    rater_id UUID NULL, -- Can be null for anonymous reviews
    rater_name VARCHAR(255) NULL, -- Display name at time of rating

    -- Score details (1-5 scale)
    score NUMERIC(3, 2) NOT NULL CHECK (score >= 1.0 AND score <= 5.0),

    -- Context
    booking_id UUID NULL, -- Link to booking if event-related

    -- Feedback (match SQLAlchemy ChefScore model in ops.py)
    comment TEXT NULL, -- Optional feedback text (was: notes)
    categories JSONB NULL, -- Breakdown scores: {food_quality: 5, presentation: 4, timeliness: 5} (was: category VARCHAR)

    -- Timestamps (immutable - no updated_at per model design)
    scored_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW() -- (was: created_at)
);

COMMENT ON TABLE ops.chef_scores IS 'Individual score history for each chef. Admin views all scores to manually determine seniority level.';

-- Indexes for chef_scores
CREATE INDEX IF NOT EXISTS idx_chef_scores_chef_id ON ops.chef_scores (chef_id);
CREATE INDEX IF NOT EXISTS idx_chef_scores_booking_id ON ops.chef_scores (booking_id);
CREATE INDEX IF NOT EXISTS idx_chef_scores_scored_at ON ops.chef_scores (scored_at DESC);
-- Note: categories is JSONB, use GIN index if needed for JSON queries

-- =====================================================
-- PART 5: Create ops.chef_earnings table (breakdown per event)
-- =====================================================

CREATE TABLE IF NOT EXISTS ops.chef_earnings (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Foreign keys
    chef_id UUID NOT NULL REFERENCES ops.chefs(id) ON DELETE CASCADE,
    booking_id UUID NOT NULL REFERENCES core.bookings(id) ON DELETE CASCADE,

    -- Headcount at time of event (snapshot for historical accuracy)
    adults_count INTEGER NOT NULL DEFAULT 0,      -- Number of adults (13+) at event
    children_count INTEGER NOT NULL DEFAULT 0,    -- Number of children (6-12) at event
    toddlers_count INTEGER NOT NULL DEFAULT 0,    -- Number of toddlers (under 6) - $0 rate
    total_chefs INTEGER NOT NULL DEFAULT 1,       -- Total chefs assigned - for split calculation

    -- Earnings breakdown (all amounts in cents)
    cooking_fee_cents INTEGER NOT NULL DEFAULT 0,     -- (adults × $13 + kids × $6.50) / total_chefs
    travel_fee_cents INTEGER NOT NULL DEFAULT 0,       -- 100% of travel fee goes to chef (not split)
    base_total_cents INTEGER NOT NULL DEFAULT 0,       -- cooking_fee + travel_fee before multiplier

    -- Pay rate info at time of calculation
    pay_rate_class public.pay_rate_class NOT NULL,
    rate_multiplier NUMERIC(4, 2) NOT NULL,            -- Multiplier: 0.80, 1.00, or 1.15
    final_amount_cents INTEGER NOT NULL DEFAULT 0,     -- base_total × rate_multiplier = final chef payment

    -- Status (uses earnings_status enum)
    status public.earnings_status NOT NULL DEFAULT 'pending',

    -- Adjustments
    adjustment_reason TEXT NULL,                       -- Reason for manual adjustment if status=adjusted
    adjusted_by UUID NULL,                             -- Admin/manager who made adjustment

    -- Timestamps
    calculated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    paid_at TIMESTAMP WITH TIME ZONE NULL,
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

COMMENT ON TABLE ops.chef_earnings IS 'Detailed earnings breakdown per event. Shows cooking_fee, travel_fee (100%), and event_value. Visible to admin and station manager only.';

-- Indexes for chef_earnings
CREATE INDEX IF NOT EXISTS idx_chef_earnings_chef_id ON ops.chef_earnings (chef_id);
CREATE INDEX IF NOT EXISTS idx_chef_earnings_booking_id ON ops.chef_earnings (booking_id);
CREATE INDEX IF NOT EXISTS idx_chef_earnings_calculated_at ON ops.chef_earnings (calculated_at);
CREATE INDEX IF NOT EXISTS idx_chef_earnings_status ON ops.chef_earnings (status);
CREATE INDEX IF NOT EXISTS idx_chef_earnings_chef_calculated ON ops.chef_earnings (chef_id, calculated_at);

-- Unique constraint: one earnings record per chef per booking
ALTER TABLE ops.chef_earnings
    ADD CONSTRAINT uq_chef_earnings_chef_booking UNIQUE (chef_id, booking_id);

-- =====================================================
-- PART 6: Add chef pay SSoT variables to dynamic_variables
-- =====================================================

-- Chef pay per headcount variables
INSERT INTO public.dynamic_variables (category, key, value, display_name, description, is_active)
VALUES
    ('chef_pay', 'chef_pay_adult_cents', '1300', 'Chef Pay Per Adult (cents)', 'Base chef pay per adult guest in cents. $13.00 = 1300 cents.', true),
    ('chef_pay', 'chef_pay_kid_cents', '650', 'Chef Pay Per Child (cents)', 'Base chef pay per child (6-12) in cents. $6.50 = 650 cents.', true),
    ('chef_pay', 'chef_pay_toddler_cents', '0', 'Chef Pay Per Toddler (cents)', 'Base chef pay per toddler (under 5) in cents. Free = 0 cents.', true)
ON CONFLICT (category, key) DO UPDATE SET
    value = EXCLUDED.value,
    display_name = EXCLUDED.display_name,
    description = EXCLUDED.description;

-- Pay rate class multipliers
INSERT INTO public.dynamic_variables (category, key, value, display_name, description, is_active)
VALUES
    ('chef_pay', 'chef_pay_mult_new', '80', 'New Chef Pay Rate %', 'Pay rate percentage for new_chef class. 80 = 80% of base rate.', true),
    ('chef_pay', 'chef_pay_mult_chef', '100', 'Chef Pay Rate %', 'Pay rate percentage for chef class. 100 = 100% of base rate.', true),
    ('chef_pay', 'chef_pay_mult_senior', '115', 'Senior Chef Pay Rate %', 'Pay rate percentage for senior_chef class. 115 = 115% of base rate.', true)
ON CONFLICT (category, key) DO UPDATE SET
    value = EXCLUDED.value,
    display_name = EXCLUDED.display_name,
    description = EXCLUDED.description;

-- Travel fee configuration for chef pay
INSERT INTO public.dynamic_variables (category, key, value, display_name, description, is_active)
VALUES
    ('chef_pay', 'chef_pay_travel_pct', '100', 'Chef Travel Fee %', 'Percentage of travel fee that goes to chef. 100 = 100% (full travel fee).', true)
ON CONFLICT (category, key) DO UPDATE SET
    value = EXCLUDED.value,
    display_name = EXCLUDED.display_name,
    description = EXCLUDED.description;

-- Child free age threshold (using existing variable if present)
INSERT INTO public.dynamic_variables (category, key, value, display_name, description, is_active)
VALUES
    ('pricing', 'child_free_under_age', '5', 'Child Free Under Age', 'Children under this age are free (toddlers). Ages 5 and under = free.', true)
ON CONFLICT (category, key) DO UPDATE SET
    value = EXCLUDED.value;

-- =====================================================
-- PART 7: Grant permissions
-- =====================================================

-- Grant permissions on new tables
GRANT SELECT, INSERT, UPDATE ON ops.chef_scores TO myhibachi_staging_user;
GRANT SELECT, INSERT, UPDATE ON ops.chef_earnings TO myhibachi_staging_user;
GRANT SELECT, INSERT, UPDATE ON ops.chef_scores TO myhibachi_user;
GRANT SELECT, INSERT, UPDATE ON ops.chef_earnings TO myhibachi_user;

-- Grant usage on sequences if any
GRANT USAGE ON ALL SEQUENCES IN SCHEMA ops TO myhibachi_staging_user;
GRANT USAGE ON ALL SEQUENCES IN SCHEMA ops TO myhibachi_user;

COMMIT;

-- =====================================================
-- VERIFICATION QUERIES (Run after migration)
-- =====================================================

-- Verify new column on bookings
-- SELECT column_name, data_type, column_default FROM information_schema.columns
-- WHERE table_schema = 'core' AND table_name = 'bookings' AND column_name = 'party_toddlers';

-- Verify new columns on chefs
-- SELECT column_name, data_type, column_default FROM information_schema.columns
-- WHERE table_schema = 'ops' AND table_name = 'chefs' AND column_name IN ('pay_rate_class', 'seniority_level');

-- Verify new tables
-- SELECT table_name FROM information_schema.tables WHERE table_schema = 'ops' AND table_name IN ('chef_scores', 'chef_earnings');

-- Verify SSoT variables
-- SELECT category, key, value, display_name FROM public.dynamic_variables WHERE category = 'chef_pay';

-- =====================================================
-- ROLLBACK SCRIPT (Keep as comment for emergency)
-- =====================================================
-- BEGIN;
-- DROP TABLE IF EXISTS ops.chef_earnings;
-- DROP TABLE IF EXISTS ops.chef_scores;
-- ALTER TABLE ops.chefs DROP COLUMN IF EXISTS pay_rate_class;
-- ALTER TABLE ops.chefs DROP COLUMN IF EXISTS seniority_level;
-- ALTER TABLE core.bookings DROP COLUMN IF EXISTS party_toddlers;
-- DROP TYPE IF EXISTS public.earnings_status;
-- DROP TYPE IF EXISTS public.pay_rate_class;
-- DROP TYPE IF EXISTS public.chef_seniority_level;
-- DELETE FROM public.dynamic_variables WHERE category = 'chef_pay';
-- COMMIT;
