-- =====================================================
-- Migration: Create token_blacklist table for JTI verification
-- Created: 2025-01-30
-- Purpose: Secure token invalidation for logout, password change, session revocation
-- Depends on: 007_create_user_sessions.sql
-- =====================================================

BEGIN;

-- Create token_blacklist table in identity schema
-- This table stores invalidated token JTIs for verification on every request
-- Uses TTL-based cleanup - tokens are removed after their original expiry
CREATE TABLE IF NOT EXISTS identity.token_blacklist (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    
    -- Token identification
    jti VARCHAR(36) NOT NULL UNIQUE,                          -- JWT ID (unique per token)
    token_type VARCHAR(20) NOT NULL CHECK (token_type IN ('access', 'refresh')),
    
    -- Association
    user_id UUID REFERENCES identity.users(id) ON DELETE SET NULL,  -- Nullable for cleanup
    session_id UUID REFERENCES identity.user_sessions(id) ON DELETE SET NULL,
    
    -- Blacklist metadata
    blacklisted_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    expires_at TIMESTAMPTZ NOT NULL,                          -- Token's original expiry (for cleanup)
    reason VARCHAR(100) NOT NULL DEFAULT 'logout',            -- 'logout', 'password_change', 'session_revoked', 'security_violation'
    
    -- Audit
    created_by UUID REFERENCES identity.users(id) ON DELETE SET NULL  -- Who triggered the blacklist
);

-- Add comment
COMMENT ON TABLE identity.token_blacklist IS 
    'Blacklisted JWT tokens for logout, password change, and security violations. Tokens removed after expiry.';

-- Index for fast JTI lookup (primary use case)
CREATE INDEX IF NOT EXISTS idx_token_blacklist_jti 
    ON identity.token_blacklist(jti);

-- Index for cleanup job (remove expired entries)
CREATE INDEX IF NOT EXISTS idx_token_blacklist_expires 
    ON identity.token_blacklist(expires_at);

-- Index for user session revocation
CREATE INDEX IF NOT EXISTS idx_token_blacklist_user_id 
    ON identity.token_blacklist(user_id);

-- Create password_reset_tokens table for secure password reset flow
CREATE TABLE IF NOT EXISTS identity.password_reset_tokens (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    
    -- Token data
    user_id UUID NOT NULL REFERENCES identity.users(id) ON DELETE CASCADE,
    token_hash VARCHAR(100) NOT NULL UNIQUE,                  -- SHA-256 hash of reset token
    
    -- Status and expiry
    expires_at TIMESTAMPTZ NOT NULL,                          -- 1 hour from creation
    used_at TIMESTAMPTZ,                                      -- When token was used (NULL = unused)
    
    -- Security tracking
    requested_ip VARCHAR(45),                                 -- IP that requested reset
    used_ip VARCHAR(45),                                      -- IP that used token
    
    -- Timestamps
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Add comment
COMMENT ON TABLE identity.password_reset_tokens IS 
    'Secure password reset tokens with 1-hour expiry. Single-use only.';

-- Index for fast token lookup
CREATE INDEX IF NOT EXISTS idx_password_reset_token_hash 
    ON identity.password_reset_tokens(token_hash);

-- Index for user lookup (limit 3 requests per hour)
CREATE INDEX IF NOT EXISTS idx_password_reset_user 
    ON identity.password_reset_tokens(user_id, created_at DESC);

-- Index for cleanup
CREATE INDEX IF NOT EXISTS idx_password_reset_expires 
    ON identity.password_reset_tokens(expires_at);

-- Grant permissions to application role
DO $$
BEGIN
    -- Grant permissions if the role exists
    IF EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'myhibachi_user') THEN
        GRANT SELECT, INSERT, UPDATE, DELETE ON identity.token_blacklist TO myhibachi_user;
        GRANT SELECT, INSERT, UPDATE, DELETE ON identity.password_reset_tokens TO myhibachi_user;
        RAISE NOTICE 'Granted permissions to myhibachi_user';
    END IF;
    
    IF EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'myhibachi_staging_user') THEN
        GRANT SELECT, INSERT, UPDATE, DELETE ON identity.token_blacklist TO myhibachi_staging_user;
        GRANT SELECT, INSERT, UPDATE, DELETE ON identity.password_reset_tokens TO myhibachi_staging_user;
        RAISE NOTICE 'Granted permissions to myhibachi_staging_user';
    END IF;
END $$;

-- Verify tables created
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_schema='identity' AND table_name='token_blacklist') THEN
        RAISE NOTICE '✅ identity.token_blacklist created successfully';
    END IF;
    
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_schema='identity' AND table_name='password_reset_tokens') THEN
        RAISE NOTICE '✅ identity.password_reset_tokens created successfully';
    END IF;
END $$;

COMMIT;

-- =====================================================
-- ROLLBACK SCRIPT (keep as comment for emergency):
-- =====================================================
-- DROP TABLE IF EXISTS identity.token_blacklist;
-- DROP TABLE IF EXISTS identity.password_reset_tokens;
