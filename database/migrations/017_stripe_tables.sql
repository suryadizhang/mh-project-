-- =====================================================
-- Migration: 017_stripe_tables.sql
-- Purpose: Create Stripe payment integration tables
-- Created: 2025-01-30
-- =====================================================
-- Tables:
--   - core.stripe_customers: Links internal customers to Stripe
--   - core.stripe_payments: Payment transaction records
--   - core.invoices: Invoice records
--   - core.refunds: Refund records
--   - core.webhook_events: Stripe webhook event log
--
-- ENUM Types:
--   - core.payment_status
--   - core.invoice_status
--   - core.refund_status
--   - core.webhook_event_status
-- =====================================================

BEGIN;

-- ==================== ENUM TYPES ====================

-- Payment status enum
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'payment_status' AND typnamespace = (SELECT oid FROM pg_namespace WHERE nspname = 'core')) THEN
        CREATE TYPE core.payment_status AS ENUM (
            'pending',
            'processing',
            'succeeded',
            'failed',
            'cancelled',
            'refunded',
            'partially_refunded'
        );
        RAISE NOTICE 'Created ENUM type: core.payment_status';
    ELSE
        RAISE NOTICE 'ENUM type core.payment_status already exists';
    END IF;
END $$;

-- Invoice status enum
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'invoice_status' AND typnamespace = (SELECT oid FROM pg_namespace WHERE nspname = 'core')) THEN
        CREATE TYPE core.invoice_status AS ENUM (
            'draft',
            'open',
            'paid',
            'uncollectible',
            'void'
        );
        RAISE NOTICE 'Created ENUM type: core.invoice_status';
    ELSE
        RAISE NOTICE 'ENUM type core.invoice_status already exists';
    END IF;
END $$;

-- Refund status enum
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'refund_status' AND typnamespace = (SELECT oid FROM pg_namespace WHERE nspname = 'core')) THEN
        CREATE TYPE core.refund_status AS ENUM (
            'pending',
            'succeeded',
            'failed',
            'cancelled'
        );
        RAISE NOTICE 'Created ENUM type: core.refund_status';
    ELSE
        RAISE NOTICE 'ENUM type core.refund_status already exists';
    END IF;
END $$;

-- Webhook event status enum
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'webhook_event_status' AND typnamespace = (SELECT oid FROM pg_namespace WHERE nspname = 'core')) THEN
        CREATE TYPE core.webhook_event_status AS ENUM (
            'received',
            'processing',
            'processed',
            'failed',
            'ignored'
        );
        RAISE NOTICE 'Created ENUM type: core.webhook_event_status';
    ELSE
        RAISE NOTICE 'ENUM type core.webhook_event_status already exists';
    END IF;
END $$;


-- ==================== TABLES ====================

-- 1. stripe_customers: Links internal customers to Stripe customer IDs
CREATE TABLE IF NOT EXISTS core.stripe_customers (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    customer_id UUID NOT NULL REFERENCES core.customers(id) ON DELETE CASCADE,
    stripe_customer_id VARCHAR(255) NOT NULL UNIQUE,
    email VARCHAR(255),
    name VARCHAR(255),
    default_payment_method VARCHAR(255),
    stripe_metadata JSONB,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ
);

-- Indexes for stripe_customers
CREATE INDEX IF NOT EXISTS ix_stripe_customers_customer_id ON core.stripe_customers(customer_id);
CREATE INDEX IF NOT EXISTS ix_stripe_customers_stripe_id ON core.stripe_customers(stripe_customer_id);

COMMENT ON TABLE core.stripe_customers IS 'Maps internal customers to Stripe customer IDs for payment processing';
COMMENT ON COLUMN core.stripe_customers.stripe_customer_id IS 'Stripe customer ID (cus_xxx)';
COMMENT ON COLUMN core.stripe_customers.default_payment_method IS 'Default payment method ID (pm_xxx)';


-- 2. stripe_payments: Payment transaction records
CREATE TABLE IF NOT EXISTS core.stripe_payments (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    stripe_customer_id UUID REFERENCES core.stripe_customers(id) ON DELETE SET NULL,
    booking_id UUID REFERENCES core.bookings(id) ON DELETE SET NULL,
    payment_intent_id VARCHAR(255) NOT NULL UNIQUE,
    amount NUMERIC(10, 2) NOT NULL,
    currency VARCHAR(3) NOT NULL DEFAULT 'usd',
    status core.payment_status NOT NULL DEFAULT 'pending',
    description TEXT,
    stripe_metadata JSONB,
    charge_id VARCHAR(255),
    receipt_url VARCHAR(500),
    failure_code VARCHAR(100),
    failure_message TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ
);

-- Indexes for stripe_payments
CREATE INDEX IF NOT EXISTS ix_stripe_payments_customer ON core.stripe_payments(stripe_customer_id);
CREATE INDEX IF NOT EXISTS ix_stripe_payments_booking ON core.stripe_payments(booking_id);
CREATE INDEX IF NOT EXISTS ix_stripe_payments_intent ON core.stripe_payments(payment_intent_id);
CREATE INDEX IF NOT EXISTS ix_stripe_payments_status ON core.stripe_payments(status);

COMMENT ON TABLE core.stripe_payments IS 'Records individual payment transactions and their statuses';
COMMENT ON COLUMN core.stripe_payments.payment_intent_id IS 'Stripe PaymentIntent ID (pi_xxx)';
COMMENT ON COLUMN core.stripe_payments.charge_id IS 'Stripe Charge ID (ch_xxx)';


-- 3. invoices: Invoice records (synced with Stripe)
CREATE TABLE IF NOT EXISTS core.invoices (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    stripe_customer_id UUID REFERENCES core.stripe_customers(id) ON DELETE SET NULL,
    booking_id UUID REFERENCES core.bookings(id) ON DELETE SET NULL,
    stripe_invoice_id VARCHAR(255) UNIQUE,
    invoice_number VARCHAR(50) NOT NULL UNIQUE,
    amount_due NUMERIC(10, 2) NOT NULL,
    amount_paid NUMERIC(10, 2) NOT NULL DEFAULT 0.00,
    currency VARCHAR(3) NOT NULL DEFAULT 'usd',
    status core.invoice_status NOT NULL DEFAULT 'draft',
    description TEXT,
    line_items JSONB,
    due_date TIMESTAMPTZ,
    paid_at TIMESTAMPTZ,
    hosted_invoice_url VARCHAR(500),
    pdf_url VARCHAR(500),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ
);

-- Indexes for invoices
CREATE INDEX IF NOT EXISTS ix_invoices_customer ON core.invoices(stripe_customer_id);
CREATE INDEX IF NOT EXISTS ix_invoices_booking ON core.invoices(booking_id);
CREATE INDEX IF NOT EXISTS ix_invoices_stripe ON core.invoices(stripe_invoice_id);
CREATE INDEX IF NOT EXISTS ix_invoices_status ON core.invoices(status);

COMMENT ON TABLE core.invoices IS 'Invoice records synced with Stripe invoices';
COMMENT ON COLUMN core.invoices.stripe_invoice_id IS 'Stripe Invoice ID (in_xxx)';
COMMENT ON COLUMN core.invoices.invoice_number IS 'Human-readable invoice number';


-- 4. refunds: Refund records
CREATE TABLE IF NOT EXISTS core.refunds (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    payment_id UUID NOT NULL REFERENCES core.stripe_payments(id) ON DELETE CASCADE,
    stripe_refund_id VARCHAR(255) UNIQUE,
    amount NUMERIC(10, 2) NOT NULL,
    currency VARCHAR(3) NOT NULL DEFAULT 'usd',
    status core.refund_status NOT NULL DEFAULT 'pending',
    reason VARCHAR(255),
    description TEXT,
    stripe_metadata JSONB,
    failure_reason TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ,
    refunded_by UUID REFERENCES identity.users(id) ON DELETE SET NULL
);

-- Indexes for refunds
CREATE INDEX IF NOT EXISTS ix_refunds_payment ON core.refunds(payment_id);
CREATE INDEX IF NOT EXISTS ix_refunds_stripe ON core.refunds(stripe_refund_id);
CREATE INDEX IF NOT EXISTS ix_refunds_status ON core.refunds(status);

COMMENT ON TABLE core.refunds IS 'Refund records for payment transactions';
COMMENT ON COLUMN core.refunds.stripe_refund_id IS 'Stripe Refund ID (re_xxx)';
COMMENT ON COLUMN core.refunds.refunded_by IS 'Admin user who initiated the refund';


-- 5. webhook_events: Stripe webhook event log
CREATE TABLE IF NOT EXISTS core.webhook_events (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    stripe_event_id VARCHAR(255) NOT NULL UNIQUE,
    event_type VARCHAR(100) NOT NULL,
    status core.webhook_event_status NOT NULL DEFAULT 'received',
    payload JSONB NOT NULL,
    processing_error TEXT,
    processed_at TIMESTAMPTZ,
    retry_count INTEGER NOT NULL DEFAULT 0,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Indexes for webhook_events
CREATE INDEX IF NOT EXISTS ix_webhook_events_stripe_id ON core.webhook_events(stripe_event_id);
CREATE INDEX IF NOT EXISTS ix_webhook_events_type ON core.webhook_events(event_type);
CREATE INDEX IF NOT EXISTS ix_webhook_events_status ON core.webhook_events(status);
CREATE INDEX IF NOT EXISTS ix_webhook_events_created ON core.webhook_events(created_at);

COMMENT ON TABLE core.webhook_events IS 'Log of Stripe webhook events for auditing and replay';
COMMENT ON COLUMN core.webhook_events.stripe_event_id IS 'Stripe Event ID (evt_xxx)';
COMMENT ON COLUMN core.webhook_events.retry_count IS 'Number of processing retry attempts';


COMMIT;

-- =====================================================
-- ROLLBACK SCRIPT (for emergency use)
-- =====================================================
-- DROP TABLE IF EXISTS core.webhook_events CASCADE;
-- DROP TABLE IF EXISTS core.refunds CASCADE;
-- DROP TABLE IF EXISTS core.invoices CASCADE;
-- DROP TABLE IF EXISTS core.stripe_payments CASCADE;
-- DROP TABLE IF EXISTS core.stripe_customers CASCADE;
-- DROP TYPE IF EXISTS core.webhook_event_status;
-- DROP TYPE IF EXISTS core.refund_status;
-- DROP TYPE IF EXISTS core.invoice_status;
-- DROP TYPE IF EXISTS core.payment_status;
