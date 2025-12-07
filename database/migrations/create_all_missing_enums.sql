-- Comprehensive enum creation for all schemas
-- This file creates all missing PostgreSQL enum types for the MyHibachi backend

-- ========== NEWSLETTER SCHEMA ==========
-- sms_queue_status (needed for newsletter.sms_send_queue)
DO $$ BEGIN
    CREATE TYPE newsletter.sms_queue_status AS ENUM ('pending', 'sending', 'sent', 'failed', 'cancelled');
EXCEPTION
    WHEN duplicate_object THEN NULL;
END $$;

-- sms_delivery_status (needed for newsletter.sms_delivery_events)
DO $$ BEGIN
    CREATE TYPE newsletter.sms_delivery_status AS ENUM ('queued', 'sending', 'sent', 'delivered', 'failed', 'undelivered');
EXCEPTION
    WHEN duplicate_object THEN NULL;
END $$;

-- campaign_channel (needed for newsletter.campaigns)
DO $$ BEGIN
    CREATE TYPE newsletter.campaign_channel AS ENUM ('email', 'sms', 'both');
EXCEPTION
    WHEN duplicate_object THEN NULL;
END $$;

-- campaign_status (needed for newsletter.campaigns)
DO $$ BEGIN
    CREATE TYPE newsletter.campaign_status AS ENUM ('draft', 'scheduled', 'sending', 'sent', 'cancelled');
EXCEPTION
    WHEN duplicate_object THEN NULL;
END $$;

-- campaign_event_type (needed for newsletter.campaign_events)
DO $$ BEGIN
    CREATE TYPE newsletter.campaign_event_type AS ENUM ('sent', 'delivered', 'opened', 'clicked', 'replied', 'bounced', 'unsubscribed', 'complained');
EXCEPTION
    WHEN duplicate_object THEN NULL;
END $$;

-- ========== INTEGRA SCHEMA ==========
-- payment_provider (needed for integra.payment_events)
DO $$ BEGIN
    CREATE TYPE integra.payment_provider AS ENUM ('stripe', 'plaid', 'manual');
EXCEPTION
    WHEN duplicate_object THEN NULL;
END $$;

-- payment_method (needed for integra.payment_events)
DO $$ BEGIN
    CREATE TYPE integra.payment_method AS ENUM ('card', 'ach', 'venmo', 'zelle', 'cash', 'check');
EXCEPTION
    WHEN duplicate_object THEN NULL;
END $$;

-- match_status (needed for integra.payment_matches)
DO $$ BEGIN
    CREATE TYPE integra.match_status AS ENUM ('auto', 'manual', 'ignored');
EXCEPTION
    WHEN duplicate_object THEN NULL;
END $$;

-- call_direction (needed for integra.call_sessions)
DO $$ BEGIN
    CREATE TYPE integra.call_direction AS ENUM ('inbound', 'outbound');
EXCEPTION
    WHEN duplicate_object THEN NULL;
END $$;

-- social_platform (needed for integra.social_inbox)
DO $$ BEGIN
    CREATE TYPE integra.social_platform AS ENUM ('instagram', 'facebook', 'google_business', 'yelp', 'tiktok', 'twitter');
EXCEPTION
    WHEN duplicate_object THEN NULL;
END $$;

-- ========== MARKETING SCHEMA ==========
-- qr_code_type (needed for marketing.qr_codes)
DO $$ BEGIN
    CREATE TYPE marketing.qr_code_type AS ENUM ('menu', 'booking', 'review', 'promotion', 'event');
EXCEPTION
    WHEN duplicate_object THEN NULL;
END $$;

-- ========== FEEDBACK SCHEMA ==========
-- coupon_status (needed for feedback.discount_coupons)
DO $$ BEGIN
    CREATE TYPE feedback.coupon_status AS ENUM ('active', 'used', 'expired', 'revoked');
EXCEPTION
    WHEN duplicate_object THEN NULL;
END $$;

-- ========== CRM SCHEMA ==========
-- contact_type (needed for crm.contacts)
DO $$ BEGIN
    CREATE TYPE crm.contact_type AS ENUM ('customer', 'lead', 'vendor', 'partner', 'other');
EXCEPTION
    WHEN duplicate_object THEN NULL;
END $$;

-- contact_status (needed for crm.contacts)
DO $$ BEGIN
    CREATE TYPE crm.contact_status AS ENUM ('active', 'inactive', 'archived');
EXCEPTION
    WHEN duplicate_object THEN NULL;
END $$;

-- ========== LEAD SCHEMA ==========
-- lead_source (needed for lead.leads)
DO $$ BEGIN
    CREATE TYPE lead.lead_source AS ENUM ('website', 'referral', 'social_media', 'advertisement', 'event', 'partner', 'other');
EXCEPTION
    WHEN duplicate_object THEN NULL;
END $$;

-- lead_status (needed for lead.leads)
DO $$ BEGIN
    CREATE TYPE lead.lead_status AS ENUM ('new', 'contacted', 'qualified', 'proposal', 'negotiation', 'won', 'lost');
EXCEPTION
    WHEN duplicate_object THEN NULL;
END $$;

-- lead_quality (needed for lead.leads)
DO $$ BEGIN
    CREATE TYPE lead.lead_quality AS ENUM ('hot', 'warm', 'cold', 'unknown');
EXCEPTION
    WHEN duplicate_object THEN NULL;
END $$;

-- ========== EVENTS SCHEMA ==========
-- outbox_status (needed for events.outbox)
DO $$ BEGIN
    CREATE TYPE events.outbox_status AS ENUM ('pending', 'processing', 'completed', 'failed', 'retry');
EXCEPTION
    WHEN duplicate_object THEN NULL;
END $$;

-- Verify all enums were created
SELECT n.nspname as schema, t.typname as enum_name
FROM pg_type t
JOIN pg_namespace n ON t.typnamespace = n.oid
WHERE t.typtype = 'e'
AND n.nspname NOT IN ('pg_catalog', 'public')
ORDER BY n.nspname, t.typname;
