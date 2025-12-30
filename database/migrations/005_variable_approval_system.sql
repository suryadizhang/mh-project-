-- =====================================================
-- Migration: Variable Approval System
-- Created: 2025-12-28
-- Purpose: Two-person approval for critical variable changes
--          - Critical variables (pricing, deposit) require 2 admin approvals
--          - OR 1 super admin can bypass (god mode)
--          - Supports scheduled changes with effective_from dates
-- =====================================================

BEGIN;

-- =====================================================
-- 1. PENDING VARIABLE APPROVALS TABLE
-- =====================================================
-- Stores pending changes awaiting approval
-- Critical variables require 2 admin approvals OR 1 super admin

CREATE TABLE IF NOT EXISTS public.pending_variable_approvals (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- What's being changed
    variable_id UUID REFERENCES public.dynamic_variables(id) ON DELETE CASCADE,
    category VARCHAR(50) NOT NULL,           -- For new variables (no existing ID)
    key VARCHAR(100) NOT NULL,

    -- Proposed change
    current_value JSONB,                     -- Current value (null for new variables)
    proposed_value JSONB NOT NULL,           -- New value being proposed
    change_type VARCHAR(20) NOT NULL,        -- 'create', 'update', 'delete'
    change_reason TEXT,                      -- Why the change is needed

    -- Scheduling (for future-dated changes)
    effective_from TIMESTAMPTZ,              -- When change should take effect
    effective_to TIMESTAMPTZ,                -- When value expires (optional)

    -- Request details
    requested_by UUID NOT NULL,              -- Admin who initiated the change
    requested_by_email VARCHAR(255),         -- Denormalized for display
    requested_at TIMESTAMPTZ DEFAULT NOW(),

    -- Approval status
    status VARCHAR(20) DEFAULT 'pending' CHECK (
        status IN ('pending', 'approved', 'rejected', 'auto_approved', 'expired', 'applied')
    ),

    -- Approval tracking
    approvals_required INT DEFAULT 2,        -- How many approvals needed (2 for critical)
    approvals_received INT DEFAULT 0,        -- How many approvals received so far

    -- Expiration (auto-reject if not approved in time)
    expires_at TIMESTAMPTZ DEFAULT (NOW() + INTERVAL '7 days'),

    -- Audit
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_pending_approvals_status
    ON public.pending_variable_approvals(status);
CREATE INDEX IF NOT EXISTS idx_pending_approvals_category
    ON public.pending_variable_approvals(category);
CREATE INDEX IF NOT EXISTS idx_pending_approvals_requested_by
    ON public.pending_variable_approvals(requested_by);
CREATE INDEX IF NOT EXISTS idx_pending_approvals_expires
    ON public.pending_variable_approvals(expires_at)
    WHERE status = 'pending';

-- Comments
COMMENT ON TABLE public.pending_variable_approvals IS
    'Queue for variable changes awaiting approval. Critical changes need 2 admins or 1 super admin.';


-- =====================================================
-- 2. VARIABLE APPROVAL ACTIONS TABLE
-- =====================================================
-- Tracks each approval/rejection action on a pending change

CREATE TABLE IF NOT EXISTS public.variable_approval_actions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Reference to pending approval
    pending_approval_id UUID NOT NULL
        REFERENCES public.pending_variable_approvals(id) ON DELETE CASCADE,

    -- Who took action
    actor_id UUID NOT NULL,
    actor_email VARCHAR(255),
    actor_role VARCHAR(50) NOT NULL,         -- 'admin', 'super_admin'

    -- What action was taken
    action VARCHAR(20) NOT NULL CHECK (
        action IN ('approve', 'reject', 'cancel')
    ),
    comment TEXT,                            -- Optional comment explaining decision

    -- When
    acted_at TIMESTAMPTZ DEFAULT NOW(),

    -- Request context
    ip_address INET,
    user_agent TEXT
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_approval_actions_pending
    ON public.variable_approval_actions(pending_approval_id);
CREATE INDEX IF NOT EXISTS idx_approval_actions_actor
    ON public.variable_approval_actions(actor_id);

-- Comments
COMMENT ON TABLE public.variable_approval_actions IS
    'Tracks each approval/rejection action. Super admin = instant approval.';


-- =====================================================
-- 3. CRITICAL VARIABLES CONFIGURATION
-- =====================================================
-- Defines which categories/keys require multi-person approval

CREATE TABLE IF NOT EXISTS public.critical_variable_config (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Matching rules (use * for wildcard)
    category_pattern VARCHAR(50) NOT NULL,   -- 'pricing', 'deposit', or '*'
    key_pattern VARCHAR(100) DEFAULT '*',    -- Specific key or '*' for all

    -- Approval requirements
    approvals_required INT DEFAULT 2,        -- How many admin approvals needed
    super_admin_can_bypass BOOLEAN DEFAULT true, -- Super admin = god mode

    -- Optional: Only require approval for changes above threshold
    value_threshold DECIMAL,                 -- e.g., require approval if change > $100

    -- Status
    is_active BOOLEAN DEFAULT true,

    -- Audit
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    created_by UUID
);

-- Insert default critical variable rules
INSERT INTO public.critical_variable_config (category_pattern, key_pattern, approvals_required, super_admin_can_bypass)
VALUES
    ('pricing', '*', 2, true),      -- All pricing changes need 2 approvals
    ('deposit', '*', 2, true),      -- All deposit changes need 2 approvals
    ('travel', 'travel_per_mile_cents', 2, true),  -- Per-mile rate is critical
    ('booking', 'party_minimum_cents', 2, true)    -- Party minimum is critical
ON CONFLICT DO NOTHING;

-- Index
CREATE INDEX IF NOT EXISTS idx_critical_config_category
    ON public.critical_variable_config(category_pattern, key_pattern);

-- Comments
COMMENT ON TABLE public.critical_variable_config IS
    'Defines which variables require multi-person approval before changes apply.';


-- =====================================================
-- 4. VIEW: PENDING APPROVALS WITH DETAILS
-- =====================================================

CREATE OR REPLACE VIEW public.v_pending_approvals AS
SELECT
    pa.id,
    pa.variable_id,
    pa.category,
    pa.key,
    pa.current_value,
    pa.proposed_value,
    pa.change_type,
    pa.change_reason,
    pa.effective_from,
    pa.effective_to,
    pa.requested_by,
    pa.requested_by_email,
    pa.requested_at,
    pa.status,
    pa.approvals_required,
    pa.approvals_received,
    pa.expires_at,
    -- Calculate if approval threshold is met
    (pa.approvals_received >= pa.approvals_required) AS is_fully_approved,
    -- Time until expiration
    (pa.expires_at - NOW()) AS time_until_expiry,
    -- List of approvers
    (
        SELECT json_agg(json_build_object(
            'actor_email', aa.actor_email,
            'action', aa.action,
            'comment', aa.comment,
            'acted_at', aa.acted_at
        ) ORDER BY aa.acted_at)
        FROM public.variable_approval_actions aa
        WHERE aa.pending_approval_id = pa.id
    ) AS approval_history
FROM public.pending_variable_approvals pa
WHERE pa.status = 'pending';

COMMENT ON VIEW public.v_pending_approvals IS
    'View of pending approvals with approval history and status calculations.';


-- =====================================================
-- 5. FUNCTION: CHECK IF VARIABLE IS CRITICAL
-- =====================================================

CREATE OR REPLACE FUNCTION public.is_critical_variable(
    p_category VARCHAR,
    p_key VARCHAR
) RETURNS TABLE (
    is_critical BOOLEAN,
    approvals_required INT,
    super_admin_can_bypass BOOLEAN
) AS $$
BEGIN
    RETURN QUERY
    SELECT
        true AS is_critical,
        cvc.approvals_required,
        cvc.super_admin_can_bypass
    FROM public.critical_variable_config cvc
    WHERE cvc.is_active = true
      AND (cvc.category_pattern = p_category OR cvc.category_pattern = '*')
      AND (cvc.key_pattern = p_key OR cvc.key_pattern = '*')
    ORDER BY
        -- Most specific match first
        CASE WHEN cvc.category_pattern = p_category AND cvc.key_pattern = p_key THEN 1
             WHEN cvc.category_pattern = p_category AND cvc.key_pattern = '*' THEN 2
             WHEN cvc.category_pattern = '*' AND cvc.key_pattern = p_key THEN 3
             ELSE 4
        END
    LIMIT 1;

    -- If no match, return non-critical (no approval needed)
    IF NOT FOUND THEN
        RETURN QUERY SELECT false, 0, true;
    END IF;
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION public.is_critical_variable IS
    'Check if a variable requires multi-person approval based on category/key patterns.';


-- =====================================================
-- 6. FUNCTION: EXPIRE OLD PENDING APPROVALS
-- =====================================================
-- Can be called by a cron job or on each request

CREATE OR REPLACE FUNCTION public.expire_pending_approvals()
RETURNS INT AS $$
DECLARE
    expired_count INT;
BEGIN
    UPDATE public.pending_variable_approvals
    SET
        status = 'expired',
        updated_at = NOW()
    WHERE status = 'pending'
      AND expires_at < NOW();

    GET DIAGNOSTICS expired_count = ROW_COUNT;
    RETURN expired_count;
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION public.expire_pending_approvals IS
    'Mark pending approvals as expired if past their expiry date.';


-- =====================================================
-- 7. ADD is_critical COLUMN TO DYNAMIC_VARIABLES
-- =====================================================
-- Quick lookup for whether a variable requires approval

ALTER TABLE public.dynamic_variables
ADD COLUMN IF NOT EXISTS requires_approval BOOLEAN DEFAULT false;

-- Update existing critical variables
UPDATE public.dynamic_variables dv
SET requires_approval = true
WHERE EXISTS (
    SELECT 1 FROM public.critical_variable_config cvc
    WHERE cvc.is_active = true
      AND (cvc.category_pattern = dv.category OR cvc.category_pattern = '*')
      AND (cvc.key_pattern = dv.key OR cvc.key_pattern = '*')
);

COMMENT ON COLUMN public.dynamic_variables.requires_approval IS
    'True if changes to this variable require multi-admin approval.';


COMMIT;

-- =====================================================
-- ROLLBACK SCRIPT (if needed)
-- =====================================================
-- DROP VIEW IF EXISTS public.v_pending_approvals;
-- DROP FUNCTION IF EXISTS public.is_critical_variable;
-- DROP FUNCTION IF EXISTS public.expire_pending_approvals;
-- DROP TABLE IF EXISTS public.variable_approval_actions;
-- DROP TABLE IF EXISTS public.pending_variable_approvals;
-- DROP TABLE IF EXISTS public.critical_variable_config;
-- ALTER TABLE public.dynamic_variables DROP COLUMN IF EXISTS requires_approval;
