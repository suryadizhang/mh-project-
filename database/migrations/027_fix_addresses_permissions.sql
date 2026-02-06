-- =====================================================
-- FIX: Grant permissions on core.addresses table
-- Created: 2026-02-05
-- Purpose: Fix "permission denied for table addresses" error
-- Issue: Migration 003 created table but didn't grant permissions
-- =====================================================

-- Grant permissions on core.addresses table to all users
-- Production user
GRANT SELECT, INSERT, UPDATE, DELETE ON core.addresses TO myhibachi_user;

-- Staging user
GRANT SELECT, INSERT, UPDATE, DELETE ON core.addresses TO myhibachi_staging_user;

-- Also grant on any sequences (for potential future auto-increment)
GRANT USAGE ON ALL SEQUENCES IN SCHEMA core TO myhibachi_user;
GRANT USAGE ON ALL SEQUENCES IN SCHEMA core TO myhibachi_staging_user;

-- Ensure default privileges are set for future tables in core schema
ALTER DEFAULT PRIVILEGES IN SCHEMA core GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO myhibachi_user;
ALTER DEFAULT PRIVILEGES IN SCHEMA core GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO myhibachi_staging_user;

-- Verify permissions
SELECT
    grantee,
    table_schema,
    table_name,
    privilege_type
FROM information_schema.table_privileges
WHERE table_schema = 'core'
  AND table_name = 'addresses'
ORDER BY grantee, privilege_type;
