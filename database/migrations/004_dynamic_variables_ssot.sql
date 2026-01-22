-- =====================================================
-- Migration: Dynamic Variables - Single Source of Truth
-- Created: 2025-01-28
-- Purpose: Create dynamic_variables table for all configurable business values
--          Enables admin to change pricing, policies, and settings via UI
--          WITHOUT requiring code changes or deployments
-- =====================================================

BEGIN;

-- =====================================================
-- 1. DYNAMIC VARIABLES TABLE
-- =====================================================
-- Stores all configurable business values (pricing, policies, travel fees, etc.)
-- Uses JSONB for flexible value storage
-- Supports scheduled changes with effective_from/to dates

CREATE TABLE IF NOT EXISTS public.dynamic_variables (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Categorization
    category VARCHAR(50) NOT NULL,           -- 'pricing', 'policy', 'travel', 'menu', 'booking'
    key VARCHAR(100) NOT NULL,               -- 'adult_price_cents', 'deposit_amount_cents'

    -- Value storage (JSONB for flexibility)
    value JSONB NOT NULL,                    -- {"amount": 5500} or {"enabled": true}

    -- Display and documentation
    display_name VARCHAR(200) NOT NULL,       -- "Adult Price"
    description TEXT,                         -- "Per-person price for adults (13+)"
    unit VARCHAR(50),                         -- "cents", "miles", "hours", "percent"

    -- Validation rules (enforced by application)
    validation_rules JSONB,                   -- {"min": 0, "max": 100000, "type": "integer"}

    -- Scheduled changes support
    effective_from TIMESTAMPTZ DEFAULT NOW(), -- When this value becomes active
    effective_to TIMESTAMPTZ,                 -- When this value expires (null = forever)

    -- Audit fields
    is_active BOOLEAN DEFAULT true,
    updated_by UUID,                          -- References identity.users if exists
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    created_at TIMESTAMPTZ DEFAULT NOW(),

    -- Ensure unique key per category (for active records)
    CONSTRAINT uq_dynamic_variables_key UNIQUE (category, key)
);

-- Indexes for fast lookups
CREATE INDEX IF NOT EXISTS idx_dynamic_variables_category ON public.dynamic_variables(category);
CREATE INDEX IF NOT EXISTS idx_dynamic_variables_key ON public.dynamic_variables(key);
CREATE INDEX IF NOT EXISTS idx_dynamic_variables_active ON public.dynamic_variables(is_active) WHERE is_active = true;
CREATE INDEX IF NOT EXISTS idx_dynamic_variables_effective ON public.dynamic_variables(effective_from, effective_to);

-- Comments for documentation
COMMENT ON TABLE public.dynamic_variables IS 'Single Source of Truth for all configurable business values. Updated via Admin UI.';
COMMENT ON COLUMN public.dynamic_variables.category IS 'Value category: pricing, policy, travel, menu, booking';
COMMENT ON COLUMN public.dynamic_variables.key IS 'Unique key within category, e.g., adult_price_cents';
COMMENT ON COLUMN public.dynamic_variables.value IS 'JSONB value, structure depends on key type';
COMMENT ON COLUMN public.dynamic_variables.unit IS 'Unit of measurement for display: cents, miles, hours, percent';
COMMENT ON COLUMN public.dynamic_variables.effective_from IS 'When this value becomes active (for scheduled changes)';
COMMENT ON COLUMN public.dynamic_variables.effective_to IS 'When this value expires (null = never expires)';


-- =====================================================
-- 2. CONFIG AUDIT LOG TABLE
-- =====================================================
-- Tracks all changes to dynamic_variables for compliance and debugging
-- Immutable - records are NEVER updated or deleted

CREATE TABLE IF NOT EXISTS public.config_audit_log (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- What changed
    variable_id UUID NOT NULL REFERENCES public.dynamic_variables(id),
    category VARCHAR(50) NOT NULL,
    key VARCHAR(100) NOT NULL,

    -- Change details
    old_value JSONB,                          -- Previous value (null for creates)
    new_value JSONB NOT NULL,                 -- New value
    change_type VARCHAR(20) NOT NULL,         -- 'create', 'update', 'delete', 'restore'

    -- Who and when
    changed_by UUID,                          -- References identity.users
    changed_by_email VARCHAR(255),            -- Denormalized for audit trail
    changed_at TIMESTAMPTZ DEFAULT NOW(),

    -- Why (optional reason)
    change_reason TEXT,

    -- Request context
    ip_address INET,
    user_agent TEXT,
    request_id UUID                           -- Correlation ID for debugging
);

-- Index for finding changes to a specific variable
CREATE INDEX IF NOT EXISTS idx_config_audit_log_variable ON public.config_audit_log(variable_id);
CREATE INDEX IF NOT EXISTS idx_config_audit_log_key ON public.config_audit_log(category, key);
CREATE INDEX IF NOT EXISTS idx_config_audit_log_changed_at ON public.config_audit_log(changed_at DESC);
CREATE INDEX IF NOT EXISTS idx_config_audit_log_changed_by ON public.config_audit_log(changed_by);

COMMENT ON TABLE public.config_audit_log IS 'Immutable audit log of all configuration changes. Never modified after creation.';


-- =====================================================
-- 3. SEED DATA - Current Pricing Values
-- =====================================================
-- These are the CURRENT values from ai_booking_config.py
-- After migration, ai_booking_config.py will READ from this table

-- Pricing category
INSERT INTO public.dynamic_variables (category, key, value, display_name, description, unit, validation_rules) VALUES
    ('pricing', 'adult_price_cents', '{"amount": 5500}', 'Adult Price', 'Per-person price for adults (13+)', 'cents', '{"min": 1000, "max": 50000, "type": "integer"}'),
    ('pricing', 'child_price_cents', '{"amount": 3000}', 'Child Price', 'Per-person price for children (6-12)', 'cents', '{"min": 500, "max": 30000, "type": "integer"}'),
    ('pricing', 'child_free_under_age', '{"amount": 5}', 'Free Under Age', 'Children under this age eat free', 'years', '{"min": 0, "max": 12, "type": "integer"}'),
    ('pricing', 'party_minimum_cents', '{"amount": 55000}', 'Party Minimum', 'Minimum total order amount', 'cents', '{"min": 10000, "max": 200000, "type": "integer"}'),
    ('pricing', 'deposit_amount_cents', '{"amount": 10000}', 'Deposit Amount', 'Refundable deposit to secure booking', 'cents', '{"min": 5000, "max": 50000, "type": "integer"}'),
    ('pricing', 'extra_protein_price_cents', '{"amount": 1000}', 'Extra Protein Price', 'Price for each extra protein beyond 2 per guest', 'cents', '{"min": 500, "max": 5000, "type": "integer"}')
ON CONFLICT (category, key) DO NOTHING;

-- Premium protein upgrades
INSERT INTO public.dynamic_variables (category, key, value, display_name, description, unit, validation_rules) VALUES
    ('pricing', 'upgrade_salmon_cents', '{"amount": 500}', 'Salmon Upgrade', 'Premium upgrade price for Salmon', 'cents', '{"min": 0, "max": 5000, "type": "integer"}'),
    ('pricing', 'upgrade_scallops_cents', '{"amount": 500}', 'Scallops Upgrade', 'Premium upgrade price for Scallops', 'cents', '{"min": 0, "max": 5000, "type": "integer"}'),
    ('pricing', 'upgrade_filet_mignon_cents', '{"amount": 500}', 'Filet Mignon Upgrade', 'Premium upgrade price for Filet Mignon', 'cents', '{"min": 0, "max": 5000, "type": "integer"}'),
    ('pricing', 'upgrade_lobster_tail_cents', '{"amount": 1500}', 'Lobster Tail Upgrade', 'Premium upgrade price for Lobster Tail', 'cents', '{"min": 0, "max": 10000, "type": "integer"}')
ON CONFLICT (category, key) DO NOTHING;

-- Add-on items
INSERT INTO public.dynamic_variables (category, key, value, display_name, description, unit, validation_rules) VALUES
    ('pricing', 'addon_yakisoba_noodles_cents', '{"amount": 500}', 'Yakisoba Noodles', 'Add-on price for Yakisoba Noodles', 'cents', '{"min": 0, "max": 3000, "type": "integer"}'),
    ('pricing', 'addon_extra_fried_rice_cents', '{"amount": 500}', 'Extra Fried Rice', 'Add-on price for Extra Fried Rice', 'cents', '{"min": 0, "max": 3000, "type": "integer"}'),
    ('pricing', 'addon_extra_vegetables_cents', '{"amount": 500}', 'Extra Vegetables', 'Add-on price for Extra Vegetables', 'cents', '{"min": 0, "max": 3000, "type": "integer"}'),
    ('pricing', 'addon_edamame_cents', '{"amount": 500}', 'Edamame', 'Add-on price for Edamame', 'cents', '{"min": 0, "max": 3000, "type": "integer"}'),
    ('pricing', 'addon_gyoza_cents', '{"amount": 1000}', 'Gyoza', 'Add-on price for Gyoza (10 pieces)', 'cents', '{"min": 0, "max": 5000, "type": "integer"}')
ON CONFLICT (category, key) DO NOTHING;

-- Travel fee settings
INSERT INTO public.dynamic_variables (category, key, value, display_name, description, unit, validation_rules) VALUES
    ('travel', 'free_miles', '{"amount": 30}', 'Free Travel Miles', 'Miles included in base price', 'miles', '{"min": 0, "max": 100, "type": "integer"}'),
    ('travel', 'per_mile_cents', '{"amount": 200}', 'Per Mile Rate', 'Charge per mile after free miles', 'cents', '{"min": 50, "max": 1000, "type": "integer"}'),
    ('travel', 'max_service_radius_miles', '{"amount": 100}', 'Max Service Radius', 'Maximum distance we will travel', 'miles', '{"min": 50, "max": 500, "type": "integer"}')
ON CONFLICT (category, key) DO NOTHING;

-- Policy settings
INSERT INTO public.dynamic_variables (category, key, value, display_name, description, unit, validation_rules) VALUES
    ('policy', 'deposit_refund_days', '{"amount": 4}', 'Deposit Refund Window', 'Days before event when deposit is refundable', 'days', '{"min": 1, "max": 30, "type": "integer"}'),
    ('policy', 'min_booking_advance_hours', '{"amount": 48}', 'Minimum Advance Booking', 'Minimum hours before event to book', 'hours', '{"min": 24, "max": 168, "type": "integer"}'),
    ('policy', 'menu_change_deadline_hours', '{"amount": 12}', 'Menu Change Deadline', 'Hours before event when menu changes are locked', 'hours', '{"min": 6, "max": 72, "type": "integer"}'),
    ('policy', 'free_reschedule_hours', '{"amount": 24}', 'Free Reschedule Window', 'Hours before event to reschedule for free', 'hours', '{"min": 12, "max": 72, "type": "integer"}'),
    ('policy', 'reschedule_fee_cents', '{"amount": 10000}', 'Late Reschedule Fee', 'Fee for rescheduling within deadline', 'cents', '{"min": 0, "max": 50000, "type": "integer"}')
ON CONFLICT (category, key) DO NOTHING;

-- Menu settings
INSERT INTO public.dynamic_variables (category, key, value, display_name, description, unit, validation_rules) VALUES
    ('menu', 'proteins_per_guest', '{"amount": 2}', 'Proteins Per Guest', 'Number of protein selections included per guest', 'count', '{"min": 1, "max": 5, "type": "integer"}'),
    ('menu', 'free_proteins', '{"items": ["chicken", "ny_strip_steak", "shrimp", "calamari", "tofu"]}', 'Free Base Proteins', 'Proteins included at no extra charge', 'list', '{"type": "array"}'),
    ('menu', 'premium_proteins', '{"items": ["salmon", "scallops", "filet_mignon", "lobster_tail"]}', 'Premium Upgrade Proteins', 'Proteins that cost extra as upgrades', 'list', '{"type": "array"}')
ON CONFLICT (category, key) DO NOTHING;

-- Booking settings
INSERT INTO public.dynamic_variables (category, key, value, display_name, description, unit, validation_rules) VALUES
    ('booking', 'min_guests', '{"amount": 1}', 'Minimum Guests', 'Minimum number of guests for a booking', 'count', '{"min": 1, "max": 10, "type": "integer"}'),
    ('booking', 'max_guests', '{"amount": 100}', 'Maximum Guests', 'Maximum number of guests for a single event', 'count', '{"min": 20, "max": 200, "type": "integer"}'),
    ('booking', 'min_guests_for_hibachi', '{"amount": 10}', 'Minimum for Hibachi', 'Minimum guests to reach party minimum', 'count', '{"min": 5, "max": 20, "type": "integer"}')
ON CONFLICT (category, key) DO NOTHING;

-- Gratuity suggestions
INSERT INTO public.dynamic_variables (category, key, value, display_name, description, unit, validation_rules) VALUES
    ('policy', 'gratuity_min_percent', '{"amount": 20}', 'Suggested Gratuity Min', 'Minimum suggested gratuity percentage', 'percent', '{"min": 0, "max": 50, "type": "integer"}'),
    ('policy', 'gratuity_max_percent', '{"amount": 35}', 'Suggested Gratuity Max', 'Maximum suggested gratuity percentage', 'percent', '{"min": 10, "max": 100, "type": "integer"}')
ON CONFLICT (category, key) DO NOTHING;


-- =====================================================
-- 4. HELPER FUNCTION: Get Current Value
-- =====================================================
-- Returns the current effective value for a given category/key

CREATE OR REPLACE FUNCTION get_dynamic_variable(p_category VARCHAR, p_key VARCHAR)
RETURNS JSONB AS $$
DECLARE
    result JSONB;
BEGIN
    SELECT value INTO result
    FROM public.dynamic_variables
    WHERE category = p_category
      AND key = p_key
      AND is_active = true
      AND (effective_from IS NULL OR effective_from <= NOW())
      AND (effective_to IS NULL OR effective_to > NOW())
    ORDER BY effective_from DESC NULLS LAST
    LIMIT 1;

    RETURN result;
END;
$$ LANGUAGE plpgsql STABLE;

COMMENT ON FUNCTION get_dynamic_variable IS 'Get current effective value for a dynamic variable';


-- =====================================================
-- 5. VIEW: Current Active Variables
-- =====================================================
-- Easy view of all currently active variables

CREATE OR REPLACE VIEW public.current_dynamic_variables AS
SELECT
    id,
    category,
    key,
    value,
    display_name,
    description,
    unit,
    effective_from,
    effective_to,
    updated_at,
    updated_by
FROM public.dynamic_variables
WHERE is_active = true
  AND (effective_from IS NULL OR effective_from <= NOW())
  AND (effective_to IS NULL OR effective_to > NOW())
ORDER BY category, key;

COMMENT ON VIEW public.current_dynamic_variables IS 'View of currently active dynamic variables';


COMMIT;

-- =====================================================
-- ROLLBACK SCRIPT (if needed)
-- =====================================================
-- DROP VIEW IF EXISTS public.current_dynamic_variables;
-- DROP FUNCTION IF EXISTS get_dynamic_variable;
-- DROP TABLE IF EXISTS public.config_audit_log;
-- DROP TABLE IF EXISTS public.dynamic_variables;
