-- ============================================================================
-- LEAD GENERATION COMPLIANCE & REFERRAL TABLES
-- ============================================================================
-- Purpose: Store consent records and referral tracking for TCPA/CAN-SPAM compliance
-- Created: November 13, 2025
-- ============================================================================

-- ============================================================================
-- CONSENT_RECORDS TABLE
-- ============================================================================
-- Purpose: Full audit trail for TCPA/CAN-SPAM compliance
-- Retention: 7 years (legal requirement)
-- ============================================================================

CREATE TABLE IF NOT EXISTS consent_records (
    id SERIAL PRIMARY KEY,
    
    -- Lead association (nullable for direct newsletter signups)
    lead_id UUID NULL REFERENCES leads(id) ON DELETE SET NULL,
    
    -- Contact information (stored encrypted at application level)
    phone VARCHAR(20) NULL,  -- E.164 format: +15551234567
    email VARCHAR(255) NULL,
    
    -- Consent details
    consent_type VARCHAR(20) NOT NULL CHECK (consent_type IN ('sms', 'email', 'marketing', 'terms')),
    consent_given BOOLEAN NOT NULL DEFAULT TRUE,
    consent_timestamp TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    consent_withdrawn_at TIMESTAMP NULL,
    
    -- Audit trail (TCPA requirement)
    consent_source VARCHAR(50) NOT NULL,  -- 'web_quote', 'exit_intent', 'social_media', 'referral', etc.
    consent_ip_address VARCHAR(45) NULL,  -- IPv4 or IPv6
    consent_user_agent TEXT NULL,
    consent_text TEXT NOT NULL,  -- Exact consent text shown to user
    
    -- Method tracking
    consent_method VARCHAR(20) NOT NULL CHECK (consent_method IN ('checkbox', 'auto_subscribe', 'double_optin', 'sms_reply')),
    consent_form_url VARCHAR(500) NULL,
    
    -- Additional context
    lead_source VARCHAR(50) NULL,
    campaign_id VARCHAR(100) NULL,
    metadata JSONB DEFAULT '{}'::jsonb,
    
    -- Consent-specific flags
    sms_consent BOOLEAN DEFAULT FALSE,
    email_consent BOOLEAN DEFAULT FALSE,
    
    -- Audit timestamps
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    
    -- Validation
    CONSTRAINT consent_records_contact_check CHECK (
        (phone IS NOT NULL) OR (email IS NOT NULL)
    )
);

-- Indexes for consent_records
CREATE INDEX IF NOT EXISTS idx_consent_records_lead_id ON consent_records(lead_id);
CREATE INDEX IF NOT EXISTS idx_consent_records_phone ON consent_records(phone) WHERE phone IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_consent_records_email ON consent_records(email) WHERE email IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_consent_records_type_timestamp ON consent_records(consent_type, consent_timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_consent_records_source ON consent_records(consent_source, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_consent_records_withdrawn ON consent_records(consent_withdrawn_at) WHERE consent_withdrawn_at IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_consent_records_created ON consent_records(created_at DESC);

-- Metadata JSONB index for flexible querying
CREATE INDEX IF NOT EXISTS idx_consent_records_metadata_gin ON consent_records USING gin (metadata);

-- ============================================================================
-- REFERRALS TABLE
-- ============================================================================
-- Purpose: Track referral codes, rewards, and conversions
-- ============================================================================

CREATE TABLE IF NOT EXISTS referrals (
    id SERIAL PRIMARY KEY,
    
    -- Referrer information
    referrer_lead_id UUID NULL REFERENCES leads(id) ON DELETE SET NULL,
    referrer_phone VARCHAR(20) NULL,  -- E.164 format
    referrer_email VARCHAR(255) NULL,
    referrer_name VARCHAR(255) NULL,
    
    -- Referral code (unique per referrer)
    referral_code VARCHAR(20) NOT NULL UNIQUE,  -- Example: 'JOHN2025ABC'
    
    -- Referred customer information
    referred_lead_id UUID NULL REFERENCES leads(id) ON DELETE SET NULL,
    referred_phone VARCHAR(20) NULL,
    referred_email VARCHAR(255) NULL,
    referred_name VARCHAR(255) NULL,
    
    -- Conversion tracking
    referral_status VARCHAR(20) NOT NULL DEFAULT 'pending' CHECK (
        referral_status IN ('pending', 'converted', 'rewarded', 'expired', 'cancelled')
    ),
    
    -- Booking association
    booking_id UUID NULL,  -- References bookings(id) when converted
    booking_date TIMESTAMP NULL,
    booking_amount_cents INTEGER NULL,
    
    -- Reward tracking
    reward_type VARCHAR(50) NULL,  -- 'menu_item', 'discount_percent', 'discount_fixed', 'free_addon'
    reward_value VARCHAR(100) NULL,  -- '$10 off', '10%', 'free_shrimp', 'free_fried_rice'
    reward_issued_at TIMESTAMP NULL,
    reward_redeemed_at TIMESTAMP NULL,
    
    -- UTM tracking for attribution
    utm_source VARCHAR(100) NULL,
    utm_medium VARCHAR(100) NULL,
    utm_campaign VARCHAR(100) NULL,
    
    -- Additional metadata
    referral_channel VARCHAR(50) NULL,  -- 'email', 'sms', 'social', 'word_of_mouth'
    referral_message TEXT NULL,
    metadata JSONB DEFAULT '{}'::jsonb,
    
    -- Expiration
    expires_at TIMESTAMP NULL,
    
    -- Audit timestamps
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    
    -- Validation
    CONSTRAINT referrals_referrer_check CHECK (
        (referrer_lead_id IS NOT NULL) OR 
        (referrer_phone IS NOT NULL) OR 
        (referrer_email IS NOT NULL)
    ),
    CONSTRAINT referrals_status_conversion_check CHECK (
        (referral_status != 'converted' OR booking_id IS NOT NULL)
    )
);

-- Indexes for referrals
CREATE INDEX IF NOT EXISTS idx_referrals_referrer_lead ON referrals(referrer_lead_id);
CREATE INDEX IF NOT EXISTS idx_referrals_referred_lead ON referrals(referred_lead_id);
CREATE INDEX IF NOT EXISTS idx_referrals_code ON referrals(referral_code);
CREATE INDEX IF NOT EXISTS idx_referrals_status ON referrals(referral_status, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_referrals_booking ON referrals(booking_id) WHERE booking_id IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_referrals_referrer_phone ON referrals(referrer_phone) WHERE referrer_phone IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_referrals_referrer_email ON referrals(referrer_email) WHERE referrer_email IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_referrals_created ON referrals(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_referrals_expires ON referrals(expires_at) WHERE expires_at IS NOT NULL;

-- Metadata JSONB index for flexible querying
CREATE INDEX IF NOT EXISTS idx_referrals_metadata_gin ON referrals USING gin (metadata);

-- ============================================================================
-- TRIGGERS FOR UPDATED_AT
-- ============================================================================

-- Consent records trigger
CREATE OR REPLACE FUNCTION update_consent_records_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_consent_records_updated_at
    BEFORE UPDATE ON consent_records
    FOR EACH ROW
    EXECUTE FUNCTION update_consent_records_updated_at();

-- Referrals trigger
CREATE OR REPLACE FUNCTION update_referrals_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_referrals_updated_at
    BEFORE UPDATE ON referrals
    FOR EACH ROW
    EXECUTE FUNCTION update_referrals_updated_at();

-- ============================================================================
-- TABLE COMMENTS
-- ============================================================================

COMMENT ON TABLE consent_records IS 'TCPA/CAN-SPAM compliance audit trail for all consent captures';
COMMENT ON COLUMN consent_records.consent_text IS 'Exact consent text shown to user (required for TCPA compliance)';
COMMENT ON COLUMN consent_records.consent_ip_address IS 'IP address where consent was given (audit trail)';
COMMENT ON COLUMN consent_records.consent_method IS 'Method of consent capture (checkbox, auto_subscribe, double_optin, sms_reply)';
COMMENT ON COLUMN consent_records.consent_withdrawn_at IS 'When user withdrew consent (STOP command)';
COMMENT ON COLUMN consent_records.metadata IS 'Additional flexible data stored as JSONB';

COMMENT ON TABLE referrals IS 'Referral tracking system with unique codes and reward management';
COMMENT ON COLUMN referrals.referral_code IS 'Unique referral code per referrer (e.g., JOHN2025ABC)';
COMMENT ON COLUMN referrals.referral_status IS 'Status: pending, converted, rewarded, expired, cancelled';
COMMENT ON COLUMN referrals.reward_type IS 'Type of reward: menu_item, discount_percent, discount_fixed, free_addon';
COMMENT ON COLUMN referrals.reward_value IS 'Human-readable reward value ($10 off, 10%, free_shrimp, etc.)';

-- ============================================================================
-- HELPER FUNCTIONS
-- ============================================================================

-- Function to generate unique referral code
CREATE OR REPLACE FUNCTION generate_referral_code(referrer_name VARCHAR(255))
RETURNS VARCHAR(20) AS $$
DECLARE
    code_base VARCHAR(10);
    year_part VARCHAR(4);
    random_part VARCHAR(6);
    final_code VARCHAR(20);
    attempt INTEGER := 0;
BEGIN
    -- Extract first name or first 4 characters of name
    code_base := UPPER(LEFT(REGEXP_REPLACE(referrer_name, '[^a-zA-Z]', '', 'g'), 4));
    IF code_base = '' THEN
        code_base := 'USER';
    END IF;
    
    -- Add year
    year_part := EXTRACT(YEAR FROM CURRENT_DATE)::VARCHAR;
    
    -- Loop until we find a unique code
    LOOP
        -- Generate random alphanumeric string
        random_part := UPPER(SUBSTRING(MD5(RANDOM()::TEXT) FROM 1 FOR 6));
        
        -- Combine parts
        final_code := code_base || year_part || random_part;
        
        -- Check if code already exists
        IF NOT EXISTS (SELECT 1 FROM referrals WHERE referral_code = final_code) THEN
            RETURN final_code;
        END IF;
        
        -- Prevent infinite loop
        attempt := attempt + 1;
        IF attempt > 100 THEN
            RAISE EXCEPTION 'Failed to generate unique referral code after 100 attempts';
        END IF;
    END LOOP;
END;
$$ LANGUAGE plpgsql;

-- Function to check if consent is still valid
CREATE OR REPLACE FUNCTION is_consent_valid(
    p_phone VARCHAR(20) DEFAULT NULL,
    p_email VARCHAR(255) DEFAULT NULL,
    p_consent_type VARCHAR(20) DEFAULT 'marketing'
)
RETURNS BOOLEAN AS $$
DECLARE
    valid_consent BOOLEAN;
BEGIN
    SELECT EXISTS (
        SELECT 1
        FROM consent_records
        WHERE (
            (p_phone IS NOT NULL AND phone = p_phone) OR
            (p_email IS NOT NULL AND email = p_email)
        )
        AND consent_type = p_consent_type
        AND consent_given = TRUE
        AND consent_withdrawn_at IS NULL
    ) INTO valid_consent;
    
    RETURN COALESCE(valid_consent, FALSE);
END;
$$ LANGUAGE plpgsql;

-- ============================================================================
-- SAMPLE DATA (for testing only)
-- ============================================================================
-- Uncomment to insert sample data for testing:
/*
-- Sample consent record
INSERT INTO consent_records (
    lead_id,
    phone,
    email,
    consent_type,
    consent_given,
    consent_source,
    consent_ip_address,
    consent_user_agent,
    consent_text,
    consent_method,
    sms_consent,
    email_consent
) VALUES (
    NULL,  -- Direct newsletter signup
    '+15551234567',
    'john@example.com',
    'marketing',
    TRUE,
    'web_quote',
    '192.168.1.1',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64)',
    'I consent to receive SMS messages from my Hibachi LLC. Message frequency varies. Message and data rates may apply. Reply STOP to opt out.',
    'checkbox',
    TRUE,
    TRUE
);

-- Sample referral
INSERT INTO referrals (
    referrer_phone,
    referrer_email,
    referrer_name,
    referral_code,
    referral_status,
    reward_type,
    reward_value,
    referral_channel
) VALUES (
    '+15551234567',
    'john@example.com',
    'John Smith',
    generate_referral_code('John Smith'),
    'pending',
    'free_addon',
    'free_fried_rice',
    'email'
);
*/

-- ============================================================================
-- VERIFICATION QUERIES
-- ============================================================================

-- Check consent_records structure
-- SELECT column_name, data_type, is_nullable, column_default
-- FROM information_schema.columns
-- WHERE table_name = 'consent_records'
-- ORDER BY ordinal_position;

-- Check referrals structure
-- SELECT column_name, data_type, is_nullable, column_default
-- FROM information_schema.columns
-- WHERE table_name = 'referrals'
-- ORDER BY ordinal_position;

-- Check recent consents
-- SELECT 
--     id,
--     consent_type,
--     consent_source,
--     consent_method,
--     sms_consent,
--     email_consent,
--     consent_timestamp
-- FROM consent_records
-- ORDER BY consent_timestamp DESC
-- LIMIT 10;

-- Check active referrals
-- SELECT 
--     id,
--     referral_code,
--     referrer_name,
--     referral_status,
--     reward_type,
--     reward_value,
--     created_at
-- FROM referrals
-- WHERE referral_status IN ('pending', 'converted')
-- ORDER BY created_at DESC;

-- Check consent compliance rate
-- SELECT 
--     consent_type,
--     consent_method,
--     COUNT(*) as total_consents,
--     SUM(CASE WHEN consent_given THEN 1 ELSE 0 END) as consents_given,
--     SUM(CASE WHEN consent_withdrawn_at IS NOT NULL THEN 1 ELSE 0 END) as consents_withdrawn,
--     ROUND(100.0 * SUM(CASE WHEN consent_given THEN 1 ELSE 0 END) / COUNT(*), 2) as consent_rate
-- FROM consent_records
-- GROUP BY consent_type, consent_method
-- ORDER BY consent_type, consent_method;

-- Check referral conversion rate
-- SELECT 
--     referral_status,
--     COUNT(*) as total_referrals,
--     AVG(booking_amount_cents / 100.0) as avg_booking_amount,
--     COUNT(CASE WHEN reward_redeemed_at IS NOT NULL THEN 1 END) as rewards_redeemed
-- FROM referrals
-- GROUP BY referral_status
-- ORDER BY referral_status;

-- ============================================================================
-- MIGRATION COMPLETE
-- ============================================================================
-- Tables created: consent_records, referrals
-- Indexes created: 15 total (7 for consent_records, 8 for referrals)
-- Triggers created: 2 (updated_at triggers)
-- Functions created: 3 (generate_referral_code, is_consent_valid, update triggers)
-- ============================================================================
