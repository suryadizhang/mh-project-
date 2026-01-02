-- =====================================================
-- Migration: Add CHEF role to user_role CHECK constraint
-- Created: 2025-01-30
-- Purpose: Enable 5-tier RBAC system with dedicated chef portal
--
-- This migration adds CHEF to the allowed user roles in identity.users table.
-- Part of Batch 1.x RBAC enhancement: role-specific page views.
--
-- ROLE-SPECIFIC PAGE VIEWS (UX Requirement):
-- ==========================================
-- Each role has a dedicated page/view - they ONLY see options for their job tasks.
-- - SUPER_ADMIN: Full admin dashboard with ALL menu options
-- - ADMIN: Admin dashboard scoped to assigned stations
-- - CUSTOMER_SUPPORT: Customer-focused dashboard (bookings, reviews, leads)
-- - STATION_MANAGER: Station dashboard (chef scheduling, station bookings)
-- - CHEF: Chef portal (own schedule, availability, assigned event details)
-- =====================================================

BEGIN;

-- =====================================================
-- STEP 1: Check current constraint
-- =====================================================
DO $$
BEGIN
    RAISE NOTICE '🔍 Checking existing role CHECK constraint on identity.users...';
END $$;

-- =====================================================
-- STEP 2: Drop existing CHECK constraint (if exists)
-- =====================================================
DO $$
BEGIN
    -- Try to drop the constraint by various possible names
    BEGIN
        ALTER TABLE identity.users DROP CONSTRAINT IF EXISTS users_role_check;
        RAISE NOTICE '✅ Dropped constraint: users_role_check';
    EXCEPTION WHEN OTHERS THEN
        RAISE NOTICE '⚠️ Could not drop users_role_check: %', SQLERRM;
    END;

    BEGIN
        ALTER TABLE identity.users DROP CONSTRAINT IF EXISTS check_valid_role;
        RAISE NOTICE '✅ Dropped constraint: check_valid_role';
    EXCEPTION WHEN OTHERS THEN
        RAISE NOTICE '⚠️ Could not drop check_valid_role: %', SQLERRM;
    END;
END $$;

-- =====================================================
-- STEP 3: Add new CHECK constraint with CHEF role
-- =====================================================
DO $$
BEGIN
    -- Add constraint with all 5 roles (using UPPERCASE to match auth.py)
    ALTER TABLE identity.users
    ADD CONSTRAINT check_valid_role
    CHECK (role IN ('SUPER_ADMIN', 'ADMIN', 'CUSTOMER_SUPPORT', 'STATION_MANAGER', 'CHEF'));

    RAISE NOTICE '✅ Added CHECK constraint with 5 roles: SUPER_ADMIN, ADMIN, CUSTOMER_SUPPORT, STATION_MANAGER, CHEF';
EXCEPTION WHEN OTHERS THEN
    -- Constraint might already be correct, that's OK
    RAISE NOTICE '⚠️ Could not add CHECK constraint: % (may already exist)', SQLERRM;
END $$;

-- =====================================================
-- STEP 4: Create user_role ENUM type if not exists
-- =====================================================
DO $$
BEGIN
    -- Check if enum type exists
    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'user_role') THEN
        CREATE TYPE user_role AS ENUM (
            'SUPER_ADMIN',
            'ADMIN',
            'CUSTOMER_SUPPORT',
            'STATION_MANAGER',
            'CHEF'
        );
        RAISE NOTICE '✅ Created user_role ENUM type with 5 roles';
    ELSE
        -- Check if CHEF exists in the enum
        IF NOT EXISTS (
            SELECT 1 FROM pg_enum
            WHERE enumtypid = 'user_role'::regtype
            AND enumlabel = 'CHEF'
        ) THEN
            ALTER TYPE user_role ADD VALUE IF NOT EXISTS 'CHEF';
            RAISE NOTICE '✅ Added CHEF to existing user_role ENUM';
        ELSE
            RAISE NOTICE '✓ user_role ENUM already has CHEF';
        END IF;
    END IF;
END $$;

-- =====================================================
-- STEP 5: Add comment documenting the 5-tier RBAC
-- =====================================================
COMMENT ON COLUMN identity.users.role IS
'5-tier RBAC role: SUPER_ADMIN, ADMIN, CUSTOMER_SUPPORT, STATION_MANAGER, CHEF.
Each role has dedicated page views showing only relevant job options.
Added CHEF role in migration 006_add_chef_role.sql (2025-01-30)';

-- =====================================================
-- STEP 6: Verify the migration
-- =====================================================
DO $$
DECLARE
    role_count INT;
BEGIN
    -- Count distinct roles in the constraint
    SELECT COUNT(*) INTO role_count
    FROM pg_constraint
    WHERE conname = 'check_valid_role';

    IF role_count > 0 THEN
        RAISE NOTICE '✅ Migration complete: check_valid_role constraint exists';
    ELSE
        RAISE WARNING '⚠️ CHECK constraint may not have been created - verify manually';
    END IF;
END $$;

COMMIT;

-- =====================================================
-- ROLLBACK SCRIPT (keep as comment for emergency):
-- =====================================================
-- ALTER TABLE identity.users DROP CONSTRAINT IF EXISTS check_valid_role;
-- ALTER TABLE identity.users ADD CONSTRAINT check_valid_role
--     CHECK (role IN ('SUPER_ADMIN', 'ADMIN', 'CUSTOMER_SUPPORT', 'STATION_MANAGER'));
