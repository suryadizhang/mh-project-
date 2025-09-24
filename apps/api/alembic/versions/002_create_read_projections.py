"""Create read model projections

Revision ID: 002
Revises: 001
Create Date: 2025-09-23 12:05:00.000000

"""

from alembic import op

# revision identifiers, used by Alembic.
revision = '002'
down_revision = '001'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create read model projections for fast queries."""

    # Inbox threads projection
    op.execute("""
        CREATE MATERIALIZED VIEW read.inbox_threads AS
        SELECT
            t.id as thread_id,
            t.customer_id,
            CONCAT(c.first_name, ' ', c.last_name) as customer_name,
            c.phone_encrypted as customer_phone,
            c.email_encrypted as customer_email,
            t.channel,
            t.status,
            t.assigned_agent_id,
            t.ai_mode,
            t.last_message_at,
            COUNT(m.id) as message_count,
            MAX(CASE WHEN m.direction = 'inbound' THEN m.created_at END) as last_inbound_at,
            MAX(CASE WHEN m.direction = 'outbound' THEN m.created_at END) as last_outbound_at,
            (
                SELECT m2.content
                FROM core.messages m2
                WHERE m2.thread_id = t.id
                ORDER BY m2.created_at DESC
                LIMIT 1
            ) as last_message_content,
            (
                SELECT m2.sender_type
                FROM core.messages m2
                WHERE m2.thread_id = t.id
                ORDER BY m2.created_at DESC
                LIMIT 1
            ) as last_message_sender,
            -- Customer lead score and booking info
            (
                SELECT COUNT(*)
                FROM core.bookings b
                WHERE b.customer_id = c.id AND b.deleted_at IS NULL
            ) as total_bookings,
            (
                SELECT MAX(b.created_at)
                FROM core.bookings b
                WHERE b.customer_id = c.id AND b.deleted_at IS NULL
            ) as last_booking_at,
            t.created_at,
            t.updated_at
        FROM core.message_threads t
        JOIN core.customers c ON c.id = t.customer_id
        LEFT JOIN core.messages m ON m.thread_id = t.id
        WHERE t.deleted_at IS NULL AND c.deleted_at IS NULL
        GROUP BY t.id, t.customer_id, c.first_name, c.last_name, c.phone_encrypted, c.email_encrypted,
                 t.channel, t.status, t.assigned_agent_id, t.ai_mode, t.last_message_at, t.created_at, t.updated_at, c.id
    """)

    # Create indexes on materialized view
    op.create_index('ix_read_inbox_threads_status_updated', 'inbox_threads', ['status', 'last_message_at'], schema='read')
    op.create_index('ix_read_inbox_threads_assigned', 'inbox_threads', ['assigned_agent_id'], schema='read')
    op.create_index('ix_read_inbox_threads_customer', 'inbox_threads', ['customer_id'], schema='read')

    # Payments feed projection
    op.execute("""
        CREATE MATERIALIZED VIEW read.payments_feed AS
        SELECT
            pe.id as payment_event_id,
            pe.provider,
            pe.provider_id,
            pe.method,
            pe.amount_cents,
            pe.currency,
            pe.occurred_at,
            pe.memo,
            pm.booking_id,
            pm.confidence,
            pm.match_method,
            pm.status as match_status,
            -- Booking details if matched
            b.id as booking_reference,
            CONCAT(c.first_name, ' ', c.last_name) as customer_name,
            b.date as booking_date,
            b.slot as booking_slot,
            b.status as booking_status,
            b.deposit_due_cents,
            b.total_due_cents,
            -- Payment status derived
            CASE
                WHEN pm.booking_id IS NOT NULL AND pm.status = 'auto' THEN 'matched'
                WHEN pm.booking_id IS NOT NULL AND pm.status = 'manual' THEN 'manual_match'
                WHEN pm.booking_id IS NULL THEN 'unmatched'
                ELSE 'ignored'
            END as payment_status,
            pe.created_at
        FROM integra.payment_events pe
        LEFT JOIN integra.payment_matches pm ON pm.payment_event_id = pe.id AND pm.status != 'ignored'
        LEFT JOIN core.bookings b ON b.id = pm.booking_id
        LEFT JOIN core.customers c ON c.id = b.customer_id
        ORDER BY pe.occurred_at DESC
    """)

    op.create_index('ix_read_payments_feed_status_occurred', 'payments_feed', ['payment_status', 'occurred_at'], schema='read')
    op.create_index('ix_read_payments_feed_booking', 'payments_feed', ['booking_id'], schema='read')
    op.create_index('ix_read_payments_feed_provider', 'payments_feed', ['provider', 'method'], schema='read')

    # Schedule board projection
    op.execute("""
        CREATE MATERIALIZED VIEW read.schedule_board AS
        SELECT
            -- Date and slot info
            b.date,
            b.slot,
            b.zone,
            -- Chef info
            ch.id as chef_id,
            ch.name as chef_name,
            ch.zones as chef_zones,
            -- Booking info
            b.id as booking_id,
            CONCAT(c.first_name, ' ', c.last_name) as customer_name,
            c.phone_encrypted as customer_phone,
            b.status as booking_status,
            b.party_adults + b.party_kids as total_guests,
            b.party_adults,
            b.party_kids,
            b.total_due_cents,
            b.deposit_due_cents,
            -- Address (for travel planning)
            b.address_encrypted,
            b.special_requests,
            b.notes,
            -- Timing
            b.created_at as booking_created_at,
            b.updated_at as booking_updated_at,
            -- Conflicts and availability
            CASE
                WHEN b.status IN ('confirmed', 'completed') THEN 'booked'
                WHEN b.status IN ('new', 'deposit_pending') THEN 'tentative'
                WHEN b.status = 'cancelled' THEN 'cancelled'
                ELSE 'unknown'
            END as slot_status
        FROM core.bookings b
        JOIN core.customers c ON c.id = b.customer_id
        LEFT JOIN core.chefs ch ON ch.id = b.chef_id
        WHERE b.deleted_at IS NULL AND c.deleted_at IS NULL

        UNION ALL

        -- Include available slots (empty slots for active chefs)
        SELECT
            generate_series::date as date,
            slot_time::time as slot,
            chef.zones[1] as zone,  -- Primary zone
            chef.id as chef_id,
            chef.name as chef_name,
            chef.zones as chef_zones,
            NULL as booking_id,
            NULL as customer_name,
            NULL as customer_phone,
            NULL as booking_status,
            NULL as total_guests,
            NULL as party_adults,
            NULL as party_kids,
            NULL as total_due_cents,
            NULL as deposit_due_cents,
            NULL as address_encrypted,
            NULL as special_requests,
            NULL as notes,
            NULL as booking_created_at,
            NULL as booking_updated_at,
            'available' as slot_status
        FROM generate_series(
            CURRENT_DATE,
            CURRENT_DATE + interval '60 days',
            '1 day'::interval
        ) generate_series
        CROSS JOIN (VALUES ('12:00'::time), ('15:00'::time), ('18:00'::time), ('21:00'::time)) AS slots(slot_time)
        CROSS JOIN (SELECT id, name, zones FROM core.chefs WHERE is_active = true AND deleted_at IS NULL) chef
        WHERE generate_series::date + slot_time > NOW()  -- Only future slots
        AND NOT EXISTS (
            SELECT 1 FROM core.bookings b2
            WHERE b2.chef_id = chef.id
            AND b2.date = generate_series::date
            AND b2.slot = slot_time
            AND b2.status NOT IN ('cancelled', 'no_show')
            AND b2.deleted_at IS NULL
        )
    """)

    op.create_index('ix_read_schedule_board_date_slot', 'schedule_board', ['date', 'slot'], schema='read')
    op.create_index('ix_read_schedule_board_chef_date', 'schedule_board', ['chef_id', 'date'], schema='read')
    op.create_index('ix_read_schedule_board_status', 'schedule_board', ['slot_status'], schema='read')

    # Customer 360 projection
    op.execute("""
        CREATE MATERIALIZED VIEW read.customer_360 AS
        SELECT
            c.id as customer_id,
            c.first_name,
            c.last_name,
            CONCAT(c.first_name, ' ', c.last_name) as full_name,
            c.email_encrypted,
            c.phone_encrypted,
            c.consent_sms,
            c.consent_email,
            c.timezone,
            c.tags,
            c.notes as customer_notes,
            c.created_at as customer_since,
            c.updated_at as last_updated,

            -- Booking statistics
            COUNT(DISTINCT b.id) FILTER (WHERE b.deleted_at IS NULL) as total_bookings,
            COUNT(DISTINCT b.id) FILTER (WHERE b.status = 'completed') as completed_bookings,
            COUNT(DISTINCT b.id) FILTER (WHERE b.status = 'cancelled') as cancelled_bookings,
            COALESCE(SUM(b.total_due_cents) FILTER (WHERE b.status = 'completed'), 0) as lifetime_value_cents,
            MAX(b.date) FILTER (WHERE b.status = 'completed') as last_booking_date,
            MIN(b.date) FILTER (WHERE b.status = 'completed') as first_booking_date,

            -- Payment information
            COUNT(DISTINCT pm.id) as total_payments,
            COALESCE(SUM(pe.amount_cents), 0) as total_paid_cents,

            -- Communication statistics
            COUNT(DISTINCT t.id) as total_threads,
            COUNT(DISTINCT m.id) as total_messages,
            MAX(t.last_message_at) as last_contact_at,

            -- Derived insights
            CASE
                WHEN COUNT(DISTINCT b.id) FILTER (WHERE b.deleted_at IS NULL) = 0 THEN 'lead'
                WHEN COUNT(DISTINCT b.id) FILTER (WHERE b.status = 'completed') = 0 THEN 'prospect'
                WHEN COUNT(DISTINCT b.id) FILTER (WHERE b.status = 'completed') = 1 THEN 'new_customer'
                WHEN COUNT(DISTINCT b.id) FILTER (WHERE b.status = 'completed') > 1 THEN 'repeat_customer'
                ELSE 'unknown'
            END as customer_segment,

            CASE
                WHEN MAX(t.last_message_at) > NOW() - interval '7 days' THEN 'hot'
                WHEN MAX(t.last_message_at) > NOW() - interval '30 days' THEN 'warm'
                WHEN MAX(t.last_message_at) > NOW() - interval '90 days' THEN 'cool'
                ELSE 'cold'
            END as engagement_level,

            -- Next best action suggestion
            CASE
                WHEN COUNT(DISTINCT b.id) FILTER (WHERE b.status IN ('new', 'deposit_pending')) > 0 THEN 'follow_up_booking'
                WHEN COUNT(DISTINCT b.id) FILTER (WHERE b.status = 'completed') > 0
                     AND MAX(b.date) FILTER (WHERE b.status = 'completed') < CURRENT_DATE - interval '90 days' THEN 'reactivation'
                WHEN COUNT(DISTINCT b.id) FILTER (WHERE b.status = 'completed') = 0 THEN 'conversion'
                ELSE 'nurture'
            END as suggested_action

        FROM core.customers c
        LEFT JOIN core.bookings b ON b.customer_id = c.id
        LEFT JOIN integra.payment_matches pm ON pm.booking_id = b.id
        LEFT JOIN integra.payment_events pe ON pe.id = pm.payment_event_id
        LEFT JOIN core.message_threads t ON t.customer_id = c.id
        LEFT JOIN core.messages m ON m.thread_id = t.id
        WHERE c.deleted_at IS NULL
        GROUP BY c.id, c.first_name, c.last_name, c.email_encrypted, c.phone_encrypted,
                 c.consent_sms, c.consent_email, c.timezone, c.tags, c.notes, c.created_at, c.updated_at
    """)

    op.create_index('ix_read_customer_360_segment', 'customer_360', ['customer_segment'], schema='read')
    op.create_index('ix_read_customer_360_engagement', 'customer_360', ['engagement_level'], schema='read')
    op.create_index('ix_read_customer_360_action', 'customer_360', ['suggested_action'], schema='read')
    op.create_index('ix_read_customer_360_value', 'customer_360', ['lifetime_value_cents'], schema='read')

    # Booking detail projection
    op.execute("""
        CREATE MATERIALIZED VIEW read.booking_detail AS
        SELECT
            b.id as booking_id,
            b.customer_id,
            CONCAT(c.first_name, ' ', c.last_name) as customer_name,
            c.email_encrypted as customer_email,
            c.phone_encrypted as customer_phone,
            b.date,
            b.slot,
            b.address_encrypted,
            b.zone,
            b.chef_id,
            ch.name as chef_name,
            ch.google_calendar_id,
            b.status,
            b.party_adults,
            b.party_kids,
            b.party_adults + b.party_kids as total_guests,
            b.deposit_due_cents,
            b.total_due_cents,
            b.menu_items,
            b.special_requests,
            b.notes,
            b.source,
            b.metadata,
            b.created_at,
            b.updated_at,

            -- Payment summary
            COALESCE(SUM(pe.amount_cents) FILTER (WHERE pm.status != 'ignored'), 0) as total_paid_cents,
            COUNT(pm.id) FILTER (WHERE pm.status != 'ignored') as payment_count,
            ARRAY_AGG(
                DISTINCT jsonb_build_object(
                    'provider', pe.provider,
                    'method', pe.method,
                    'amount_cents', pe.amount_cents,
                    'occurred_at', pe.occurred_at,
                    'memo', pe.memo
                )
            ) FILTER (WHERE pe.id IS NOT NULL AND pm.status != 'ignored') as payments,

            -- Message thread info
            COUNT(DISTINCT t.id) as thread_count,
            COUNT(DISTINCT m.id) as total_messages,
            MAX(t.last_message_at) as last_contact_at,

            -- Status calculations
            CASE
                WHEN b.deposit_due_cents <= COALESCE(SUM(pe.amount_cents) FILTER (WHERE pm.status != 'ignored'), 0)
                     AND b.total_due_cents > COALESCE(SUM(pe.amount_cents) FILTER (WHERE pm.status != 'ignored'), 0)
                THEN true
                ELSE false
            END as deposit_paid,

            CASE
                WHEN b.total_due_cents <= COALESCE(SUM(pe.amount_cents) FILTER (WHERE pm.status != 'ignored'), 0)
                THEN true
                ELSE false
            END as fully_paid,

            b.total_due_cents - COALESCE(SUM(pe.amount_cents) FILTER (WHERE pm.status != 'ignored'), 0) as balance_due_cents

        FROM core.bookings b
        JOIN core.customers c ON c.id = b.customer_id
        LEFT JOIN core.chefs ch ON ch.id = b.chef_id
        LEFT JOIN integra.payment_matches pm ON pm.booking_id = b.id
        LEFT JOIN integra.payment_events pe ON pe.id = pm.payment_event_id
        LEFT JOIN core.message_threads t ON t.customer_id = c.id
        LEFT JOIN core.messages m ON m.thread_id = t.id
        WHERE b.deleted_at IS NULL AND c.deleted_at IS NULL
        GROUP BY b.id, b.customer_id, c.first_name, c.last_name, c.email_encrypted, c.phone_encrypted,
                 b.date, b.slot, b.address_encrypted, b.zone, b.chef_id, ch.name, ch.google_calendar_id,
                 b.status, b.party_adults, b.party_kids, b.deposit_due_cents, b.total_due_cents,
                 b.menu_items, b.special_requests, b.notes, b.source, b.metadata, b.created_at, b.updated_at
    """)

    op.create_index('ix_read_booking_detail_customer', 'booking_detail', ['customer_id'], schema='read')
    op.create_index('ix_read_booking_detail_date_slot', 'booking_detail', ['date', 'slot'], schema='read')
    op.create_index('ix_read_booking_detail_status', 'booking_detail', ['status'], schema='read')
    op.create_index('ix_read_booking_detail_chef', 'booking_detail', ['chef_id'], schema='read')
    op.create_index('ix_read_booking_detail_payment_status', 'booking_detail', ['deposit_paid', 'fully_paid'], schema='read')


def downgrade() -> None:
    """Drop read model projections."""

    op.execute("DROP MATERIALIZED VIEW IF EXISTS read.booking_detail")
    op.execute("DROP MATERIALIZED VIEW IF EXISTS read.customer_360")
    op.execute("DROP MATERIALIZED VIEW IF EXISTS read.schedule_board")
    op.execute("DROP MATERIALIZED VIEW IF EXISTS read.payments_feed")
    op.execute("DROP MATERIALIZED VIEW IF EXISTS read.inbox_threads")
