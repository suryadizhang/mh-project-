-- Script: check_schema_health.sql
-- Purpose: Quick health check for database schema and permissions
-- Usage: Run from admin portal or scheduled task to detect issues early
--
-- Run with: sudo -u postgres psql -d myhibachi_production -f check_schema_health.sql

\echo '=============================================='
\echo 'MY HIBACHI - DATABASE SCHEMA HEALTH CHECK'
\echo '=============================================='
\echo ''

-- Check 1: Tables with missing permissions
\echo '📋 CHECK 1: Tables with MISSING permissions for myhibachi_user'
\echo '----------------------------------------------------------------'

SELECT
    schemaname || '.' || tablename AS table_name,
    CASE WHEN NOT has_table_privilege('myhibachi_user', schemaname || '.' || tablename, 'SELECT') THEN '❌ NO SELECT' ELSE '✅' END AS sel,
    CASE WHEN NOT has_table_privilege('myhibachi_user', schemaname || '.' || tablename, 'INSERT') THEN '❌ NO INSERT' ELSE '✅' END AS ins
FROM pg_tables
WHERE schemaname IN ('core', 'identity', 'audit', 'communications', 'crm', 'lead', 'newsletter', 'ai')
  AND (
    NOT has_table_privilege('myhibachi_user', schemaname || '.' || tablename, 'SELECT')
    OR NOT has_table_privilege('myhibachi_user', schemaname || '.' || tablename, 'INSERT')
  )
ORDER BY schemaname, tablename;

\echo ''
\echo '📋 CHECK 2: Stations without geocoding'
\echo '----------------------------------------------------------------'

SELECT
    code,
    name,
    status,
    CASE
        WHEN lat IS NULL OR lng IS NULL THEN '❌ NOT GEOCODED'
        WHEN geocode_status != 'success' THEN '⚠️ ' || COALESCE(geocode_status, 'unknown')
        ELSE '✅ ' || ROUND(lat::numeric, 4) || ', ' || ROUND(lng::numeric, 4)
    END AS geocode_status
FROM identity.stations
WHERE status = 'active'
ORDER BY name;

\echo ''
\echo '📋 CHECK 3: Permission auto-grant trigger status'
\echo '----------------------------------------------------------------'

SELECT
    evtname AS trigger_name,
    evtevent AS event,
    evtenabled AS enabled
FROM pg_event_trigger
WHERE evtname = 'trg_auto_grant_permissions';

\echo ''
\echo '📋 CHECK 4: Schema summary'
\echo '----------------------------------------------------------------'

SELECT
    n.nspname AS schema_name,
    COUNT(*) AS table_count
FROM pg_class c
JOIN pg_namespace n ON n.oid = c.relnamespace
WHERE c.relkind = 'r' AND n.nspname IN ('core', 'identity', 'audit', 'communications', 'crm', 'lead', 'newsletter', 'ai')
GROUP BY n.nspname
ORDER BY n.nspname;

\echo ''
\echo '=============================================='
\echo 'HEALTH CHECK COMPLETE'
\echo '=============================================='
