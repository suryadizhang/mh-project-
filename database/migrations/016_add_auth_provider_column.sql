-- =====================================================
-- Migration: Add auth_provider column to identity.users
-- Created: 2026-01-16
-- Purpose: Fix SQLAlchemy model mismatch - auth_provider column missing from production
-- Root Cause: Column was added to model but migration never ran
-- =====================================================

BEGIN;

-- Step 1: Create the enum type if it doesn't exist
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'authprovider') THEN
        CREATE TYPE public.authprovider AS ENUM ('google', 'facebook', 'instagram', 'email');
        RAISE NOTICE 'Created authprovider enum type';
    END IF;
END $$;

-- Step 2: Add auth_provider column if it doesn't exist
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_schema = 'identity'
        AND table_name = 'users'
        AND column_name = 'auth_provider'
    ) THEN
        ALTER TABLE identity.users 
        ADD COLUMN auth_provider public.authprovider NOT NULL DEFAULT 'email';
        RAISE NOTICE 'Added auth_provider column to identity.users';
    ELSE
        RAISE NOTICE 'auth_provider column already exists';
    END IF;
END $$;

-- Step 3: Add comment for documentation
COMMENT ON COLUMN identity.users.auth_provider IS 'OAuth provider used for authentication: google, facebook, instagram, or email (default)';

COMMIT;

-- =====================================================
-- ROLLBACK SCRIPT (keep as comment for emergency):
-- =====================================================
-- ALTER TABLE identity.users DROP COLUMN IF EXISTS auth_provider;
-- DROP TYPE IF EXISTS public.authprovider;
