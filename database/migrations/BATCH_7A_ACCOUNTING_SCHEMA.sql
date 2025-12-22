-- =============================================================================
-- BATCH 7A: Accounting Integration Schema
-- =============================================================================
-- Purpose: Create accounting schema for Akaunting integration
-- Run on: Both staging and production AFTER Akaunting is running
-- Dependencies: None (creates new schema)
--
-- Tables Created:
--   - accounting.company_mappings     (station → Akaunting company)
--   - accounting.customer_mappings    (customer → Akaunting contact)
--   - accounting.chef_vendor_mappings (chef → Akaunting vendor)
--   - accounting.invoice_mappings     (booking → Akaunting invoice)
--   - accounting.payment_mappings     (payment → Akaunting transaction)
--   - accounting.chef_payment_mappings (chef payroll tracking)
--   - accounting.sync_history         (sync audit log)
-- =============================================================================

-- Create schema
CREATE SCHEMA IF NOT EXISTS accounting;

-- Grant permissions
GRANT USAGE ON SCHEMA accounting TO myhibachi_user;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA accounting TO myhibachi_user;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA accounting TO myhibachi_user;
ALTER DEFAULT PRIVILEGES IN SCHEMA accounting GRANT ALL ON TABLES TO myhibachi_user;
ALTER DEFAULT PRIVILEGES IN SCHEMA accounting GRANT ALL ON SEQUENCES TO myhibachi_user;

-- =============================================================================
-- Company Mappings (Station → Akaunting Company)
-- =============================================================================
CREATE TABLE IF NOT EXISTS accounting.company_mappings (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    station_id UUID NOT NULL REFERENCES identity.stations(id) ON DELETE CASCADE,
    akaunting_company_id INTEGER NOT NULL,
    akaunting_company_name VARCHAR(255) NOT NULL,
    tax_rate DECIMAL(5,2) DEFAULT 0.00,
    tax_name VARCHAR(100) DEFAULT 'Sales Tax',
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),

    UNIQUE(station_id),
    UNIQUE(akaunting_company_id)
);

COMMENT ON TABLE accounting.company_mappings IS 'Maps MyHibachi stations to Akaunting companies for multi-location accounting';

-- =============================================================================
-- Customer Mappings (Customer → Akaunting Contact)
-- =============================================================================
CREATE TABLE IF NOT EXISTS accounting.customer_mappings (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    customer_id UUID NOT NULL REFERENCES identity.users(id) ON DELETE CASCADE,
    akaunting_company_id INTEGER NOT NULL,
    akaunting_contact_id INTEGER NOT NULL,
    sync_status VARCHAR(20) DEFAULT 'synced' CHECK (
        sync_status IN ('pending', 'synced', 'failed', 'outdated')
    ),
    last_synced_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),

    UNIQUE(customer_id, akaunting_company_id)
);

CREATE INDEX IF NOT EXISTS idx_customer_mappings_akaunting
ON accounting.customer_mappings(akaunting_company_id, akaunting_contact_id);

COMMENT ON TABLE accounting.customer_mappings IS 'Maps MyHibachi customers to Akaunting contacts for invoicing';

-- =============================================================================
-- Chef Vendor Mappings (Chef → Akaunting Vendor)
-- =============================================================================
CREATE TABLE IF NOT EXISTS accounting.chef_vendor_mappings (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    chef_id UUID NOT NULL REFERENCES ops.chefs(id) ON DELETE CASCADE,
    akaunting_company_id INTEGER NOT NULL,  -- Usually the parent company
    akaunting_vendor_id INTEGER NOT NULL,
    tax_id_encrypted BYTEA,  -- Encrypted SSN/EIN for 1099
    payment_method VARCHAR(20) DEFAULT 'cash' CHECK (
        payment_method IN ('cash', 'zelle', 'check', 'direct_deposit')
    ),
    zelle_email VARCHAR(255),
    zelle_phone VARCHAR(20),
    sync_status VARCHAR(20) DEFAULT 'synced' CHECK (
        sync_status IN ('pending', 'synced', 'failed', 'outdated')
    ),
    last_synced_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),

    UNIQUE(chef_id, akaunting_company_id)
);

COMMENT ON TABLE accounting.chef_vendor_mappings IS 'Maps chefs to Akaunting vendors for payroll/1099 tracking';

-- =============================================================================
-- Invoice Mappings (Booking → Akaunting Invoice)
-- =============================================================================
CREATE TABLE IF NOT EXISTS accounting.invoice_mappings (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    booking_id UUID NOT NULL REFERENCES core.bookings(id) ON DELETE CASCADE,
    akaunting_company_id INTEGER NOT NULL,
    akaunting_invoice_id INTEGER NOT NULL,
    akaunting_invoice_number VARCHAR(50),
    invoice_status VARCHAR(20) DEFAULT 'draft' CHECK (
        invoice_status IN ('draft', 'sent', 'viewed', 'partial', 'paid', 'cancelled', 'overdue')
    ),
    invoice_amount DECIMAL(10,2),
    amount_paid DECIMAL(10,2) DEFAULT 0.00,
    pdf_url TEXT,
    sent_at TIMESTAMPTZ,
    paid_at TIMESTAMPTZ,
    sync_status VARCHAR(20) DEFAULT 'synced' CHECK (
        sync_status IN ('pending', 'synced', 'failed', 'outdated')
    ),
    last_synced_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),

    UNIQUE(booking_id),
    UNIQUE(akaunting_company_id, akaunting_invoice_id)
);

CREATE INDEX IF NOT EXISTS idx_invoice_mappings_status
ON accounting.invoice_mappings(invoice_status) WHERE invoice_status NOT IN ('paid', 'cancelled');

COMMENT ON TABLE accounting.invoice_mappings IS 'Maps bookings to Akaunting invoices for revenue tracking';

-- =============================================================================
-- Payment Mappings (Payment → Akaunting Transaction)
-- =============================================================================
CREATE TABLE IF NOT EXISTS accounting.payment_mappings (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    payment_id UUID NOT NULL REFERENCES core.payments(id) ON DELETE CASCADE,
    invoice_mapping_id UUID REFERENCES accounting.invoice_mappings(id),
    akaunting_company_id INTEGER NOT NULL,
    akaunting_transaction_id INTEGER NOT NULL,
    akaunting_account_id INTEGER,  -- Bank/Stripe account in Akaunting
    transaction_type VARCHAR(20) DEFAULT 'income' CHECK (
        transaction_type IN ('income', 'expense', 'transfer')
    ),
    sync_status VARCHAR(20) DEFAULT 'synced' CHECK (
        sync_status IN ('pending', 'synced', 'failed', 'outdated')
    ),
    last_synced_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),

    UNIQUE(payment_id),
    UNIQUE(akaunting_company_id, akaunting_transaction_id)
);

COMMENT ON TABLE accounting.payment_mappings IS 'Maps Stripe payments to Akaunting transactions';

-- =============================================================================
-- Chef Payment Mappings (Chef Payroll Tracking)
-- =============================================================================
-- This is the CUSTOM payroll table since we pay cash/Zelle
CREATE TABLE IF NOT EXISTS accounting.chef_payment_mappings (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    chef_vendor_mapping_id UUID NOT NULL REFERENCES accounting.chef_vendor_mappings(id),
    booking_id UUID REFERENCES core.bookings(id),  -- Which booking this was for
    akaunting_company_id INTEGER NOT NULL,
    akaunting_bill_id INTEGER,  -- Bill in Akaunting (optional)
    akaunting_payment_id INTEGER,  -- Payment record in Akaunting

    -- Payment Details
    payment_date DATE NOT NULL,
    amount DECIMAL(10,2) NOT NULL,
    payment_method VARCHAR(20) NOT NULL CHECK (
        payment_method IN ('cash', 'zelle', 'check', 'direct_deposit')
    ),

    -- For Zelle payments
    zelle_confirmation_number VARCHAR(100),

    -- For cash payments
    cash_receipt_signed BOOLEAN DEFAULT FALSE,

    -- 1099 Tracking
    year_to_date_total DECIMAL(12,2),  -- Calculated field, updated by trigger
    is_1099_eligible BOOLEAN DEFAULT TRUE,

    -- Status
    status VARCHAR(20) DEFAULT 'paid' CHECK (
        status IN ('pending', 'paid', 'cancelled', 'refunded')
    ),
    notes TEXT,

    -- Audit
    paid_by UUID REFERENCES identity.users(id),
    sync_status VARCHAR(20) DEFAULT 'pending' CHECK (
        sync_status IN ('pending', 'synced', 'failed')
    ),
    synced_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_chef_payments_chef_date
ON accounting.chef_payment_mappings(chef_vendor_mapping_id, payment_date);

CREATE INDEX IF NOT EXISTS idx_chef_payments_year
ON accounting.chef_payment_mappings(EXTRACT(YEAR FROM payment_date), chef_vendor_mapping_id);

COMMENT ON TABLE accounting.chef_payment_mappings IS 'Tracks chef payments (Cash/Zelle) for payroll and 1099 reporting';

-- =============================================================================
-- Sync History (Audit Log)
-- =============================================================================
CREATE TABLE IF NOT EXISTS accounting.sync_history (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    entity_type VARCHAR(50) NOT NULL,  -- 'customer', 'invoice', 'payment', 'chef_payment'
    entity_id UUID NOT NULL,
    akaunting_entity_type VARCHAR(50),  -- 'contact', 'invoice', 'transaction', 'bill'
    akaunting_entity_id INTEGER,
    operation VARCHAR(20) NOT NULL CHECK (
        operation IN ('create', 'update', 'delete', 'sync')
    ),
    status VARCHAR(20) NOT NULL CHECK (
        status IN ('success', 'failed', 'partial')
    ),
    request_payload JSONB,
    response_payload JSONB,
    error_message TEXT,
    duration_ms INTEGER,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_sync_history_entity
ON accounting.sync_history(entity_type, entity_id, created_at DESC);

CREATE INDEX IF NOT EXISTS idx_sync_history_failed
ON accounting.sync_history(status, created_at DESC) WHERE status = 'failed';

COMMENT ON TABLE accounting.sync_history IS 'Audit log for all Akaunting sync operations';

-- =============================================================================
-- Helper Function: Calculate Chef YTD Payments
-- =============================================================================
CREATE OR REPLACE FUNCTION accounting.calculate_chef_ytd(
    p_chef_vendor_mapping_id UUID,
    p_year INTEGER DEFAULT EXTRACT(YEAR FROM CURRENT_DATE)
) RETURNS DECIMAL(12,2) AS $$
    SELECT COALESCE(SUM(amount), 0)
    FROM accounting.chef_payment_mappings
    WHERE chef_vendor_mapping_id = p_chef_vendor_mapping_id
      AND EXTRACT(YEAR FROM payment_date) = p_year
      AND status = 'paid';
$$ LANGUAGE SQL STABLE;

COMMENT ON FUNCTION accounting.calculate_chef_ytd IS 'Calculate year-to-date payments to a chef for 1099 reporting';

-- =============================================================================
-- Trigger: Update YTD on Chef Payment
-- =============================================================================
CREATE OR REPLACE FUNCTION accounting.update_chef_ytd()
RETURNS TRIGGER AS $$
BEGIN
    NEW.year_to_date_total := accounting.calculate_chef_ytd(
        NEW.chef_vendor_mapping_id,
        EXTRACT(YEAR FROM NEW.payment_date)::INTEGER
    );
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trg_update_chef_ytd ON accounting.chef_payment_mappings;
CREATE TRIGGER trg_update_chef_ytd
    BEFORE INSERT OR UPDATE ON accounting.chef_payment_mappings
    FOR EACH ROW
    EXECUTE FUNCTION accounting.update_chef_ytd();

-- =============================================================================
-- View: Chef 1099 Summary
-- =============================================================================
CREATE OR REPLACE VIEW accounting.chef_1099_summary AS
SELECT
    cvm.chef_id,
    c.full_name AS chef_name,
    EXTRACT(YEAR FROM cpm.payment_date)::INTEGER AS tax_year,
    SUM(cpm.amount) AS total_payments,
    COUNT(*) AS payment_count,
    cvm.payment_method AS primary_payment_method,
    CASE
        WHEN SUM(cpm.amount) >= 600 THEN TRUE
        ELSE FALSE
    END AS requires_1099,
    cvm.tax_id_encrypted IS NOT NULL AS has_tax_id_on_file
FROM accounting.chef_payment_mappings cpm
JOIN accounting.chef_vendor_mappings cvm ON cvm.id = cpm.chef_vendor_mapping_id
JOIN ops.chefs c ON c.id = cvm.chef_id
WHERE cpm.status = 'paid'
GROUP BY
    cvm.chef_id,
    c.full_name,
    EXTRACT(YEAR FROM cpm.payment_date),
    cvm.payment_method,
    cvm.tax_id_encrypted IS NOT NULL;

COMMENT ON VIEW accounting.chef_1099_summary IS 'Summary of chef payments for 1099 reporting - shows who needs 1099 (>=$600)';

-- =============================================================================
-- View: Sync Status Dashboard
-- =============================================================================
CREATE OR REPLACE VIEW accounting.sync_status_dashboard AS
SELECT
    'Customers' AS entity_type,
    COUNT(*) FILTER (WHERE sync_status = 'synced') AS synced,
    COUNT(*) FILTER (WHERE sync_status = 'pending') AS pending,
    COUNT(*) FILTER (WHERE sync_status = 'failed') AS failed,
    COUNT(*) AS total
FROM accounting.customer_mappings
UNION ALL
SELECT
    'Invoices',
    COUNT(*) FILTER (WHERE sync_status = 'synced'),
    COUNT(*) FILTER (WHERE sync_status = 'pending'),
    COUNT(*) FILTER (WHERE sync_status = 'failed'),
    COUNT(*)
FROM accounting.invoice_mappings
UNION ALL
SELECT
    'Payments',
    COUNT(*) FILTER (WHERE sync_status = 'synced'),
    COUNT(*) FILTER (WHERE sync_status = 'pending'),
    COUNT(*) FILTER (WHERE sync_status = 'failed'),
    COUNT(*)
FROM accounting.payment_mappings
UNION ALL
SELECT
    'Chef Payments',
    COUNT(*) FILTER (WHERE sync_status = 'synced'),
    COUNT(*) FILTER (WHERE sync_status = 'pending'),
    COUNT(*) FILTER (WHERE sync_status = 'failed'),
    COUNT(*)
FROM accounting.chef_payment_mappings;

COMMENT ON VIEW accounting.sync_status_dashboard IS 'Dashboard view showing sync status across all accounting entities';

-- =============================================================================
-- Done
-- =============================================================================
-- To verify:
--   \dt accounting.*
--   \df accounting.*
--   SELECT * FROM accounting.sync_status_dashboard;
