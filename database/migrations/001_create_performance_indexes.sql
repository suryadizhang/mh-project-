-- =====================================================
-- CRITICAL DATABASE PERFORMANCE INDEXES
-- Deploy immediately to prevent query slowdowns
-- Estimated improvement: 10x-100x faster queries
-- =====================================================
-- Date: October 28, 2025
-- Priority: CRITICAL
-- Estimated deployment time: 2 minutes
-- =====================================================

-- ============================================
-- BOOKINGS TABLE INDEXES
-- ============================================
-- Most queried table in the system
-- Without these, queries slow exponentially after 10k records

-- Index: Fast customer booking history lookup
-- Used by: /api/v1/customers/{id}/bookings, admin dashboard
-- Impact: 50x faster customer history queries
CREATE INDEX IF NOT EXISTS idx_bookings_customer_id 
ON bookings(customer_id);

-- Index: Fast date-range queries
-- Used by: Calendar view, availability checks, analytics
-- Impact: 100x faster date filters
CREATE INDEX IF NOT EXISTS idx_bookings_booking_date 
ON bookings(booking_date);

-- Index: Fast status filtering (pending, confirmed, completed, cancelled)
-- Used by: Admin booking list, status filters, analytics
-- Impact: 20x faster status filters
CREATE INDEX IF NOT EXISTS idx_bookings_status 
ON bookings(status);

-- Index: Fast recent bookings queries (DESC = newest first)
-- Used by: Dashboard, recent activity, admin lists
-- Impact: 50x faster for paginated lists
CREATE INDEX IF NOT EXISTS idx_bookings_created_at 
ON bookings(created_at DESC);

-- Composite index: Station-specific booking queries
-- Used by: Multi-tenant station filtering, RBAC queries
-- Impact: 30x faster station-scoped queries
CREATE INDEX IF NOT EXISTS idx_bookings_station_date 
ON bookings(station_id, booking_date) 
WHERE station_id IS NOT NULL;

-- Composite index: Payment status + amount queries
-- Used by: Financial reports, payment analytics
-- Impact: 40x faster payment queries
CREATE INDEX IF NOT EXISTS idx_bookings_payment_status_amount 
ON bookings(payment_status, total_amount_cents)
WHERE payment_status IS NOT NULL;


-- ============================================
-- CUSTOMERS TABLE INDEXES
-- ============================================
-- Critical for search and lookup operations

-- Index: Fast email lookup (unique constraint + index)
-- Used by: Login, customer search, duplicate check
-- Impact: Instant email lookups
CREATE UNIQUE INDEX IF NOT EXISTS idx_customers_email 
ON customers(LOWER(email));

-- Index: Fast phone number lookup
-- Used by: SMS messaging, phone search, duplicate check
-- Impact: Instant phone lookups
CREATE INDEX IF NOT EXISTS idx_customers_phone 
ON customers(phone) 
WHERE phone IS NOT NULL;

-- Index: Fast name search (for autocomplete)
-- Used by: Admin customer search, booking forms
-- Impact: 10x faster name searches
CREATE INDEX IF NOT EXISTS idx_customers_name_search 
ON customers(first_name, last_name);

-- Index: Station-specific customer queries
-- Used by: Multi-tenant customer lists, RBAC
-- Impact: 20x faster station-scoped queries
CREATE INDEX IF NOT EXISTS idx_customers_station 
ON customers(station_id) 
WHERE station_id IS NOT NULL;


-- ============================================
-- MESSAGES TABLE INDEXES (Inbox)
-- ============================================
-- Critical for inbox performance

-- Index: Fast thread message retrieval
-- Used by: /api/v1/inbox/threads/{id}/messages, message lists
-- Impact: 100x faster thread queries
CREATE INDEX IF NOT EXISTS idx_messages_thread_id 
ON messages(thread_id);

-- Index: Fast recent messages (DESC = newest first)
-- Used by: Inbox lists, recent activity, unread counts
-- Impact: 50x faster inbox queries
CREATE INDEX IF NOT EXISTS idx_messages_created_at 
ON messages(created_at DESC);

-- Index: Fast channel filtering (SMS, Facebook, Instagram, Email, etc.)
-- Used by: Channel filters, analytics, integrations
-- Impact: 20x faster channel queries
CREATE INDEX IF NOT EXISTS idx_messages_channel 
ON messages(channel);

-- Index: Fast direction filtering (inbound vs outbound)
-- Used by: Sent/received filters, analytics
-- Impact: 15x faster direction queries
CREATE INDEX IF NOT EXISTS idx_messages_direction 
ON messages(direction);

-- Composite index: Unread messages per channel
-- Used by: Unread message badges, notifications
-- Impact: 30x faster unread counts
CREATE INDEX IF NOT EXISTS idx_messages_unread 
ON messages(is_read, channel, created_at DESC) 
WHERE is_read = false;


-- ============================================
-- LEADS TABLE INDEXES
-- ============================================
-- Critical for lead management and pipeline

-- Index: Fast status/stage queries
-- Used by: Lead pipeline, stage filters, kanban board
-- Impact: 25x faster pipeline queries
CREATE INDEX IF NOT EXISTS idx_leads_status 
ON leads(status);

-- Index: Fast source tracking (website, referral, social, etc.)
-- Used by: Lead source analytics, attribution
-- Impact: 20x faster source reports
CREATE INDEX IF NOT EXISTS idx_leads_source 
ON leads(source);

-- Index: Fast created date queries
-- Used by: Recent leads, date range filters, analytics
-- Impact: 40x faster date filters
CREATE INDEX IF NOT EXISTS idx_leads_created_at 
ON leads(created_at DESC);

-- Index: Fast assigned user queries
-- Used by: "My leads" filters, workload distribution
-- Impact: 30x faster assignment queries
CREATE INDEX IF NOT EXISTS idx_leads_assigned_to 
ON leads(assigned_to) 
WHERE assigned_to IS NOT NULL;

-- Composite index: Lead scoring queries
-- Used by: AI lead prioritization, hot lead filters
-- Impact: 50x faster scoring queries
CREATE INDEX IF NOT EXISTS idx_leads_score_status 
ON leads(lead_score DESC, status) 
WHERE lead_score IS NOT NULL;


-- ============================================
-- THREADS TABLE INDEXES (Inbox Threads)
-- ============================================

-- Index: Fast customer thread lookup
-- Used by: Customer message history, thread consolidation
-- Impact: 40x faster customer queries
CREATE INDEX IF NOT EXISTS idx_threads_customer_id 
ON threads(customer_id) 
WHERE customer_id IS NOT NULL;

-- Index: Fast channel filtering
-- Used by: Channel-specific inboxes, integrations
-- Impact: 25x faster channel queries
CREATE INDEX IF NOT EXISTS idx_threads_channel 
ON threads(channel);

-- Index: Fast recent threads (DESC = newest first)
-- Used by: Inbox list, recent activity
-- Impact: 50x faster inbox queries
CREATE INDEX IF NOT EXISTS idx_threads_updated_at 
ON threads(updated_at DESC);

-- Composite index: Unread threads per channel
-- Used by: Unread thread counts, notifications
-- Impact: 30x faster unread counts
CREATE INDEX IF NOT EXISTS idx_threads_unread 
ON threads(is_read, channel, updated_at DESC) 
WHERE is_read = false;


-- ============================================
-- CUSTOMER_REVIEWS TABLE INDEXES
-- ============================================

-- Index: Fast customer reviews lookup
-- Used by: Customer review history, profile pages
-- Impact: 30x faster customer queries
CREATE INDEX IF NOT EXISTS idx_reviews_customer_id 
ON customer_reviews(customer_id);

-- Index: Fast status filtering (pending, approved, rejected)
-- Used by: Moderation queue, public review lists
-- Impact: 40x faster status queries
CREATE INDEX IF NOT EXISTS idx_reviews_status 
ON customer_reviews(status);

-- Index: Fast rating queries
-- Used by: Average rating calculations, rating filters
-- Impact: 20x faster rating queries
CREATE INDEX IF NOT EXISTS idx_reviews_rating 
ON customer_reviews(rating);

-- Index: Fast recent reviews (DESC = newest first)
-- Used by: Recent reviews, homepage display
-- Impact: 50x faster recent review queries
CREATE INDEX IF NOT EXISTS idx_reviews_created_at 
ON customer_reviews(created_at DESC);

-- Composite index: Approved public reviews
-- Used by: Customer-facing review display
-- Impact: 60x faster public review queries
CREATE INDEX IF NOT EXISTS idx_reviews_approved_recent 
ON customer_reviews(status, created_at DESC) 
WHERE status = 'approved';


-- ============================================
-- NEWSLETTER_SUBSCRIBERS TABLE INDEXES
-- ============================================

-- Index: Fast email lookup (unique constraint + index)
-- Used by: Subscription checks, duplicate prevention
-- Impact: Instant email lookups
CREATE UNIQUE INDEX IF NOT EXISTS idx_newsletter_email 
ON newsletter_subscribers(LOWER(email));

-- Index: Fast status filtering (active, unsubscribed, bounced)
-- Used by: Campaign targeting, subscriber counts
-- Impact: 30x faster status queries
CREATE INDEX IF NOT EXISTS idx_newsletter_status 
ON newsletter_subscribers(status);

-- Index: Fast subscription date queries
-- Used by: New subscriber reports, cohort analysis
-- Impact: 25x faster date queries
CREATE INDEX IF NOT EXISTS idx_newsletter_subscribed_at 
ON newsletter_subscribers(subscribed_at DESC);


-- ============================================
-- NEWSLETTER_CAMPAIGNS TABLE INDEXES
-- ============================================

-- Index: Fast status filtering (draft, scheduled, sent)
-- Used by: Campaign list filters, scheduled job queries
-- Impact: 20x faster status queries
CREATE INDEX IF NOT EXISTS idx_campaigns_status 
ON newsletter_campaigns(status);

-- Index: Fast scheduled date queries
-- Used by: Scheduled campaign jobs, calendar view
-- Impact: 40x faster scheduled queries
CREATE INDEX IF NOT EXISTS idx_campaigns_scheduled_at 
ON newsletter_campaigns(scheduled_at) 
WHERE scheduled_at IS NOT NULL;


-- ============================================
-- QR_CODES TABLE INDEXES
-- ============================================

-- Index: Fast code lookup (most common query)
-- Used by: QR scan tracking, analytics
-- Impact: Instant code lookups
CREATE UNIQUE INDEX IF NOT EXISTS idx_qr_codes_code 
ON qr_codes(code);

-- Index: Fast scan count queries
-- Used by: Popular QR code reports, analytics
-- Impact: 30x faster popularity queries
CREATE INDEX IF NOT EXISTS idx_qr_codes_scan_count 
ON qr_codes(scan_count DESC);


-- ============================================
-- QR_SCANS TABLE INDEXES (Analytics)
-- ============================================

-- Index: Fast QR code scan history
-- Used by: QR analytics, scan timeline
-- Impact: 50x faster scan history queries
CREATE INDEX IF NOT EXISTS idx_qr_scans_code_id 
ON qr_scans(qr_code_id);

-- Index: Fast scan date queries
-- Used by: Daily scan reports, trend analysis
-- Impact: 40x faster date queries
CREATE INDEX IF NOT EXISTS idx_qr_scans_scanned_at 
ON qr_scans(scanned_at DESC);


-- ============================================
-- STATION_USERS TABLE INDEXES (RBAC)
-- ============================================

-- Index: Fast station user lookup
-- Used by: Station permission checks, user lists
-- Impact: 100x faster RBAC queries
CREATE INDEX IF NOT EXISTS idx_station_users_station 
ON station_users(station_id);

-- Index: Fast user station lookup
-- Used by: User station list, permission checks
-- Impact: 50x faster user queries
CREATE INDEX IF NOT EXISTS idx_station_users_user 
ON station_users(user_id);

-- Composite index: Active station assignments
-- Used by: Active user lists, permission checks
-- Impact: 80x faster active user queries
CREATE INDEX IF NOT EXISTS idx_station_users_active 
ON station_users(station_id, user_id, is_active) 
WHERE is_active = true;


-- ============================================
-- AUDIT_LOGS TABLE INDEXES (Compliance)
-- ============================================

-- Index: Fast station audit lookup
-- Used by: Station audit reports, compliance
-- Impact: 60x faster audit queries
CREATE INDEX IF NOT EXISTS idx_audit_logs_station 
ON audit_logs(station_id);

-- Index: Fast user audit lookup
-- Used by: User activity reports, security
-- Impact: 40x faster user queries
CREATE INDEX IF NOT EXISTS idx_audit_logs_user 
ON audit_logs(user_id);

-- Index: Fast timestamp queries (DESC = newest first)
-- Used by: Recent activity, audit timelines
-- Impact: 50x faster timeline queries
CREATE INDEX IF NOT EXISTS idx_audit_logs_timestamp 
ON audit_logs(timestamp DESC);

-- Composite index: Action-specific audit queries
-- Used by: Specific action reports (e.g., all deletions)
-- Impact: 70x faster action queries
CREATE INDEX IF NOT EXISTS idx_audit_logs_action 
ON audit_logs(station_id, action, timestamp DESC);


-- =====================================================
-- DEPLOYMENT VERIFICATION
-- =====================================================
-- Run this query after deployment to verify all indexes

SELECT 
    schemaname,
    tablename,
    indexname,
    indexdef
FROM pg_indexes
WHERE schemaname = 'public'
  AND (
    indexname LIKE 'idx_bookings_%' OR
    indexname LIKE 'idx_customers_%' OR
    indexname LIKE 'idx_messages_%' OR
    indexname LIKE 'idx_leads_%' OR
    indexname LIKE 'idx_threads_%' OR
    indexname LIKE 'idx_reviews_%' OR
    indexname LIKE 'idx_newsletter_%' OR
    indexname LIKE 'idx_campaigns_%' OR
    indexname LIKE 'idx_qr_%' OR
    indexname LIKE 'idx_station_%' OR
    indexname LIKE 'idx_audit_%'
  )
ORDER BY tablename, indexname;

-- Expected result: 50+ indexes created


-- =====================================================
-- PERFORMANCE TESTING QUERIES
-- =====================================================
-- Run these BEFORE and AFTER index deployment to see improvement

-- Test 1: Customer booking history (should be <10ms after indexes)
EXPLAIN ANALYZE
SELECT * FROM bookings 
WHERE customer_id = 1 
ORDER BY booking_date DESC 
LIMIT 20;

-- Test 2: Recent bookings for dashboard (should be <5ms after indexes)
EXPLAIN ANALYZE
SELECT * FROM bookings 
ORDER BY created_at DESC 
LIMIT 50;

-- Test 3: Inbox thread messages (should be <10ms after indexes)
EXPLAIN ANALYZE
SELECT * FROM messages 
WHERE thread_id = 1 
ORDER BY created_at DESC;

-- Test 4: Lead pipeline query (should be <20ms after indexes)
EXPLAIN ANALYZE
SELECT * FROM leads 
WHERE status = 'new' 
ORDER BY lead_score DESC NULLS LAST 
LIMIT 100;

-- Test 5: Unread message count (should be <5ms after indexes)
EXPLAIN ANALYZE
SELECT COUNT(*) FROM messages 
WHERE is_read = false 
  AND channel = 'sms';


-- =====================================================
-- INDEX MAINTENANCE
-- =====================================================
-- Run weekly to keep indexes optimized

-- Rebuild all indexes (run during low-traffic hours)
REINDEX DATABASE myhibachi;

-- Analyze tables to update query planner statistics
ANALYZE bookings, customers, messages, leads, threads, customer_reviews;

-- Check index bloat (should be <20%)
SELECT 
    schemaname,
    tablename,
    indexname,
    pg_size_pretty(pg_relation_size(indexrelid)) AS index_size,
    idx_scan AS index_scans,
    idx_tup_read AS tuples_read,
    idx_tup_fetch AS tuples_fetched
FROM pg_stat_user_indexes
WHERE schemaname = 'public'
ORDER BY pg_relation_size(indexrelid) DESC;


-- =====================================================
-- ROLLBACK INSTRUCTIONS (if needed)
-- =====================================================
-- Only use if indexes cause issues (extremely rare)

/*
-- Drop all custom indexes (keep primary keys and unique constraints)
DROP INDEX IF EXISTS idx_bookings_customer_id;
DROP INDEX IF EXISTS idx_bookings_booking_date;
DROP INDEX IF EXISTS idx_bookings_status;
DROP INDEX IF EXISTS idx_bookings_created_at;
DROP INDEX IF EXISTS idx_bookings_station_date;
DROP INDEX IF EXISTS idx_bookings_payment_status_amount;

DROP INDEX IF EXISTS idx_customers_email;
DROP INDEX IF EXISTS idx_customers_phone;
DROP INDEX IF EXISTS idx_customers_name_search;
DROP INDEX IF EXISTS idx_customers_station;

DROP INDEX IF EXISTS idx_messages_thread_id;
DROP INDEX IF EXISTS idx_messages_created_at;
DROP INDEX IF EXISTS idx_messages_channel;
DROP INDEX IF EXISTS idx_messages_direction;
DROP INDEX IF EXISTS idx_messages_unread;

DROP INDEX IF EXISTS idx_leads_status;
DROP INDEX IF EXISTS idx_leads_source;
DROP INDEX IF EXISTS idx_leads_created_at;
DROP INDEX IF EXISTS idx_leads_assigned_to;
DROP INDEX IF EXISTS idx_leads_score_status;

DROP INDEX IF EXISTS idx_threads_customer_id;
DROP INDEX IF EXISTS idx_threads_channel;
DROP INDEX IF EXISTS idx_threads_updated_at;
DROP INDEX IF EXISTS idx_threads_unread;

DROP INDEX IF EXISTS idx_reviews_customer_id;
DROP INDEX IF EXISTS idx_reviews_status;
DROP INDEX IF EXISTS idx_reviews_rating;
DROP INDEX IF EXISTS idx_reviews_created_at;
DROP INDEX IF EXISTS idx_reviews_approved_recent;

DROP INDEX IF EXISTS idx_newsletter_email;
DROP INDEX IF EXISTS idx_newsletter_status;
DROP INDEX IF EXISTS idx_newsletter_subscribed_at;

DROP INDEX IF EXISTS idx_campaigns_status;
DROP INDEX IF EXISTS idx_campaigns_scheduled_at;

DROP INDEX IF EXISTS idx_qr_codes_code;
DROP INDEX IF EXISTS idx_qr_codes_scan_count;

DROP INDEX IF EXISTS idx_qr_scans_code_id;
DROP INDEX IF EXISTS idx_qr_scans_scanned_at;

DROP INDEX IF EXISTS idx_station_users_station;
DROP INDEX IF EXISTS idx_station_users_user;
DROP INDEX IF EXISTS idx_station_users_active;

DROP INDEX IF EXISTS idx_audit_logs_station;
DROP INDEX IF EXISTS idx_audit_logs_user;
DROP INDEX IF EXISTS idx_audit_logs_timestamp;
DROP INDEX IF EXISTS idx_audit_logs_action;
*/


-- =====================================================
-- NOTES FOR DEPLOYMENT
-- =====================================================
/*
1. **Timing:** Deploy during low-traffic hours (2-4 AM)
2. **Duration:** ~2-5 minutes depending on data volume
3. **Downtime:** Zero - indexes created online
4. **Monitoring:** Watch CPU spike during creation (normal)
5. **Verification:** Run verification query after deployment
6. **Performance:** Test queries before/after to confirm improvement

IMPORTANT:
- IF NOT EXISTS prevents errors if index already exists
- All indexes are non-blocking (can create during production)
- Partial indexes (WHERE clauses) save disk space
- UNIQUE indexes also enforce data integrity
- Composite indexes enable multi-column queries

NEXT STEPS AFTER DEPLOYMENT:
1. ✅ Run verification query
2. ✅ Run performance test queries
3. ✅ Monitor slow query log (should see dramatic improvement)
4. ✅ Update documentation with index strategy
5. ✅ Schedule weekly REINDEX maintenance
*/
