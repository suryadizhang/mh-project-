-- Manual creation of communications schema and call_recordings table
-- This is needed because Alembic migrations ran but schema was skipped in dev environment

-- Create communications schema
CREATE SCHEMA IF NOT EXISTS communications;

-- Create ENUM types
DO $$ BEGIN
    CREATE TYPE communications.recording_status AS ENUM (
        'pending',
        'downloading',
        'available',
        'archived',
        'deleted',
        'error'
    );
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

DO $$ BEGIN
    CREATE TYPE communications.recording_type AS ENUM (
        'inbound',
        'outbound',
        'internal'
    );
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

-- Create call_recordings table
CREATE TABLE IF NOT EXISTS communications.call_recordings (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    
    -- RingCentral Metadata
    rc_recording_id VARCHAR(255) UNIQUE,
    rc_session_id VARCHAR(255),
    rc_extension_id VARCHAR(100),
    
    -- Call Information
    from_phone VARCHAR(20),
    to_phone VARCHAR(20),
    direction VARCHAR(20),
    type communications.recording_type DEFAULT 'inbound',
    
    -- Timing
    call_started_at TIMESTAMP WITH TIME ZONE,
    call_ended_at TIMESTAMP WITH TIME ZONE,
    duration_seconds INTEGER,
    
    -- Recording Status
    status communications.recording_status DEFAULT 'pending',
    
    -- Storage
    vps_file_path TEXT,
    file_size_bytes BIGINT,
    content_type VARCHAR(100) DEFAULT 'audio/mpeg',
    
    -- RingCentral AI Transcript Fields
    rc_transcript TEXT,
    rc_transcript_confidence FLOAT,
    rc_ai_insights JSONB,
    rc_transcript_fetched_at TIMESTAMP WITH TIME ZONE,
    
    -- Customer & Booking Linking
    customer_id VARCHAR(255),
    booking_id INTEGER,
    
    -- State Management
    state VARCHAR(50),
    
    -- Audit
    accessed_count INTEGER DEFAULT 0,
    last_accessed_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    deleted_at TIMESTAMP WITH TIME ZONE
);

-- Create indexes
CREATE INDEX IF NOT EXISTS idx_call_recordings_rc_recording_id 
    ON communications.call_recordings(rc_recording_id);

CREATE INDEX IF NOT EXISTS idx_call_recordings_rc_session_id 
    ON communications.call_recordings(rc_session_id);

CREATE INDEX IF NOT EXISTS idx_call_recordings_from_phone 
    ON communications.call_recordings(from_phone);

CREATE INDEX IF NOT EXISTS idx_call_recordings_to_phone 
    ON communications.call_recordings(to_phone);

CREATE INDEX IF NOT EXISTS idx_call_recordings_call_started_at 
    ON communications.call_recordings(call_started_at);

CREATE INDEX IF NOT EXISTS idx_call_recordings_status 
    ON communications.call_recordings(status);

CREATE INDEX IF NOT EXISTS idx_call_recordings_customer_id 
    ON communications.call_recordings(customer_id);

CREATE INDEX IF NOT EXISTS idx_call_recordings_booking_id 
    ON communications.call_recordings(booking_id);

-- Performance indexes from Phase 2.4
CREATE INDEX IF NOT EXISTS idx_call_recordings_customer_datetime 
    ON communications.call_recordings(customer_id, call_started_at);

CREATE INDEX IF NOT EXISTS idx_call_recordings_has_transcript 
    ON communications.call_recordings(id) 
    WHERE rc_transcript IS NOT NULL;

-- Grant permissions
GRANT ALL ON SCHEMA communications TO postgres;
GRANT ALL ON ALL TABLES IN SCHEMA communications TO postgres;

-- Success message
SELECT 'Communications schema and call_recordings table created successfully!' AS status;
