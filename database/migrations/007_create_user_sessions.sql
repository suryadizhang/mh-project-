CREATE TABLE IF NOT EXISTS identity.user_sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES identity.users(id),
    session_token VARCHAR(64) NOT NULL UNIQUE,
    refresh_token_hash VARCHAR(100) NOT NULL UNIQUE,
    access_token_jti VARCHAR(36) NOT NULL UNIQUE,
    refresh_token_jti VARCHAR(36) NOT NULL UNIQUE,
    device_fingerprint VARCHAR(64),
    user_agent TEXT,
    ip_address VARCHAR(45),
    location VARCHAR(100),
    mfa_verified BOOLEAN NOT NULL DEFAULT false,
    mfa_verified_at TIMESTAMPTZ,
    status VARCHAR(20) NOT NULL DEFAULT 'active',
    expires_at TIMESTAMPTZ NOT NULL,
    last_used_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_user_sessions_user_id ON identity.user_sessions(user_id);
CREATE INDEX IF NOT EXISTS idx_user_sessions_session_token ON identity.user_sessions(session_token);
CREATE INDEX IF NOT EXISTS idx_user_sessions_status ON identity.user_sessions(status);
CREATE INDEX IF NOT EXISTS idx_user_sessions_expires_at ON identity.user_sessions(expires_at);

-- Grant permissions to application user
GRANT ALL PRIVILEGES ON TABLE identity.user_sessions TO myhibachi_user;
