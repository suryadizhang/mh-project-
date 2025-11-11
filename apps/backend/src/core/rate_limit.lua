-- Atomic Rate Limiting with Redis Lua Script
-- This script ensures atomic check-and-increment to prevent race conditions
--
-- KEYS[1] = minute_key (e.g., "rate_limit:user:123:minute:12345")
-- KEYS[2] = hour_key (e.g., "rate_limit:user:123:hour:12345")
-- ARGV[1] = minute_limit (e.g., 60)
-- ARGV[2] = hour_limit (e.g., 1000)
-- ARGV[3] = minute_ttl (e.g., 120 seconds)
-- ARGV[4] = hour_ttl (e.g., 7200 seconds)
--
-- Returns:
--   {1, minute_count, hour_count} if allowed
--   {0, minute_count, hour_count, "per_minute"} if minute limit exceeded
--   {0, minute_count, hour_count, "per_hour"} if hour limit exceeded

-- Get current counts
local minute_count = tonumber(redis.call('GET', KEYS[1])) or 0
local hour_count = tonumber(redis.call('GET', KEYS[2])) or 0

local minute_limit = tonumber(ARGV[1])
local hour_limit = tonumber(ARGV[2])
local minute_ttl = tonumber(ARGV[3])
local hour_ttl = tonumber(ARGV[4])

-- Check minute limit first (stricter limit)
if minute_count >= minute_limit then
    return {0, minute_count, hour_count, "per_minute"}
end

-- Check hour limit
if hour_count >= hour_limit then
    return {0, minute_count, hour_count, "per_hour"}
end

-- Both limits OK - atomically increment and set TTL
redis.call('INCR', KEYS[1])
redis.call('EXPIRE', KEYS[1], minute_ttl)
redis.call('INCR', KEYS[2])
redis.call('EXPIRE', KEYS[2], hour_ttl)

-- Return success with new counts
return {1, minute_count + 1, hour_count + 1}
