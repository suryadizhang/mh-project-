-- =====================================================
-- Migration: 011_travel_cache_table.sql
-- Purpose: Create travel_cache table for Google Maps API response caching
-- Created: 2025-01-30
-- Author: AI Agent
-- Batch: 1 (Smart Scheduling)
-- =====================================================

-- Travel Cache Table
-- Caches travel time calculations from Google Maps/OpenRouteService
-- Reduces API costs and improves response times
-- TTL: 7 days (configurable via expires_at)

BEGIN;

-- Create travel_cache table in public schema
CREATE TABLE IF NOT EXISTS public.travel_cache (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Origin coordinates (rounded to 3 decimals for ~100m precision)
    origin_lat FLOAT NOT NULL,
    origin_lng FLOAT NOT NULL,

    -- Destination coordinates (rounded to 3 decimals for ~100m precision)
    dest_lat FLOAT NOT NULL,
    dest_lng FLOAT NOT NULL,

    -- Travel calculation results
    travel_time_minutes INTEGER NOT NULL,
    distance_miles FLOAT NOT NULL,

    -- Rush hour flag (affects travel time multiplier)
    is_rush_hour BOOLEAN NOT NULL DEFAULT FALSE,

    -- Data source tracking
    source VARCHAR(50) NOT NULL DEFAULT 'google_maps',
    -- Valid values: 'google_maps', 'openroute', 'estimate'

    -- Cache metadata
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    expires_at TIMESTAMPTZ NOT NULL DEFAULT (NOW() + INTERVAL '7 days'),

    -- Usage statistics
    hit_count INTEGER NOT NULL DEFAULT 0
);

-- Comments for documentation
COMMENT ON TABLE public.travel_cache IS 'Caches travel time API responses to reduce costs and improve latency. TTL: 7 days.';
COMMENT ON COLUMN public.travel_cache.origin_lat IS 'Origin latitude, rounded to 3 decimals (~100m precision)';
COMMENT ON COLUMN public.travel_cache.origin_lng IS 'Origin longitude, rounded to 3 decimals (~100m precision)';
COMMENT ON COLUMN public.travel_cache.dest_lat IS 'Destination latitude, rounded to 3 decimals (~100m precision)';
COMMENT ON COLUMN public.travel_cache.dest_lng IS 'Destination longitude, rounded to 3 decimals (~100m precision)';
COMMENT ON COLUMN public.travel_cache.travel_time_minutes IS 'Calculated travel time in minutes';
COMMENT ON COLUMN public.travel_cache.distance_miles IS 'Calculated distance in miles';
COMMENT ON COLUMN public.travel_cache.is_rush_hour IS 'Whether this calculation is for rush hour (Mon-Fri 3-7PM)';
COMMENT ON COLUMN public.travel_cache.source IS 'API source: google_maps, openroute, or estimate';
COMMENT ON COLUMN public.travel_cache.hit_count IS 'Number of times this cache entry has been used';

-- Index for efficient coordinate lookups (primary query pattern)
CREATE INDEX IF NOT EXISTS idx_travel_cache_coords
    ON public.travel_cache (origin_lat, origin_lng, dest_lat, dest_lng);

-- Index for cache expiration cleanup
CREATE INDEX IF NOT EXISTS idx_travel_cache_expires
    ON public.travel_cache (expires_at);

-- Index for rush hour filtering
CREATE INDEX IF NOT EXISTS idx_travel_cache_rush_hour
    ON public.travel_cache (is_rush_hour)
    WHERE is_rush_hour = TRUE;

COMMIT;

-- =====================================================
-- ROLLBACK SCRIPT (if needed)
-- =====================================================
-- DROP INDEX IF EXISTS public.idx_travel_cache_rush_hour;
-- DROP INDEX IF EXISTS public.idx_travel_cache_expires;
-- DROP INDEX IF EXISTS public.idx_travel_cache_coords;
-- DROP TABLE IF EXISTS public.travel_cache;
