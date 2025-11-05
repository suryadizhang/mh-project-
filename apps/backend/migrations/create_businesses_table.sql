-- White-Label Multi-Tenancy Foundation
-- Creates businesses table for supporting multiple restaurant brands

-- Drop existing table if exists (for fresh migration)
DROP TABLE IF EXISTS businesses CASCADE;

-- Create businesses table
CREATE TABLE businesses (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    slug VARCHAR(100) NOT NULL UNIQUE,
    domain VARCHAR(255) UNIQUE,
    
    -- Branding
    logo_url VARCHAR(500),
    primary_color VARCHAR(7) DEFAULT '#FF6B6B',
    secondary_color VARCHAR(7) DEFAULT '#4ECDC4',
    
    -- Contact Information
    phone VARCHAR(20),
    email VARCHAR(255),
    address TEXT,
    
    -- Business Settings
    timezone VARCHAR(50) NOT NULL DEFAULT 'America/Los_Angeles',
    currency VARCHAR(3) NOT NULL DEFAULT 'USD',
    settings JSONB NOT NULL DEFAULT '{}',
    
    -- Subscription (White-Label Revenue Model)
    subscription_tier VARCHAR(50) NOT NULL DEFAULT 'self_hosted',
    subscription_status VARCHAR(20) NOT NULL DEFAULT 'active',
    monthly_fee NUMERIC(10, 2) NOT NULL DEFAULT 0.00,
    
    -- Metadata
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes for performance
CREATE INDEX idx_businesses_slug ON businesses(slug);
CREATE UNIQUE INDEX idx_businesses_domain ON businesses(domain) WHERE domain IS NOT NULL;
CREATE INDEX idx_businesses_subscription_status ON businesses(subscription_status);
CREATE INDEX idx_businesses_is_active ON businesses(is_active);

-- Insert My Hibachi Chef as the default business (self-hosted)
INSERT INTO businesses (
    name, slug, domain,
    logo_url, primary_color, secondary_color,
    phone, email, address,
    timezone, currency, settings,
    subscription_tier, subscription_status, monthly_fee,
    is_active
) VALUES (
    'My Hibachi Chef',
    'my-hibachi-chef',
    'myhibachichef.com',
    NULL,
    '#FF6B6B',
    '#4ECDC4',
    '555-0123',
    'info@myhibachichef.com',
    '123 Hibachi Lane, Los Angeles, CA 90001',
    'America/Los_Angeles',
    'USD',
    '{}'::jsonb,
    'self_hosted',
    'active',
    0.00,
    TRUE
) ON CONFLICT (slug) DO NOTHING;

-- Verify
SELECT id, name, slug, subscription_tier, is_active FROM businesses;
