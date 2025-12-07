-- Add MFA columns to identity.users table for WebAuthn + PIN authentication
-- Run this on the production database

-- WebAuthn credentials (array of registered authenticators)
ALTER TABLE identity.users
ADD COLUMN IF NOT EXISTS webauthn_credentials JSONB DEFAULT '[]';

-- PIN hash (bcrypt hashed 4-6 digit PIN)
ALTER TABLE identity.users
ADD COLUMN IF NOT EXISTS pin_hash VARCHAR(255);

-- PIN attempt tracking for lockout
ALTER TABLE identity.users
ADD COLUMN IF NOT EXISTS pin_attempts INT DEFAULT 0;

-- PIN lockout timestamp
ALTER TABLE identity.users
ADD COLUMN IF NOT EXISTS pin_locked_until TIMESTAMP WITH TIME ZONE;

-- Whether MFA setup is complete (WebAuthn + PIN both configured)
ALTER TABLE identity.users
ADD COLUMN IF NOT EXISTS mfa_setup_complete BOOLEAN DEFAULT FALSE;

-- When MFA was set up
ALTER TABLE identity.users
ADD COLUMN IF NOT EXISTS mfa_setup_at TIMESTAMP WITH TIME ZONE;

-- Flag to force PIN reset (set by SUPER_ADMIN)
ALTER TABLE identity.users
ADD COLUMN IF NOT EXISTS pin_reset_required BOOLEAN DEFAULT FALSE;

-- Add index for MFA queries
CREATE INDEX IF NOT EXISTS idx_users_mfa_setup ON identity.users(mfa_setup_complete);

-- Verify columns were added
SELECT column_name, data_type, column_default
FROM information_schema.columns
WHERE table_schema = 'identity'
AND table_name = 'users'
AND column_name IN ('webauthn_credentials', 'pin_hash', 'pin_attempts', 'pin_locked_until', 'mfa_setup_complete', 'mfa_setup_at', 'pin_reset_required');
