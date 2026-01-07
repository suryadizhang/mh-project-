-- =====================================================
-- Migration: Add OAuth Columns to identity.users
-- Created: 2025-01-30
-- Purpose: Add OAuth provider columns to support Google, Microsoft, Apple login
-- Author: My Hibachi Dev Team
-- =====================================================
--
-- CONTEXT:
-- The User model in apps/backend/src/db/models/identity/users.py defines OAuth columns
-- (google_id, microsoft_id, apple_id, auth_provider, full_name, is_email_verified, is_super_admin)
-- but these columns don't exist in the production database, causing SQLAlchemy errors
-- when trying to access these attributes.
--
-- ERROR FIXED:
-- "type object 'User' has no attribute 'google_id'" on staging Google OAuth login
--
-- CURRENT OAUTH STATUS:
-- - ACTIVE: Google OAuth (used for admin login via GoogleOAuthAccount table)
-- - FUTURE: Microsoft OAuth (columns ready, not implemented yet)
-- - FUTURE: Apple OAuth (columns ready, not implemented yet)
--
-- ROLLBACK:
-- ALTER TABLE identity.users DROP COLUMN IF EXISTS google_id;
-- ALTER TABLE identity.users DROP COLUMN IF EXISTS microsoft_id;
-- ALTER TABLE identity.users DROP COLUMN IF EXISTS apple_id;
-- ALTER TABLE identity.users DROP COLUMN IF EXISTS auth_provider;
-- ALTER TABLE identity.users DROP COLUMN IF EXISTS full_name;
-- ALTER TABLE identity.users DROP COLUMN IF EXISTS is_email_verified;
-- ALTER TABLE identity.users DROP COLUMN IF EXISTS is_super_admin;
-- DROP TYPE IF EXISTS public.authprovider;
-- =====================================================

BEGIN;

-- 1. Create auth_provider enum type if it doesn't exist
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'authprovider' AND typnamespace = 'public'::regnamespace) THEN
        CREATE TYPE public.authprovider AS ENUM ('google', 'facebook', 'instagram', 'email');
        RAISE NOTICE 'Created authprovider enum type';
    ELSE
        RAISE NOTICE 'authprovider enum type already exists';
    END IF;
END $$;

-- 2. Add OAuth ID columns (for direct social login linking)
DO $$
BEGIN
    -- Google ID (PRIMARY - currently active for admin Google OAuth)
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_schema = 'identity' AND table_name = 'users' AND column_name = 'google_id'
    ) THEN
        ALTER TABLE identity.users ADD COLUMN google_id VARCHAR(255);
        CREATE INDEX IF NOT EXISTS idx_users_google_id ON identity.users(google_id);
        RAISE NOTICE 'Added google_id column with index';
    END IF;

    -- Microsoft ID (FUTURE - ready for Microsoft OAuth integration)
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_schema = 'identity' AND table_name = 'users' AND column_name = 'microsoft_id'
    ) THEN
        ALTER TABLE identity.users ADD COLUMN microsoft_id VARCHAR(255);
        RAISE NOTICE 'Added microsoft_id column';
    END IF;

    -- Apple ID (FUTURE - ready for Apple Sign-In integration)
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_schema = 'identity' AND table_name = 'users' AND column_name = 'apple_id'
    ) THEN
        ALTER TABLE identity.users ADD COLUMN apple_id VARCHAR(255);
        RAISE NOTICE 'Added apple_id column';
    END IF;
END $$;

-- 3. Add auth_provider column to track primary authentication method
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_schema = 'identity' AND table_name = 'users' AND column_name = 'auth_provider'
    ) THEN
        ALTER TABLE identity.users ADD COLUMN auth_provider public.authprovider DEFAULT 'email';
        RAISE NOTICE 'Added auth_provider column with default EMAIL';
    END IF;
END $$;

-- 4. Add full_name column (computed display name from OAuth profile)
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_schema = 'identity' AND table_name = 'users' AND column_name = 'full_name'
    ) THEN
        ALTER TABLE identity.users ADD COLUMN full_name VARCHAR(255);
        RAISE NOTICE 'Added full_name column';
    END IF;
END $$;

-- 5. Add is_email_verified column (separate from is_verified for granular control)
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_schema = 'identity' AND table_name = 'users' AND column_name = 'is_email_verified'
    ) THEN
        ALTER TABLE identity.users ADD COLUMN is_email_verified BOOLEAN NOT NULL DEFAULT false;
        RAISE NOTICE 'Added is_email_verified column with default false';
    END IF;
END $$;

-- 6. Add is_super_admin column (denormalized flag for quick access checks)
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_schema = 'identity' AND table_name = 'users' AND column_name = 'is_super_admin'
    ) THEN
        ALTER TABLE identity.users ADD COLUMN is_super_admin BOOLEAN NOT NULL DEFAULT false;
        RAISE NOTICE 'Added is_super_admin column with default false';
    END IF;
END $$;

-- 7. Add comments for documentation
COMMENT ON COLUMN identity.users.google_id IS 'Google OAuth subject ID (sub claim). Primary OAuth provider for admin accounts.';
COMMENT ON COLUMN identity.users.microsoft_id IS 'Microsoft OAuth subject ID. FUTURE: For Microsoft login integration.';
COMMENT ON COLUMN identity.users.apple_id IS 'Apple Sign-In user ID. FUTURE: For Apple login integration.';
COMMENT ON COLUMN identity.users.auth_provider IS 'Primary authentication provider used by this user.';
COMMENT ON COLUMN identity.users.full_name IS 'Full display name from OAuth profile or manually set.';
COMMENT ON COLUMN identity.users.is_email_verified IS 'Email verification status (separate from is_verified for granular control).';
COMMENT ON COLUMN identity.users.is_super_admin IS 'Quick access flag for super admin check (denormalized from user_roles for performance).';

COMMIT;

-- =====================================================
-- VERIFICATION QUERIES (run after migration):
-- =====================================================
-- Check columns exist:
-- SELECT column_name, data_type, is_nullable, column_default
-- FROM information_schema.columns
-- WHERE table_schema = 'identity' AND table_name = 'users'
-- AND column_name IN ('google_id', 'microsoft_id', 'apple_id', 'auth_provider', 'full_name', 'is_email_verified', 'is_super_admin');
--
-- Check enum exists:
-- SELECT typname, enumlabel FROM pg_enum
-- JOIN pg_type ON pg_type.oid = pg_enum.enumtypid
-- WHERE typname = 'authprovider';
-- =====================================================
