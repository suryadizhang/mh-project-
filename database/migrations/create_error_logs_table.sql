-- Create error_logs table for admin dashboard
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

-- Create indexes for faster queries
CREATE INDEX IF NOT EXISTS ix_error_logs_correlation_id ON error_logs(correlation_id);
CREATE INDEX IF NOT EXISTS ix_error_logs_timestamp ON error_logs(timestamp);
CREATE INDEX IF NOT EXISTS ix_error_logs_user_id ON error_logs(user_id);
CREATE INDEX IF NOT EXISTS ix_error_logs_level ON error_logs(level);
