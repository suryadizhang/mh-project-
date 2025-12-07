-- Security Monitoring Tables Migration
-- Run this after adding MFA columns

-- Create security schema if not exists
CREATE SCHEMA IF NOT EXISTS security;

-- ============================================
-- Security Events Table (Audit Log)
-- ============================================
CREATE TABLE IF NOT EXISTS security.security_events (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    event_type VARCHAR(50) NOT NULL,
    user_id UUID REFERENCES identity.users(id) ON DELETE SET NULL,
    email VARCHAR(255),
    ip_address VARCHAR(45),  -- IPv6 compatible
    user_agent TEXT,
    details JSONB DEFAULT '{}',
    severity VARCHAR(20) DEFAULT 'low',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Indexes for security_events
CREATE INDEX IF NOT EXISTS idx_security_events_user_id ON security.security_events(user_id);
CREATE INDEX IF NOT EXISTS idx_security_events_email ON security.security_events(email);
CREATE INDEX IF NOT EXISTS idx_security_events_ip_address ON security.security_events(ip_address);
CREATE INDEX IF NOT EXISTS idx_security_events_event_type ON security.security_events(event_type);
CREATE INDEX IF NOT EXISTS idx_security_events_created_at ON security.security_events(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_security_events_severity ON security.security_events(severity);

-- Composite index for brute force detection
CREATE INDEX IF NOT EXISTS idx_security_events_ip_type_time
ON security.security_events(ip_address, event_type, created_at DESC);

-- ============================================
-- Admin Alerts Table (Dashboard Notifications)
-- ============================================
CREATE TABLE IF NOT EXISTS security.admin_alerts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    title VARCHAR(255) NOT NULL,
    message TEXT NOT NULL,
    severity VARCHAR(20) NOT NULL DEFAULT 'low',
    event_type VARCHAR(50) NOT NULL,
    user_id UUID REFERENCES identity.users(id) ON DELETE SET NULL,
    email VARCHAR(255),
    ip_address VARCHAR(45),
    requires_action BOOLEAN DEFAULT FALSE,
    action_url VARCHAR(500),
    status VARCHAR(20) DEFAULT 'new',
    resolved_by UUID REFERENCES identity.users(id) ON DELETE SET NULL,
    resolved_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Indexes for admin_alerts
CREATE INDEX IF NOT EXISTS idx_admin_alerts_status ON security.admin_alerts(status);
CREATE INDEX IF NOT EXISTS idx_admin_alerts_severity ON security.admin_alerts(severity);
CREATE INDEX IF NOT EXISTS idx_admin_alerts_created_at ON security.admin_alerts(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_admin_alerts_requires_action ON security.admin_alerts(requires_action) WHERE requires_action = true;

-- ============================================
-- Blocked IPs Table (For rate limiting/blocking)
-- ============================================
CREATE TABLE IF NOT EXISTS security.blocked_ips (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    ip_address VARCHAR(45) NOT NULL UNIQUE,
    reason VARCHAR(255) NOT NULL,
    blocked_by UUID REFERENCES identity.users(id) ON DELETE SET NULL,
    blocked_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    expires_at TIMESTAMP WITH TIME ZONE,  -- NULL = permanent
    is_active BOOLEAN DEFAULT TRUE,
    notes TEXT
);

CREATE INDEX IF NOT EXISTS idx_blocked_ips_address ON security.blocked_ips(ip_address);
CREATE INDEX IF NOT EXISTS idx_blocked_ips_active ON security.blocked_ips(is_active) WHERE is_active = true;

-- ============================================
-- Add lockout_count column to identity.users for progressive lockout
-- ============================================
ALTER TABLE identity.users
ADD COLUMN IF NOT EXISTS lockout_count INTEGER DEFAULT 0;

ALTER TABLE identity.users
ADD COLUMN IF NOT EXISTS last_lockout_at TIMESTAMP WITH TIME ZONE;

ALTER TABLE identity.users
ADD COLUMN IF NOT EXISTS is_security_disabled BOOLEAN DEFAULT FALSE;

-- ============================================
-- Create view for active security alerts (for dashboard)
-- ============================================
CREATE OR REPLACE VIEW security.active_alerts AS
SELECT
    a.*,
    u.email as target_user_email,
    u.first_name || ' ' || u.last_name as target_user_name
FROM security.admin_alerts a
LEFT JOIN identity.users u ON a.user_id = u.id
WHERE a.status IN ('new', 'acknowledged')
ORDER BY
    CASE a.severity
        WHEN 'critical' THEN 1
        WHEN 'high' THEN 2
        WHEN 'medium' THEN 3
        ELSE 4
    END,
    a.created_at DESC;

-- ============================================
-- Create view for security dashboard stats
-- ============================================
CREATE OR REPLACE VIEW security.dashboard_stats AS
SELECT
    (SELECT COUNT(*) FROM security.admin_alerts WHERE status = 'new') as new_alerts,
    (SELECT COUNT(*) FROM security.admin_alerts WHERE status = 'new' AND severity = 'critical') as critical_alerts,
    (SELECT COUNT(*) FROM security.security_events WHERE created_at > NOW() - INTERVAL '24 hours') as events_24h,
    (SELECT COUNT(*) FROM security.security_events WHERE event_type = 'account_locked' AND created_at > NOW() - INTERVAL '24 hours') as lockouts_24h,
    (SELECT COUNT(*) FROM security.security_events WHERE event_type = 'mfa_failed' AND created_at > NOW() - INTERVAL '24 hours') as failed_mfa_24h,
    (SELECT COUNT(DISTINCT ip_address) FROM security.security_events WHERE event_type IN ('login_failed', 'mfa_failed') AND created_at > NOW() - INTERVAL '1 hour') as suspicious_ips_1h,
    (SELECT COUNT(*) FROM security.blocked_ips WHERE is_active = true) as blocked_ips;

-- ============================================
-- Grant permissions
-- ============================================
GRANT USAGE ON SCHEMA security TO myhibachi_user;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA security TO myhibachi_user;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA security TO myhibachi_user;

-- ============================================
-- Insert sample test alert (can remove after testing)
-- ============================================
-- INSERT INTO security.admin_alerts (title, message, severity, event_type, requires_action)
-- VALUES ('System Started', 'Security monitoring system initialized successfully.', 'low', 'login_success', false);

SELECT 'Security tables created successfully!' as status;
