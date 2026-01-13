-- =====================================================
-- Migration: Create audit_logs Table
-- Created: 2025-01-30
-- Purpose: Create the audit_logs table for admin action tracking
--
-- CRITICAL: This table was missing from migrations but required by:
--   - apps/backend/src/core/audit_logger.py (AuditLogger class)
--   - apps/backend/src/services/audit_service.py (AuditService)
--
-- Columns designed for:
--   - WHO: user_id, user_role, user_name, user_email
--   - WHAT: action, resource_type, resource_id, resource_name
--   - WHEN: timestamp, created_at
--   - WHERE: ip_address, user_agent, station_id
--   - WHY: delete_reason (for DELETE actions)
--   - DETAILS: old_values, new_values, metadata (JSONB)
--
-- Compliance: GDPR, SOC 2 audit trail requirements
-- =====================================================

BEGIN;

-- Create the audit_logs table if it doesn't exist
CREATE TABLE IF NOT EXISTS audit_logs (
    -- Primary Key
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- WHO: User information (denormalized for compliance - survives user deletion)
    user_id UUID,
    user_role VARCHAR(50),
    user_name VARCHAR(255),
    user_email VARCHAR(255),

    -- WHAT: Action details
    action VARCHAR(50) NOT NULL,  -- VIEW, CREATE, UPDATE, DELETE
    resource_type VARCHAR(100),   -- booking, customer, lead, chef, etc.
    resource_id VARCHAR(100),     -- UUID or identifier of the resource
    resource_name VARCHAR(500),   -- Human-readable name for UI display

    -- WHERE: Request context
    ip_address VARCHAR(45),       -- IPv4 or IPv6 address
    user_agent TEXT,              -- Browser/client information
    station_id UUID,              -- Multi-tenant station context

    -- WHY: Reason for destructive actions
    delete_reason TEXT,           -- Required for DELETE actions (10-500 chars)

    -- DETAILS: Before/after state for change tracking
    old_values JSONB,             -- State before change
    new_values JSONB,             -- State after change
    metadata JSONB DEFAULT '{}',  -- Additional context

    -- WHEN: Timestamps
    timestamp TIMESTAMPTZ DEFAULT NOW(),   -- When the action occurred
    created_at TIMESTAMPTZ DEFAULT NOW(),  -- When log was created (usually same)

    -- Constraints
    CONSTRAINT chk_audit_action CHECK (action IN ('VIEW', 'CREATE', 'UPDATE', 'DELETE')),
    CONSTRAINT chk_delete_reason CHECK (
        (action != 'DELETE') OR
        (delete_reason IS NOT NULL AND LENGTH(delete_reason) >= 10)
    )
);

-- Add comments for documentation
COMMENT ON TABLE audit_logs IS 'Audit trail for all admin actions (GDPR/SOC2 compliance)';
COMMENT ON COLUMN audit_logs.user_id IS 'UUID of the user who performed the action';
COMMENT ON COLUMN audit_logs.user_role IS 'Role at time of action (denormalized for compliance)';
COMMENT ON COLUMN audit_logs.action IS 'Action type: VIEW, CREATE, UPDATE, DELETE';
COMMENT ON COLUMN audit_logs.resource_type IS 'Type of resource affected (booking, customer, etc.)';
COMMENT ON COLUMN audit_logs.delete_reason IS 'Required reason for DELETE actions (10-500 chars)';
COMMENT ON COLUMN audit_logs.old_values IS 'JSONB snapshot of resource state before change';
COMMENT ON COLUMN audit_logs.new_values IS 'JSONB snapshot of resource state after change';
COMMENT ON COLUMN audit_logs.metadata IS 'Additional context (logged_at, request details, etc.)';

-- Create indexes (matching 001_create_performance_indexes.sql but idempotent)
-- These may already exist from performance migration

-- Index: Station-scoped audit queries
CREATE INDEX IF NOT EXISTS idx_audit_logs_station
ON audit_logs(station_id);

-- Index: User activity queries
CREATE INDEX IF NOT EXISTS idx_audit_logs_user
ON audit_logs(user_id);

-- Index: Chronological queries (newest first)
CREATE INDEX IF NOT EXISTS idx_audit_logs_timestamp
ON audit_logs(timestamp DESC);

-- Index: Station + Action + Time composite for filtered queries
CREATE INDEX IF NOT EXISTS idx_audit_logs_action
ON audit_logs(station_id, action, timestamp DESC);

-- Index: Resource lookup (find all logs for a specific resource)
CREATE INDEX IF NOT EXISTS idx_audit_logs_resource
ON audit_logs(resource_type, resource_id);

-- Index: IP address for security investigations
CREATE INDEX IF NOT EXISTS idx_audit_logs_ip
ON audit_logs(ip_address)
WHERE ip_address IS NOT NULL;

COMMIT;

-- =====================================================
-- ROLLBACK SCRIPT (keep as comment for emergency)
-- =====================================================
-- DROP TABLE IF EXISTS audit_logs CASCADE;
-- =====================================================
