-- ============================================
-- Login History & IP Monitoring Tables
-- Run this on production database
-- ============================================

-- Login history table (stores ALL logins)
CREATE TABLE IF NOT EXISTS security.login_history (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES identity.users(id) ON DELETE CASCADE,
    email VARCHAR(255) NOT NULL,
    ip_address VARCHAR(45) NOT NULL,  -- Supports IPv6
    user_agent TEXT,
    device_fingerprint VARCHAR(64),   -- Hash of device characteristics

    -- Device info (parsed from user agent)
    browser VARCHAR(50),
    os VARCHAR(50),
    device_type VARCHAR(20),  -- desktop, mobile, tablet

    -- Geolocation data (from IP lookup)
    country VARCHAR(100),
    country_code VARCHAR(3),
    region VARCHAR(100),
    city VARCHAR(100),
    latitude DECIMAL(10, 7),
    longitude DECIMAL(10, 7),
    timezone VARCHAR(50),
    isp VARCHAR(255),

    -- Risk assessment
    is_new_ip BOOLEAN DEFAULT FALSE,
    is_new_device BOOLEAN DEFAULT FALSE,
    is_suspicious BOOLEAN DEFAULT FALSE,
    success BOOLEAN DEFAULT TRUE,  -- Was the login successful
    risk_score INTEGER DEFAULT 0,  -- 0-100
    risk_factors JSONB DEFAULT '[]'::jsonb,

    -- Timestamps
    login_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

    -- For tracking known IPs per user
    is_trusted BOOLEAN DEFAULT FALSE,  -- User/admin marked as trusted

    -- Alert references
    alert_id UUID REFERENCES security.admin_alerts(id) ON DELETE SET NULL
);

-- Known IPs per user (for detecting new IPs)
CREATE TABLE IF NOT EXISTS security.known_user_ips (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES identity.users(id) ON DELETE CASCADE,
    ip_address VARCHAR(45) NOT NULL,
    first_seen TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    last_seen TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    login_count INTEGER DEFAULT 1,
    country VARCHAR(100),
    city VARCHAR(100),
    is_trusted BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

    UNIQUE(user_id, ip_address)
);

-- IP reputation cache (for bad IP detection)
CREATE TABLE IF NOT EXISTS security.ip_reputation_cache (
    ip_address VARCHAR(45) PRIMARY KEY,
    reputation_score INTEGER DEFAULT 50,  -- 0=bad, 50=neutral, 100=good
    is_vpn BOOLEAN DEFAULT FALSE,
    is_proxy BOOLEAN DEFAULT FALSE,
    is_tor BOOLEAN DEFAULT FALSE,
    is_datacenter BOOLEAN DEFAULT FALSE,
    threat_types JSONB DEFAULT '[]'::jsonb,
    country_code VARCHAR(3),
    last_checked TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    expires_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() + INTERVAL '7 days'
);

-- Indexes for efficient queries
CREATE INDEX IF NOT EXISTS idx_login_history_user_id ON security.login_history(user_id);
CREATE INDEX IF NOT EXISTS idx_login_history_ip_address ON security.login_history(ip_address);
CREATE INDEX IF NOT EXISTS idx_login_history_login_at ON security.login_history(login_at DESC);
CREATE INDEX IF NOT EXISTS idx_login_history_email ON security.login_history(email);
CREATE INDEX IF NOT EXISTS idx_login_history_suspicious ON security.login_history(is_suspicious) WHERE is_suspicious = TRUE;
CREATE INDEX IF NOT EXISTS idx_login_history_user_time ON security.login_history(user_id, login_at DESC);
CREATE INDEX IF NOT EXISTS idx_login_history_ip_time ON security.login_history(ip_address, login_at DESC);

CREATE INDEX IF NOT EXISTS idx_known_user_ips_user ON security.known_user_ips(user_id);
CREATE INDEX IF NOT EXISTS idx_known_user_ips_ip ON security.known_user_ips(ip_address);

CREATE INDEX IF NOT EXISTS idx_ip_reputation_expires ON security.ip_reputation_cache(expires_at);

-- Add new event types to support IP monitoring
-- (These are just string values, no enum alteration needed)

-- View for recent suspicious logins
CREATE OR REPLACE VIEW security.v_suspicious_logins AS
SELECT
    lh.id,
    lh.user_id,
    lh.email,
    lh.ip_address,
    lh.city,
    lh.country,
    lh.is_new_ip,
    lh.is_new_device,
    lh.risk_score,
    lh.risk_factors,
    lh.login_at,
    lh.user_agent
FROM security.login_history lh
WHERE lh.is_suspicious = TRUE
  AND lh.login_at > NOW() - INTERVAL '7 days'
ORDER BY lh.login_at DESC;

-- View for geo-impossible travel detection
CREATE OR REPLACE VIEW security.v_potential_geo_violations AS
SELECT
    l1.user_id,
    l1.email,
    l1.ip_address AS ip_1,
    l1.city AS city_1,
    l1.country AS country_1,
    l1.latitude AS lat_1,
    l1.longitude AS lon_1,
    l1.login_at AS login_1,
    l2.ip_address AS ip_2,
    l2.city AS city_2,
    l2.country AS country_2,
    l2.latitude AS lat_2,
    l2.longitude AS lon_2,
    l2.login_at AS login_2,
    EXTRACT(EPOCH FROM (l2.login_at - l1.login_at)) / 60 AS minutes_between,
    -- Haversine distance calculation (approximate)
    (6371 * acos(
        LEAST(1.0, GREATEST(-1.0,
            cos(radians(l1.latitude)) * cos(radians(l2.latitude)) *
            cos(radians(l2.longitude) - radians(l1.longitude)) +
            sin(radians(l1.latitude)) * sin(radians(l2.latitude))
        ))
    )) AS distance_km
FROM security.login_history l1
JOIN security.login_history l2 ON l1.user_id = l2.user_id
    AND l2.login_at > l1.login_at
    AND l2.login_at < l1.login_at + INTERVAL '2 hours'
    AND l1.ip_address != l2.ip_address
WHERE l1.login_at > NOW() - INTERVAL '24 hours'
  AND l1.latitude IS NOT NULL
  AND l2.latitude IS NOT NULL;

-- Function to check if an IP is new for a user
CREATE OR REPLACE FUNCTION security.is_new_ip_for_user(
    p_user_id UUID,
    p_ip_address VARCHAR(45)
) RETURNS BOOLEAN AS $$
BEGIN
    RETURN NOT EXISTS (
        SELECT 1 FROM security.known_user_ips
        WHERE user_id = p_user_id AND ip_address = p_ip_address
    );
END;
$$ LANGUAGE plpgsql;

-- Function to count new IPs in last 24 hours for a user
CREATE OR REPLACE FUNCTION security.count_new_ips_24h(
    p_user_id UUID
) RETURNS INTEGER AS $$
BEGIN
    RETURN (
        SELECT COUNT(DISTINCT ip_address)
        FROM security.login_history
        WHERE user_id = p_user_id
          AND is_new_ip = TRUE
          AND login_at > NOW() - INTERVAL '24 hours'
    );
END;
$$ LANGUAGE plpgsql;

-- Function to check if same IP hit multiple accounts
CREATE OR REPLACE FUNCTION security.ip_accounts_count_1h(
    p_ip_address VARCHAR(45)
) RETURNS INTEGER AS $$
BEGIN
    RETURN (
        SELECT COUNT(DISTINCT user_id)
        FROM security.login_history
        WHERE ip_address = p_ip_address
          AND login_at > NOW() - INTERVAL '1 hour'
    );
END;
$$ LANGUAGE plpgsql;

COMMENT ON TABLE security.login_history IS 'Comprehensive log of all login attempts with geolocation and risk assessment';
COMMENT ON TABLE security.known_user_ips IS 'Tracks known IPs per user for new IP detection';
COMMENT ON TABLE security.ip_reputation_cache IS 'Cached IP reputation data from external services';
