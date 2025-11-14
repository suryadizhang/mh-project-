-- ============================================================================
-- KNOWLEDGE SYNC HISTORY TABLE
-- ============================================================================
-- Purpose: Track all knowledge base synchronization operations for audit trail
-- Created: 2025 (Dynamic Knowledge Base Phase 3)
-- ============================================================================

-- Drop existing table if exists (development only)
-- DROP TABLE IF EXISTS sync_history CASCADE;

-- Create sync_history table
CREATE TABLE IF NOT EXISTS sync_history (
    id SERIAL PRIMARY KEY,
    
    -- Source identification
    source_type VARCHAR(20) NOT NULL CHECK (source_type IN ('menu', 'faqs', 'terms')),
    source_file_path TEXT NOT NULL,  -- Full path to the TypeScript/TSX file
    
    -- Sync tracking
    file_hash VARCHAR(64) NOT NULL,  -- SHA256 hash of file content
    last_sync_time TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    
    -- Change statistics
    changes_applied INT DEFAULT 0,  -- Total changes successfully applied
    items_added INT DEFAULT 0,      -- New items inserted
    items_modified INT DEFAULT 0,   -- Existing items updated
    items_deleted INT DEFAULT 0,    -- Items removed from DB
    conflicts_detected INT DEFAULT 0,  -- Manual DB edits that conflicted with file changes
    
    -- Sync metadata
    synced_by VARCHAR(100),  -- Superadmin user ID or 'auto-sync'
    sync_type VARCHAR(20) DEFAULT 'auto' CHECK (sync_type IN ('auto', 'manual', 'force')),
    sync_status VARCHAR(20) DEFAULT 'success' CHECK (sync_status IN ('success', 'partial', 'failed')),
    
    -- Error tracking
    error_message TEXT,  -- Error details if sync_status = 'failed'
    
    -- Audit trail
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes for efficient querying
CREATE INDEX IF NOT EXISTS idx_sync_history_source ON sync_history(source_type, last_sync_time DESC);
CREATE INDEX IF NOT EXISTS idx_sync_history_status ON sync_history(sync_status, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_sync_history_user ON sync_history(synced_by, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_sync_history_created ON sync_history(created_at DESC);

-- Create trigger for updated_at
CREATE OR REPLACE FUNCTION update_sync_history_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_sync_history_updated_at
    BEFORE UPDATE ON sync_history
    FOR EACH ROW
    EXECUTE FUNCTION update_sync_history_updated_at();

-- Add comments for documentation
COMMENT ON TABLE sync_history IS 'Audit trail for knowledge base synchronization operations';
COMMENT ON COLUMN sync_history.source_type IS 'Type of knowledge source: menu, faqs, or terms';
COMMENT ON COLUMN sync_history.file_hash IS 'SHA256 hash of source file content for change detection';
COMMENT ON COLUMN sync_history.sync_type IS 'Type of sync: auto (scheduled), manual (triggered), or force (override conflicts)';
COMMENT ON COLUMN sync_history.sync_status IS 'Result of sync operation: success, partial (with conflicts), or failed';
COMMENT ON COLUMN sync_history.conflicts_detected IS 'Number of items with manual DB edits that conflicted with file changes';

-- ============================================================================
-- SAMPLE DATA (for testing only)
-- ============================================================================
-- Uncomment to insert sample sync history for testing:
/*
INSERT INTO sync_history (
    source_type,
    source_file_path,
    file_hash,
    changes_applied,
    items_added,
    items_modified,
    items_deleted,
    conflicts_detected,
    synced_by,
    sync_type,
    sync_status
) VALUES
    ('menu', 'apps/website/src/app/menu/page.tsx', 'abc123def456', 5, 2, 3, 0, 0, 'auto-sync', 'auto', 'success'),
    ('faqs', 'apps/website/src/data/faqsData.ts', 'def456ghi789', 3, 1, 2, 0, 0, 'auto-sync', 'auto', 'success'),
    ('terms', 'apps/website/src/app/contact/terms/page.tsx', 'ghi789jkl012', 2, 0, 1, 1, 1, 'superadmin-123', 'force', 'partial');
*/

-- ============================================================================
-- VERIFICATION QUERIES
-- ============================================================================
-- Check table structure
-- SELECT column_name, data_type, is_nullable, column_default
-- FROM information_schema.columns
-- WHERE table_name = 'sync_history'
-- ORDER BY ordinal_position;

-- Check indexes
-- SELECT indexname, indexdef
-- FROM pg_indexes
-- WHERE tablename = 'sync_history';

-- Check recent sync history
-- SELECT 
--     id,
--     source_type,
--     sync_type,
--     sync_status,
--     changes_applied,
--     conflicts_detected,
--     last_sync_time
-- FROM sync_history
-- ORDER BY last_sync_time DESC
-- LIMIT 10;

-- Check sync success rate by source
-- SELECT 
--     source_type,
--     COUNT(*) as total_syncs,
--     SUM(CASE WHEN sync_status = 'success' THEN 1 ELSE 0 END) as successful,
--     SUM(CASE WHEN sync_status = 'partial' THEN 1 ELSE 0 END) as partial,
--     SUM(CASE WHEN sync_status = 'failed' THEN 1 ELSE 0 END) as failed,
--     SUM(changes_applied) as total_changes_applied,
--     SUM(conflicts_detected) as total_conflicts
-- FROM sync_history
-- GROUP BY source_type
-- ORDER BY source_type;
