-- Migration: 029_auto_grant_permissions_trigger.sql
-- Description: Automatically grant permissions to myhibachi_user when new tables are created
-- Purpose: Prevent "permission denied" errors when new tables are added to managed schemas
-- Created: 2026-02-05
--
-- How it works:
-- 1. An event trigger fires AFTER any CREATE TABLE in managed schemas
-- 2. The trigger function grants SELECT, INSERT, UPDATE, DELETE to myhibachi_user
-- 3. Also grants USAGE on any sequences created with the table
--
-- Managed schemas: core, identity, audit, communications, crm, lead, newsletter, ai

-- ============================================================================
-- STEP 1: Create the trigger function
-- ============================================================================

CREATE OR REPLACE FUNCTION public.auto_grant_permissions_on_new_table()
RETURNS event_trigger
LANGUAGE plpgsql
SECURITY DEFINER
AS $$
DECLARE
    obj record;
    managed_schemas text[] := ARRAY['core', 'identity', 'audit', 'communications', 'crm', 'lead', 'newsletter', 'ai'];
    schema_name text;
    table_name text;
BEGIN
    -- Loop through all objects created in this transaction
    FOR obj IN SELECT * FROM pg_event_trigger_ddl_commands()
    LOOP
        -- Only process tables
        IF obj.object_type = 'table' THEN
            -- Extract schema and table name
            schema_name := split_part(obj.object_identity, '.', 1);
            table_name := split_part(obj.object_identity, '.', 2);

            -- Only grant on managed schemas
            IF schema_name = ANY(managed_schemas) THEN
                -- Grant permissions to production user
                EXECUTE format('GRANT SELECT, INSERT, UPDATE, DELETE ON %I.%I TO myhibachi_user', schema_name, table_name);

                -- Grant permissions to staging user (if exists)
                BEGIN
                    EXECUTE format('GRANT SELECT, INSERT, UPDATE, DELETE ON %I.%I TO myhibachi_staging_user', schema_name, table_name);
                EXCEPTION WHEN undefined_object THEN
                    -- Staging user doesn't exist in production, ignore
                    NULL;
                END;

                RAISE NOTICE 'Auto-granted permissions on %.% to myhibachi_user', schema_name, table_name;
            END IF;
        END IF;

        -- Also handle sequences (for SERIAL/BIGSERIAL columns)
        IF obj.object_type = 'sequence' THEN
            schema_name := split_part(obj.object_identity, '.', 1);

            IF schema_name = ANY(managed_schemas) THEN
                EXECUTE format('GRANT USAGE ON %s TO myhibachi_user', obj.object_identity);

                BEGIN
                    EXECUTE format('GRANT USAGE ON %s TO myhibachi_staging_user', obj.object_identity);
                EXCEPTION WHEN undefined_object THEN
                    NULL;
                END;
            END IF;
        END IF;
    END LOOP;
END;
$$;

-- ============================================================================
-- STEP 2: Create the event trigger
-- ============================================================================

-- Drop if exists (for idempotency)
DROP EVENT TRIGGER IF EXISTS trg_auto_grant_permissions;

-- Create the event trigger
CREATE EVENT TRIGGER trg_auto_grant_permissions
ON ddl_command_end
WHEN TAG IN ('CREATE TABLE', 'CREATE SEQUENCE')
EXECUTE FUNCTION public.auto_grant_permissions_on_new_table();

-- ============================================================================
-- STEP 3: Verify trigger is active
-- ============================================================================

-- You can verify with:
-- SELECT evtname, evtevent, evtenabled FROM pg_event_trigger WHERE evtname = 'trg_auto_grant_permissions';

-- ============================================================================
-- TESTING (Run manually to verify)
-- ============================================================================
--
-- -- Create a test table
-- CREATE TABLE core.test_auto_grant (id SERIAL PRIMARY KEY, name TEXT);
--
-- -- Check permissions
-- SELECT has_table_privilege('myhibachi_user', 'core.test_auto_grant', 'SELECT');
-- -- Should return: t (true)
--
-- -- Clean up
-- DROP TABLE core.test_auto_grant;

-- ============================================================================
-- ROLLBACK (if needed)
-- ============================================================================
--
-- DROP EVENT TRIGGER IF EXISTS trg_auto_grant_permissions;
-- DROP FUNCTION IF EXISTS public.auto_grant_permissions_on_new_table();
