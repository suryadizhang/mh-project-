# 📊 PRODUCTION MONITORING QUERIES

## Phase 2A+2C Performance Optimization

**Purpose:** Monitor performance, health, and success of Phase 2
deployment  
**Database:** PostgreSQL (Supabase)  
**Last Updated:** November 2, 2025

---

## 🎯 QUICK HEALTH CHECK (Run First)

### 1. Overall System Health

```sql
-- Quick health snapshot
SELECT
    'AI Messages (24h)' as metric,
    COUNT(*) as value
FROM ai_messages
WHERE created_at >= NOW() - INTERVAL '24 hours'

UNION ALL

SELECT
    'Emotion Records (24h)',
    COUNT(*)
FROM emotion_history
WHERE created_at >= NOW() - INTERVAL '24 hours'

UNION ALL

SELECT
    'Active Conversations (24h)',
    COUNT(DISTINCT conversation_id)
FROM ai_messages
WHERE created_at >= NOW() - INTERVAL '24 hours'

UNION ALL

SELECT
    'Database Size (MB)',
    ROUND(pg_database_size(current_database()) / 1024.0 / 1024.0, 2)::numeric;
```

**Expected Results:**

- AI Messages: Should match production volume
- Emotion Records: Should be ~100% of AI Messages
- Active Conversations: Normal user engagement
- Database Size: Stable growth

---

## ⚡ PERFORMANCE MONITORING

### 2. Query Performance (PostgreSQL Stats)

```sql
-- Top 10 slowest queries affecting new features
SELECT
    substring(query from 1 for 80) as query_start,
    calls,
    ROUND(mean_exec_time::numeric, 2) as avg_time_ms,
    ROUND(max_exec_time::numeric, 2) as max_time_ms,
    ROUND(total_exec_time::numeric, 2) as total_time_ms
FROM pg_stat_statements
WHERE query ILIKE ANY(ARRAY[
    '%ai_messages%',
    '%ai_conversations%',
    '%emotion_history%',
    '%bookings%'
])
    AND query NOT LIKE '%pg_stat_statements%'
ORDER BY mean_exec_time DESC
LIMIT 10;
```

**Expected Results:**

- avg_time_ms < 100ms for SELECT queries
- avg_time_ms < 200ms for INSERT queries
- max_time_ms < 500ms for all queries

**Alert If:**

- Any query avg_time_ms > 300ms
- Any query max_time_ms > 1000ms

---

### 3. Index Usage Analysis

```sql
-- Verify indexes are being used (not just existing)
SELECT
    schemaname,
    tablename,
    indexname,
    idx_scan as times_used,
    idx_tup_read as rows_read,
    idx_tup_fetch as rows_fetched
FROM pg_stat_user_indexes
WHERE indexname LIKE 'idx_%'
    AND schemaname IN ('core', 'identity', 'lead', 'newsletter', 'integra', 'feedback')
    AND (tablename = 'ai_messages' OR tablename = 'ai_conversations' OR tablename = 'emotion_history')
ORDER BY idx_scan DESC;
```

**Expected Results:**

- idx_scan > 0 for all indexes (means they're being used)
- High idx_scan for conversation_id, customer_id indexes

**Alert If:**

- idx_scan = 0 for primary indexes (not being used)
- idx_tup_read very high but idx_tup_fetch low (inefficient index)

---

### 4. Table Size & Growth Rate

```sql
-- Monitor table growth (run daily to compare)
SELECT
    schemaname,
    tablename,
    pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) as total_size,
    pg_size_pretty(pg_relation_size(schemaname||'.'||tablename)) as table_size,
    pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename) - pg_relation_size(schemaname||'.'||tablename)) as indexes_size,
    n_live_tup as row_count
FROM pg_stat_user_tables
WHERE tablename IN ('ai_messages', 'ai_conversations', 'emotion_history', 'bookings')
ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;
```

**Expected Results:**

- Steady growth proportional to user activity
- Indexes ~10-30% of table size

**Alert If:**

- Growth rate >1GB/day unexpectedly
- Indexes >50% of table size

---

## 📈 BUSINESS METRICS

### 5. AI Message Volume & Response Time

```sql
-- Daily message volume with conversation breakdown
SELECT
    DATE(created_at) as date,
    COUNT(*) as total_messages,
    COUNT(DISTINCT conversation_id) as unique_conversations,
    ROUND(COUNT(*)::numeric / COUNT(DISTINCT conversation_id), 2) as avg_messages_per_conversation,
    COUNT(CASE WHEN role = 'user' THEN 1 END) as user_messages,
    COUNT(CASE WHEN role = 'assistant' THEN 1 END) as ai_messages
FROM ai_messages
WHERE created_at >= NOW() - INTERVAL '7 days'
GROUP BY DATE(created_at)
ORDER BY date DESC;
```

**Expected Results:**

- Stable or growing message volume
- avg_messages_per_conversation: 3-8 (normal conversation)
- user_messages ≈ ai_messages (balanced conversation)

---

### 6. Emotion Detection Coverage

```sql
-- Verify emotion detection running on all messages
SELECT
    DATE(m.created_at) as date,
    COUNT(m.id) as total_messages,
    COUNT(e.id) as messages_with_emotion,
    ROUND(100.0 * COUNT(e.id) / COUNT(m.id), 2) as coverage_percent
FROM ai_messages m
LEFT JOIN emotion_history e ON e.conversation_id = m.conversation_id
    AND DATE(e.created_at) = DATE(m.created_at)
WHERE m.created_at >= NOW() - INTERVAL '7 days'
GROUP BY DATE(m.created_at)
ORDER BY date DESC;
```

**Expected Results:**

- coverage_percent: 95-100% (emotion detection working)

**Alert If:**

- coverage_percent < 90% (background tasks failing)

---

### 7. Emotion Distribution Analysis

```sql
-- Analyze customer emotions (JSON extraction)
SELECT
    DATE(created_at) as date,
    emotion_data->>'primary_emotion' as emotion,
    COUNT(*) as count,
    ROUND(AVG((emotion_data->>'intensity')::numeric), 2) as avg_intensity
FROM emotion_history
WHERE created_at >= NOW() - INTERVAL '7 days'
    AND emotion_data IS NOT NULL
GROUP BY DATE(created_at), emotion_data->>'primary_emotion'
ORDER BY date DESC, count DESC;
```

**Expected Results:**

- Mostly positive/neutral emotions
- Negative emotions <20%
- High intensity negatives flagged for review

**Alert If:**

- Negative emotions >30% (customer satisfaction issue)
- High intensity negative emotions increasing

---

### 8. Booking Performance & Follow-ups

```sql
-- Booking creation with follow-up scheduling
SELECT
    DATE(created_at) as date,
    COUNT(*) as total_bookings,
    COUNT(CASE WHEN status = 'confirmed' THEN 1 END) as confirmed_bookings,
    COUNT(CASE WHEN status = 'pending' THEN 1 END) as pending_bookings,
    ROUND(100.0 * COUNT(CASE WHEN status = 'confirmed' THEN 1 END) / COUNT(*), 2) as confirmation_rate
FROM bookings
WHERE created_at >= NOW() - INTERVAL '7 days'
GROUP BY DATE(created_at)
ORDER BY date DESC;
```

**Expected Results:**

- confirmation_rate: >80%
- No increase in pending bookings

---

## 🔍 BACKGROUND TASK MONITORING

### 9. Background Task Success Rate

```sql
-- Compare message creation to emotion processing
-- (They should be nearly equal if background tasks working)
WITH message_counts AS (
    SELECT
        DATE(created_at) as date,
        COUNT(*) as messages
    FROM ai_messages
    WHERE created_at >= NOW() - INTERVAL '7 days'
    GROUP BY DATE(created_at)
),
emotion_counts AS (
    SELECT
        DATE(created_at) as date,
        COUNT(*) as emotions
    FROM emotion_history
    WHERE created_at >= NOW() - INTERVAL '7 days'
    GROUP BY DATE(created_at)
)
SELECT
    m.date,
    m.messages,
    COALESCE(e.emotions, 0) as emotions,
    ROUND(100.0 * COALESCE(e.emotions, 0) / m.messages, 2) as success_rate_percent
FROM message_counts m
LEFT JOIN emotion_counts e ON m.date = e.date
ORDER BY m.date DESC;
```

**Expected Results:**

- success_rate_percent: 95-100%

**Alert If:**

- success_rate_percent < 90% (background tasks failing)
- Gap between messages and emotions growing

---

### 10. Background Task Latency

```sql
-- Check if emotion records are created promptly after messages
SELECT
    DATE(m.created_at) as date,
    ROUND(AVG(EXTRACT(EPOCH FROM (e.created_at - m.created_at))), 2) as avg_delay_seconds,
    ROUND(MAX(EXTRACT(EPOCH FROM (e.created_at - m.created_at))), 2) as max_delay_seconds,
    COUNT(*) as sample_size
FROM ai_messages m
JOIN emotion_history e ON e.conversation_id = m.conversation_id
    AND e.created_at >= m.created_at
    AND e.created_at <= m.created_at + INTERVAL '10 minutes'
WHERE m.created_at >= NOW() - INTERVAL '7 days'
GROUP BY DATE(m.created_at)
ORDER BY date DESC;
```

**Expected Results:**

- avg_delay_seconds: 1-5 seconds (background task executing quickly)
- max_delay_seconds: <30 seconds

**Alert If:**

- avg_delay_seconds > 30 seconds
- max_delay_seconds > 300 seconds (5 minutes)

---

## 🚨 ERROR MONITORING

### 11. Failed Queries & Errors

```sql
-- Check for query errors in pg_stat_database
SELECT
    datname,
    xact_rollback as transactions_rolled_back,
    conflicts as conflicts_detected,
    deadlocks as deadlock_count,
    temp_files as temp_files_created,
    temp_bytes as temp_bytes_used
FROM pg_stat_database
WHERE datname = current_database();
```

**Expected Results:**

- xact_rollback: Low (< 1% of total transactions)
- conflicts: 0
- deadlocks: 0

**Alert If:**

- deadlocks > 0 (database contention issue)
- xact_rollback increasing rapidly

---

### 12. Connection Pool Status

```sql
-- Monitor database connections
SELECT
    COUNT(*) as total_connections,
    COUNT(CASE WHEN state = 'active' THEN 1 END) as active_connections,
    COUNT(CASE WHEN state = 'idle' THEN 1 END) as idle_connections,
    COUNT(CASE WHEN state = 'idle in transaction' THEN 1 END) as idle_in_transaction,
    MAX(EXTRACT(EPOCH FROM (NOW() - state_change))) as longest_idle_seconds
FROM pg_stat_activity
WHERE datname = current_database()
    AND pid != pg_backend_pid();
```

**Expected Results:**

- total_connections: <50% of max (usually 20/100)
- active_connections: 1-10 (normal activity)
- idle_in_transaction: 0 (no stuck transactions)
- longest_idle_seconds: <300 (5 minutes)

**Alert If:**

- total_connections >80% of max
- idle_in_transaction >5 (transaction leaks)
- longest_idle_seconds >600 (10 minutes)

---

## 📊 OPTIMIZATION VALIDATION

### 13. UPSERT Performance (Phase 2A.2)

```sql
-- Verify UPSERT is faster than SELECT+INSERT
-- Check conversation creation timing
SELECT
    DATE(created_at) as date,
    COUNT(*) as conversations_created,
    COUNT(DISTINCT thread_id) as unique_threads
FROM ai_conversations
WHERE created_at >= NOW() - INTERVAL '7 days'
GROUP BY DATE(created_at)
ORDER BY date DESC;
```

**Validation:**

- Should see no race condition duplicates
- Conversation creation should be instantaneous

---

### 14. Background Task Effectiveness (Phase 2A.3)

```sql
-- Verify emotion stats are not blocking message storage
-- Check for any messages without emotion analysis
SELECT
    COUNT(*) as messages_without_emotion,
    ROUND(100.0 * COUNT(*) / (SELECT COUNT(*) FROM ai_messages WHERE created_at >= NOW() - INTERVAL '24 hours'), 2) as percent_missing
FROM ai_messages m
LEFT JOIN emotion_history e ON e.conversation_id = m.conversation_id
    AND e.created_at >= m.created_at
    AND e.created_at <= m.created_at + INTERVAL '1 hour'
WHERE m.created_at >= NOW() - INTERVAL '24 hours'
    AND e.id IS NULL;
```

**Expected Results:**

- messages_without_emotion: <5% (some legitimate misses due to timing)

**Alert If:**

- percent_missing >10% (background tasks not running)

---

## 🎯 ALERTING THRESHOLDS

### Critical Alerts (Page On-Call)

```sql
-- Run every 5 minutes
-- Alert if ANY of these conditions true:

-- 1. Response time degradation
SELECT 'CRITICAL: Slow queries detected' as alert
FROM pg_stat_statements
WHERE mean_exec_time > 1000 -- 1 second
    AND calls > 10
    AND query ILIKE ANY(ARRAY['%ai_messages%', '%bookings%'])
LIMIT 1;

-- 2. Background task failure
SELECT 'CRITICAL: Background tasks failing' as alert
WHERE (
    SELECT COUNT(*) FROM ai_messages WHERE created_at >= NOW() - INTERVAL '1 hour'
) * 0.9 > (
    SELECT COUNT(*) FROM emotion_history WHERE created_at >= NOW() - INTERVAL '1 hour'
);

-- 3. Database connection exhaustion
SELECT 'CRITICAL: Connection pool exhausted' as alert
WHERE (
    SELECT COUNT(*) FROM pg_stat_activity WHERE datname = current_database()
) > 80; -- Assuming max 100 connections

-- 4. Deadlocks detected
SELECT 'CRITICAL: Deadlocks detected' as alert
FROM pg_stat_database
WHERE datname = current_database()
    AND deadlocks > 0;
```

### Warning Alerts (Notify Team)

```sql
-- Run every 15 minutes

-- 1. Increasing error rate
SELECT 'WARNING: Error rate increasing' as alert
WHERE (
    SELECT xact_rollback::float / NULLIF(xact_commit + xact_rollback, 0)
    FROM pg_stat_database
    WHERE datname = current_database()
) > 0.05; -- 5% rollback rate

-- 2. Slow background task processing
SELECT 'WARNING: Background task latency high' as alert
WHERE (
    SELECT AVG(EXTRACT(EPOCH FROM (e.created_at - m.created_at)))
    FROM ai_messages m
    JOIN emotion_history e ON e.conversation_id = m.conversation_id
    WHERE m.created_at >= NOW() - INTERVAL '1 hour'
) > 60; -- 60 seconds average delay

-- 3. High database load
SELECT 'WARNING: Database load high' as alert
WHERE (
    SELECT COUNT(*) FROM pg_stat_activity
    WHERE state = 'active' AND datname = current_database()
) > 20; -- 20 concurrent active queries
```

---

## 📅 SCHEDULED MONITORING

### Hourly (First 24 Hours Post-Deployment)

- [ ] Run Quick Health Check (#1)
- [ ] Check Query Performance (#2)
- [ ] Verify Background Task Success (#9)

### Daily (First Week)

- [ ] AI Message Volume (#5)
- [ ] Emotion Detection Coverage (#6)
- [ ] Booking Performance (#8)
- [ ] Table Size & Growth (#4)

### Weekly (Ongoing)

- [ ] Index Usage Analysis (#3)
- [ ] Emotion Distribution (#7)
- [ ] Full Performance Review
- [ ] Optimization Validation (#13, #14)

---

## 🔧 TROUBLESHOOTING QUERIES

### If Response Times Are Slow

```sql
-- Find blocking queries
SELECT
    pid,
    now() - pg_stat_activity.query_start AS duration,
    query,
    state,
    wait_event_type,
    wait_event
FROM pg_stat_activity
WHERE state != 'idle'
    AND query NOT ILIKE '%pg_stat_activity%'
ORDER BY duration DESC;
```

### If Background Tasks Failing

```sql
-- Check for recent errors (requires application logging)
-- Adjust based on your logging setup
SELECT * FROM application_logs
WHERE level = 'ERROR'
    AND message ILIKE '%emotion%'
    AND created_at >= NOW() - INTERVAL '1 hour'
ORDER BY created_at DESC
LIMIT 20;
```

### If Database Growing Too Fast

```sql
-- Find largest tables
SELECT
    schemaname,
    tablename,
    pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) as size,
    n_live_tup as rows
FROM pg_stat_user_tables
ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC
LIMIT 10;
```

---

## 📞 ESCALATION

**If metrics outside expected ranges:**

1. **Critical Alerts** → Immediate rollback (see
   PRODUCTION_DEPLOYMENT_CHECKLIST.md)
2. **Warning Alerts** → Investigate within 30 minutes
3. **Informational** → Review within 24 hours

**Contact:**

- On-Call Engineer: ******\_******
- Database Admin: ******\_******
- Team Lead: ******\_******

---

**Last Updated:** November 2, 2025  
**Version:** 1.0  
**Status:** Production Ready ✅
