-- Migration: Customer Review Blog System
-- Created: October 26, 2025
-- Description: Add tables for customer reviews with admin approval workflow

-- Customer review blog posts
CREATE TABLE IF NOT EXISTS customer_review_blog_posts (
    id SERIAL PRIMARY KEY,
    customer_id INTEGER REFERENCES customers(id) ON DELETE CASCADE,
    booking_id INTEGER REFERENCES bookings(id) ON DELETE SET NULL,
    
    -- Content
    title VARCHAR(255) NOT NULL,
    content TEXT NOT NULL,
    rating INTEGER NOT NULL CHECK (rating >= 1 AND rating <= 5),
    
    -- Images (stored as JSON array)
    images JSONB DEFAULT '[]',
    
    -- Status (admin approval workflow)
    status VARCHAR(20) DEFAULT 'pending' CHECK (status IN ('pending', 'approved', 'rejected')),
    approved_by INTEGER REFERENCES users(id) ON DELETE SET NULL,
    approved_at TIMESTAMP,
    rejection_reason TEXT,
    
    -- External reviews (track if they also reviewed on Google/Yelp)
    reviewed_on_google BOOLEAN DEFAULT FALSE,
    reviewed_on_yelp BOOLEAN DEFAULT FALSE,
    google_review_link TEXT,
    yelp_review_link TEXT,
    
    -- Metadata
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- SEO
    slug VARCHAR(255) UNIQUE,
    keywords TEXT[],
    
    -- Engagement
    likes_count INTEGER DEFAULT 0,
    helpful_count INTEGER DEFAULT 0
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_reviews_status ON customer_review_blog_posts(status);
CREATE INDEX IF NOT EXISTS idx_reviews_customer ON customer_review_blog_posts(customer_id);
CREATE INDEX IF NOT EXISTS idx_reviews_created ON customer_review_blog_posts(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_reviews_rating ON customer_review_blog_posts(rating);
CREATE INDEX IF NOT EXISTS idx_reviews_slug ON customer_review_blog_posts(slug);
CREATE INDEX IF NOT EXISTS idx_reviews_approved_at ON customer_review_blog_posts(approved_at DESC) WHERE status = 'approved';

-- Admin approval log (audit trail)
CREATE TABLE IF NOT EXISTS review_approval_log (
    id SERIAL PRIMARY KEY,
    review_id INTEGER REFERENCES customer_review_blog_posts(id) ON DELETE CASCADE,
    admin_id INTEGER REFERENCES users(id) ON DELETE SET NULL,
    action VARCHAR(20) NOT NULL CHECK (action IN ('pending_review', 'approved', 'rejected')),
    comment TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_approval_log_review ON review_approval_log(review_id);
CREATE INDEX IF NOT EXISTS idx_approval_log_admin ON review_approval_log(admin_id);
CREATE INDEX IF NOT EXISTS idx_approval_log_created ON review_approval_log(created_at DESC);

-- Update trigger for updated_at
CREATE OR REPLACE FUNCTION update_customer_review_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_update_customer_review_updated_at
    BEFORE UPDATE ON customer_review_blog_posts
    FOR EACH ROW
    EXECUTE FUNCTION update_customer_review_updated_at();

-- Comments for documentation
COMMENT ON TABLE customer_review_blog_posts IS 'Customer reviews with admin approval workflow';
COMMENT ON COLUMN customer_review_blog_posts.status IS 'pending, approved, or rejected';
COMMENT ON COLUMN customer_review_blog_posts.images IS 'JSON array of image URLs and metadata';
COMMENT ON TABLE review_approval_log IS 'Audit trail of all admin actions on reviews';
