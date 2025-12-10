-- ===========================================================================
-- BATCH 1: COMBINED DATABASE MIGRATION SCRIPT
-- MyHibachi - December 2025
-- ===========================================================================
-- 
-- INSTRUCTIONS:
-- 1. Take a database backup before running
-- 2. Run this script on staging first, verify, then production
-- 3. Monitor for any errors during execution
-- 
-- EXECUTION:
--   psql -h <host> -U <user> -d <database> -f BATCH_1_COMBINED_MIGRATION.sql
-- 
-- ROLLBACK:
--   Each section is idempotent (IF NOT EXISTS), but to fully rollback:
--   1. Restore from backup taken before migration
-- 
-- ===========================================================================

BEGIN;

-- ===========================================================================
-- SECTION 1: ERROR LOGS TABLE
-- Needed for: Admin dashboard error tracking
-- ===========================================================================
\echo '>>> Creating error_logs table...'

CREATE TABLE IF NOT EXISTS error_logs (
    id SERIAL PRIMARY KEY,
    correlation_id VARCHAR(36) NOT NULL,
    timestamp TIMESTAMP DEFAULT NOW(),
    method VARCHAR(10),
    path VARCHAR(512),
    client_ip VARCHAR(45),
    user_id INTEGER,
    user_role VARCHAR(50),
    error_type VARCHAR(100),
    error_message TEXT,
    error_traceback TEXT,
    status_code INTEGER,
    request_body TEXT,
    request_headers TEXT,
    user_agent VARCHAR(512),
    response_time_ms INTEGER,
    level VARCHAR(20) DEFAULT 'ERROR',
    resolved INTEGER DEFAULT 0,
    resolved_at TIMESTAMP,
    resolved_by INTEGER,
    resolution_notes TEXT
);

CREATE INDEX IF NOT EXISTS ix_error_logs_correlation_id ON error_logs(correlation_id);
CREATE INDEX IF NOT EXISTS ix_error_logs_timestamp ON error_logs(timestamp);
CREATE INDEX IF NOT EXISTS ix_error_logs_user_id ON error_logs(user_id);
CREATE INDEX IF NOT EXISTS ix_error_logs_level ON error_logs(level);

\echo '>>> error_logs table created.'

-- ===========================================================================
-- SECTION 2: MFA COLUMNS (Identity Schema)
-- Needed for: WebAuthn + PIN authentication
-- ===========================================================================
\echo '>>> Adding MFA columns to identity.users...'

ALTER TABLE identity.users
ADD COLUMN IF NOT EXISTS webauthn_credentials JSONB DEFAULT '[]';

ALTER TABLE identity.users
ADD COLUMN IF NOT EXISTS pin_hash VARCHAR(255);

ALTER TABLE identity.users
ADD COLUMN IF NOT EXISTS pin_attempts INT DEFAULT 0;

ALTER TABLE identity.users
ADD COLUMN IF NOT EXISTS pin_locked_until TIMESTAMP WITH TIME ZONE;

ALTER TABLE identity.users
ADD COLUMN IF NOT EXISTS mfa_setup_complete BOOLEAN DEFAULT FALSE;

ALTER TABLE identity.users
ADD COLUMN IF NOT EXISTS mfa_setup_at TIMESTAMP WITH TIME ZONE;

ALTER TABLE identity.users
ADD COLUMN IF NOT EXISTS pin_reset_required BOOLEAN DEFAULT FALSE;

CREATE INDEX IF NOT EXISTS idx_users_mfa_setup ON identity.users(mfa_setup_complete);

\echo '>>> MFA columns added.'

-- ===========================================================================
-- SECTION 3: SECURITY SCHEMA & TABLES
-- Needed for: Security event logging, admin alerts
-- ===========================================================================
\echo '>>> Creating security schema and tables...'

CREATE SCHEMA IF NOT EXISTS security;

-- Security Events Table
CREATE TABLE IF NOT EXISTS security.security_events (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    event_type VARCHAR(50) NOT NULL,
    user_id UUID REFERENCES identity.users(id) ON DELETE SET NULL,
    email VARCHAR(255),
    ip_address VARCHAR(45),
    user_agent TEXT,
    details JSONB DEFAULT '{}',
    severity VARCHAR(20) DEFAULT 'low',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_security_events_user_id ON security.security_events(user_id);
CREATE INDEX IF NOT EXISTS idx_security_events_email ON security.security_events(email);
CREATE INDEX IF NOT EXISTS idx_security_events_ip_address ON security.security_events(ip_address);
CREATE INDEX IF NOT EXISTS idx_security_events_event_type ON security.security_events(event_type);
CREATE INDEX IF NOT EXISTS idx_security_events_created_at ON security.security_events(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_security_events_severity ON security.security_events(severity);
CREATE INDEX IF NOT EXISTS idx_security_events_ip_type_time ON security.security_events(ip_address, event_type, created_at DESC);

-- Admin Alerts Table
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
    details JSONB DEFAULT '{}'
);

CREATE INDEX IF NOT EXISTS idx_admin_alerts_status ON security.admin_alerts(status);
CREATE INDEX IF NOT EXISTS idx_admin_alerts_severity ON security.admin_alerts(severity);
CREATE INDEX IF NOT EXISTS idx_admin_alerts_created_at ON security.admin_alerts(created_at DESC);

\echo '>>> Security tables created.'

-- ===========================================================================
-- SECTION 4: PERFORMANCE INDEXES
-- Needed for: Fast queries on core tables
-- ===========================================================================
\echo '>>> Creating performance indexes...'

-- Bookings indexes
CREATE INDEX IF NOT EXISTS idx_bookings_customer_id ON bookings(customer_id);
CREATE INDEX IF NOT EXISTS idx_bookings_booking_date ON bookings(booking_date);
CREATE INDEX IF NOT EXISTS idx_bookings_status ON bookings(status);
CREATE INDEX IF NOT EXISTS idx_bookings_created_at ON bookings(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_bookings_station_date ON bookings(station_id, booking_date) WHERE station_id IS NOT NULL;

-- Customers indexes
CREATE INDEX IF NOT EXISTS idx_customers_email ON core.customers(email);
CREATE INDEX IF NOT EXISTS idx_customers_phone ON core.customers(phone);
CREATE INDEX IF NOT EXISTS idx_customers_created_at ON core.customers(created_at DESC);

-- Payments indexes (if table exists)
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'payments') THEN
        CREATE INDEX IF NOT EXISTS idx_payments_booking_id ON payments(booking_id);
        CREATE INDEX IF NOT EXISTS idx_payments_status ON payments(status);
        CREATE INDEX IF NOT EXISTS idx_payments_created_at ON payments(created_at DESC);
    END IF;
END $$;

\echo '>>> Performance indexes created.'

-- ===========================================================================
-- SECTION 5: AI SCHEMA & TABLES (Foundation for Batch 3)
-- Needed for: AI conversation tracking, messages, feedback
-- ===========================================================================
\echo '>>> Creating AI schema and tables...'

CREATE SCHEMA IF NOT EXISTS ai;

-- Conversations Table
CREATE TABLE IF NOT EXISTS ai.conversations (
    id VARCHAR(100) PRIMARY KEY,
    user_id VARCHAR(255),
    customer_id VARCHAR(36),
    channel VARCHAR(20) NOT NULL DEFAULT 'web',
    thread_id VARCHAR(255),
    channel_metadata JSONB NOT NULL DEFAULT '{}',
    status VARCHAR(20) NOT NULL DEFAULT 'active',
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW(),
    last_message_at TIMESTAMP NOT NULL DEFAULT NOW(),
    closed_at TIMESTAMP,
    closed_reason VARCHAR(100),
    message_count INTEGER NOT NULL DEFAULT 0,
    context JSONB NOT NULL DEFAULT '{}',
    average_emotion_score FLOAT,
    emotion_trend VARCHAR(20),
    escalated BOOLEAN NOT NULL DEFAULT FALSE,
    escalated_at TIMESTAMP,
    assigned_agent_id VARCHAR(255),
    escalation_reason TEXT,
    confidence_score FLOAT DEFAULT 1.0,
    route_decision VARCHAR(50) DEFAULT 'teacher',
    student_response TEXT,
    teacher_response TEXT,
    reward_score FLOAT
);

CREATE INDEX IF NOT EXISTS idx_conversations_user_active ON ai.conversations(user_id, is_active);
CREATE INDEX IF NOT EXISTS idx_conversations_channel_status ON ai.conversations(channel, status);
CREATE INDEX IF NOT EXISTS idx_conversations_created ON ai.conversations(created_at);
CREATE INDEX IF NOT EXISTS idx_conversations_customer_id ON ai.conversations(customer_id);

-- Messages Table
CREATE TABLE IF NOT EXISTS ai.messages (
    id VARCHAR(100) PRIMARY KEY,
    conversation_id VARCHAR(100) NOT NULL REFERENCES ai.conversations(id) ON DELETE CASCADE,
    role VARCHAR(20) NOT NULL,
    content TEXT NOT NULL,
    text TEXT,
    channel VARCHAR(20) NOT NULL DEFAULT 'web',
    timestamp TIMESTAMP NOT NULL DEFAULT NOW(),
    edited_at TIMESTAMP,
    metadata JSONB DEFAULT '{}',
    emotion_score FLOAT,
    emotion_label VARCHAR(50),
    tokens_used INTEGER,
    tool_calls JSONB DEFAULT '[]'
);

CREATE INDEX IF NOT EXISTS idx_messages_conversation_id ON ai.messages(conversation_id);
CREATE INDEX IF NOT EXISTS idx_messages_timestamp ON ai.messages(timestamp);
CREATE INDEX IF NOT EXISTS idx_messages_role ON ai.messages(role);

-- AI Feedback Table
CREATE TABLE IF NOT EXISTS ai.feedback (
    id VARCHAR(100) PRIMARY KEY,
    conversation_id VARCHAR(100) REFERENCES ai.conversations(id) ON DELETE SET NULL,
    message_id VARCHAR(100) REFERENCES ai.messages(id) ON DELETE SET NULL,
    rating INTEGER CHECK (rating >= 1 AND rating <= 5),
    feedback_type VARCHAR(50),
    comment TEXT,
    user_id VARCHAR(255),
    created_at TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_feedback_conversation_id ON ai.feedback(conversation_id);
CREATE INDEX IF NOT EXISTS idx_feedback_rating ON ai.feedback(rating);

\echo '>>> AI tables created.'

-- ===========================================================================
-- VERIFICATION
-- ===========================================================================
\echo '>>> Verifying migration...'

SELECT 'error_logs' as table_name, COUNT(*) as exists FROM information_schema.tables WHERE table_name = 'error_logs'
UNION ALL
SELECT 'security.security_events', COUNT(*) FROM information_schema.tables WHERE table_schema = 'security' AND table_name = 'security_events'
UNION ALL
SELECT 'security.admin_alerts', COUNT(*) FROM information_schema.tables WHERE table_schema = 'security' AND table_name = 'admin_alerts'
UNION ALL
SELECT 'ai.conversations', COUNT(*) FROM information_schema.tables WHERE table_schema = 'ai' AND table_name = 'conversations'
UNION ALL
SELECT 'ai.messages', COUNT(*) FROM information_schema.tables WHERE table_schema = 'ai' AND table_name = 'messages'
UNION ALL
SELECT 'ai.feedback', COUNT(*) FROM information_schema.tables WHERE table_schema = 'ai' AND table_name = 'feedback';

COMMIT;

\echo ''
\echo '==========================================================================='
\echo 'BATCH 1 MIGRATION COMPLETE!'
\echo '==========================================================================='
\echo ''
\echo 'Created:'
\echo '  - error_logs table'
\echo '  - MFA columns on identity.users'
\echo '  - security.security_events table'
\echo '  - security.admin_alerts table'
\echo '  - Performance indexes on bookings, customers, payments'
\echo '  - ai.conversations table'
\echo '  - ai.messages table'
\echo '  - ai.feedback table'
\echo ''
\echo 'Next steps:'
\echo '  1. Verify tables exist in your database client'
\echo '  2. Test application functionality'
\echo '  3. Monitor for any errors'
\echo ''
