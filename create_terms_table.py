import os

from sqlalchemy import create_engine, text

# Get database URL from environment
db_url = os.getenv("DATABASE_URL_SYNC") or os.getenv(
    "DATABASE_URL", ""
).replace("postgresql+asyncpg://", "postgresql+psycopg2://")
if not db_url:
    print("DATABASE_URL not set")
    exit(1)

engine = create_engine(db_url)

# Create terms_acknowledgments table
create_table_sql = """
CREATE TABLE IF NOT EXISTS public.terms_acknowledgments (
    id SERIAL PRIMARY KEY,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    
    -- Who agreed (VARCHAR to match public.customers and public.bookings)
    customer_id VARCHAR NOT NULL,
    booking_id INTEGER NULL,
    
    -- What they agreed to
    terms_version VARCHAR(20) NOT NULL DEFAULT '1.0',
    terms_url VARCHAR(500) NOT NULL,
    terms_text_hash VARCHAR(64) NULL,
    
    -- When they agreed
    acknowledged_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    
    -- How they agreed
    channel VARCHAR(20) NOT NULL,
    acknowledgment_method VARCHAR(50) NOT NULL,
    acknowledgment_text TEXT NULL,
    
    -- Legal proof for SMS/RingCentral
    sms_message_id VARCHAR(100) NULL,
    sms_message_timestamp TIMESTAMPTZ NULL,
    sms_message_hash VARCHAR(64) NULL,
    webhook_source_ip INET NULL,
    
    -- Where they agreed from
    ip_address INET NULL,
    user_agent TEXT NULL,
    
    -- Staff context (for phone/in-person)
    staff_member_name VARCHAR(255) NULL,
    staff_member_email VARCHAR(255) NULL,
    notes TEXT NULL,
    
    -- Verification
    verified BOOLEAN NOT NULL DEFAULT TRUE,
    verification_notes TEXT NULL,
    
    -- Foreign keys
    CONSTRAINT terms_acknowledgments_customer_id_fkey 
        FOREIGN KEY (customer_id) REFERENCES public.customers(id) ON DELETE CASCADE,
    CONSTRAINT terms_acknowledgments_booking_id_fkey 
        FOREIGN KEY (booking_id) REFERENCES public.bookings(id) ON DELETE SET NULL
);

-- Create indexes
CREATE INDEX IF NOT EXISTS ix_terms_acknowledgments_customer_id ON public.terms_acknowledgments(customer_id);
CREATE INDEX IF NOT EXISTS ix_terms_acknowledgments_booking_id ON public.terms_acknowledgments(booking_id);
CREATE INDEX IF NOT EXISTS ix_terms_acknowledgments_acknowledged_at ON public.terms_acknowledgments(acknowledged_at);
CREATE INDEX IF NOT EXISTS ix_terms_acknowledgments_channel ON public.terms_acknowledgments(channel);
CREATE INDEX IF NOT EXISTS ix_terms_acknowledgments_customer_latest ON public.terms_acknowledgments(customer_id, acknowledged_at DESC);

-- Update alembic_version to mark migration as done
INSERT INTO alembic_version (version_num) VALUES ('015_add_terms_acknowledgment')
ON CONFLICT (version_num) DO NOTHING;
"""

with engine.connect() as conn:
    with conn.begin():
        conn.execute(text(create_table_sql))
        print("✅ Table created successfully!")

        # Verify table exists
        result = conn.execute(
            text(
                """
            SELECT COUNT(*) FROM information_schema.tables 
            WHERE table_schema = 'public' 
            AND table_name = 'terms_acknowledgments'
        """
            )
        )
        count = result.scalar()
        if count > 0:
            print("✅ Verified: terms_acknowledgments table exists")
        else:
            print("❌ Error: Table was not created")
