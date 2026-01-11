-- =====================================================
-- Migration: 013 - Review Media Table
-- Created: 2025-01-30
-- Purpose: Add review_media table for customer review images/videos
-- =====================================================

BEGIN;

-- Create review_media table in feedback schema
CREATE TABLE IF NOT EXISTS feedback.review_media (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    review_id UUID NOT NULL REFERENCES feedback.customer_reviews(id) ON DELETE CASCADE,

    -- Media type
    media_type VARCHAR(20) NOT NULL CHECK (media_type IN ('image', 'video')),

    -- File info
    original_filename VARCHAR(255),
    file_size_bytes INTEGER,
    content_type VARCHAR(100),

    -- R2 URLs
    original_url TEXT,
    optimized_url TEXT,
    thumbnail_url TEXT,

    -- Dimensions (for images/videos)
    width INTEGER,
    height INTEGER,

    -- Processing status
    processing_status VARCHAR(20) DEFAULT 'pending' CHECK (
        processing_status IN ('pending', 'processing', 'completed', 'failed')
    ),
    processing_error TEXT,

    -- Display order
    display_order INTEGER DEFAULT 0,

    -- Timestamps
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    processed_at TIMESTAMPTZ
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_review_media_review_id
    ON feedback.review_media(review_id);

CREATE INDEX IF NOT EXISTS idx_review_media_status
    ON feedback.review_media(processing_status)
    WHERE processing_status IN ('pending', 'processing');

-- Comments
COMMENT ON TABLE feedback.review_media IS
    'Media files (images/videos) attached to customer reviews';

COMMENT ON COLUMN feedback.review_media.original_url IS
    'R2 URL to original uploaded file';

COMMENT ON COLUMN feedback.review_media.optimized_url IS
    'R2 URL to web-optimized version (WebP for images, H.264/MP4 for videos)';

COMMENT ON COLUMN feedback.review_media.thumbnail_url IS
    'R2 URL to thumbnail (WebP, 300x300 max)';

COMMENT ON COLUMN feedback.review_media.processing_status IS
    'pending: waiting for processing, processing: in progress, completed: done, failed: error occurred';

-- Update trigger for updated_at
CREATE OR REPLACE FUNCTION feedback.update_review_media_timestamp()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trg_review_media_updated_at ON feedback.review_media;
CREATE TRIGGER trg_review_media_updated_at
    BEFORE UPDATE ON feedback.review_media
    FOR EACH ROW
    EXECUTE FUNCTION feedback.update_review_media_timestamp();

-- Grant permissions
GRANT SELECT, INSERT, UPDATE, DELETE ON feedback.review_media TO myhibachi_user;
GRANT SELECT, INSERT, UPDATE, DELETE ON feedback.review_media TO myhibachi_staging_user;

COMMIT;

-- =====================================================
-- ROLLBACK SCRIPT (keep as comment for emergency):
-- =====================================================
-- DROP TRIGGER IF EXISTS trg_review_media_updated_at ON feedback.review_media;
-- DROP FUNCTION IF EXISTS feedback.update_review_media_timestamp();
-- DROP TABLE IF EXISTS feedback.review_media;
