"""Create CRM schemas and tables

Revision ID: 001
Revises:
Create Date: 2025-09-23 12:00:00.000000

"""
import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '001'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create CRM database schemas and tables with proper constraints."""

    # Create schemas
    op.execute("CREATE SCHEMA IF NOT EXISTS core")
    op.execute("CREATE SCHEMA IF NOT EXISTS events")
    op.execute("CREATE SCHEMA IF NOT EXISTS integra")
    op.execute("CREATE SCHEMA IF NOT EXISTS read")


    # Core schema tables
    op.create_table(
        'customers',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('first_name', sa.String(100), nullable=False),
        sa.Column('last_name', sa.String(100), nullable=False),
        sa.Column('email_encrypted', sa.Text(), nullable=False),
        sa.Column('phone_encrypted', sa.Text(), nullable=False),
        sa.Column('consent_sms', sa.Boolean(), nullable=False, default=False),
        sa.Column('consent_email', sa.Boolean(), nullable=False, default=False),
        sa.Column('consent_updated_at', sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column('timezone', sa.String(50), nullable=False, default='America/Los_Angeles'),
        sa.Column('tags', postgresql.ARRAY(sa.String(50)), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text('NOW()')),
        sa.Column('updated_at', sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text('NOW()')),
        sa.Column('deleted_at', sa.TIMESTAMP(timezone=True), nullable=True),
        schema='core'
    )

    # Unique constraint on encrypted email where not deleted
    op.execute("""
        CREATE UNIQUE INDEX ix_core_customers_email_active
        ON core.customers (email_encrypted)
        WHERE deleted_at IS NULL
    """)

    op.create_table(
        'chefs',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('name', sa.String(100), nullable=False),
        sa.Column('email', sa.String(255), nullable=False),
        sa.Column('phone', sa.String(20), nullable=True),
        sa.Column('zones', postgresql.ARRAY(sa.String(50)), nullable=False),
        sa.Column('skills', postgresql.ARRAY(sa.String(50)), nullable=True),
        sa.Column('google_calendar_id', sa.String(255), nullable=True),
        sa.Column('buffer_setup_minutes', sa.Integer(), nullable=False, default=30),
        sa.Column('buffer_teardown_minutes', sa.Integer(), nullable=False, default=30),
        sa.Column('is_active', sa.Boolean(), nullable=False, default=True),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text('NOW()')),
        sa.Column('updated_at', sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text('NOW()')),
        sa.Column('deleted_at', sa.TIMESTAMP(timezone=True), nullable=True),
        schema='core'
    )

    op.create_table(
        'bookings',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('customer_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('date', sa.Date(), nullable=False),
        sa.Column('slot', sa.Time(), nullable=False),
        sa.Column('address_encrypted', sa.Text(), nullable=False),
        sa.Column('zone', sa.String(50), nullable=False),
        sa.Column('chef_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('status', sa.Enum('new', 'deposit_pending', 'confirmed', 'completed', 'cancelled', 'no_show', name='booking_status', create_type=False), nullable=False, default='new'),
        sa.Column('party_adults', sa.Integer(), nullable=False),
        sa.Column('party_kids', sa.Integer(), nullable=False, default=0),
        sa.Column('deposit_due_cents', sa.Integer(), nullable=False),
        sa.Column('total_due_cents', sa.Integer(), nullable=False),
        sa.Column('menu_items', postgresql.JSONB(), nullable=True),
        sa.Column('special_requests', sa.Text(), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('source', sa.String(50), nullable=False),
        sa.Column('metadata', postgresql.JSONB(), nullable=True),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text('NOW()')),
        sa.Column('updated_at', sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text('NOW()')),
        sa.Column('deleted_at', sa.TIMESTAMP(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['customer_id'], ['core.customers.id'], ondelete='RESTRICT'),
        sa.ForeignKeyConstraint(['chef_id'], ['core.chefs.id'], ondelete='SET NULL'),
        sa.CheckConstraint('party_adults > 0', name='check_party_adults_positive'),
        sa.CheckConstraint('party_kids >= 0', name='check_party_kids_non_negative'),
        sa.CheckConstraint('deposit_due_cents >= 0', name='check_deposit_non_negative'),
        sa.CheckConstraint('total_due_cents >= deposit_due_cents', name='check_total_gte_deposit'),
        schema='core'
    )

    # Unique constraint: one chef cannot have overlapping bookings
    op.execute("""
        CREATE UNIQUE INDEX ix_core_bookings_chef_slot_unique
        ON core.bookings (chef_id, date, slot)
        WHERE chef_id IS NOT NULL AND deleted_at IS NULL
    """)

    op.create_table(
        'message_threads',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('customer_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('channel', sa.Enum('web_chat', 'sms', 'email', 'phone', 'admin', name='message_channel', create_type=False), nullable=False),
        sa.Column('external_thread_id', sa.String(255), nullable=True),
        sa.Column('status', sa.Enum('active', 'waiting', 'resolved', 'escalated', name='thread_status', create_type=False), nullable=False, default='active'),
        sa.Column('assigned_agent_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('ai_mode', sa.Boolean(), nullable=False, default=True),
        sa.Column('last_message_at', sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text('NOW()')),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text('NOW()')),
        sa.Column('updated_at', sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text('NOW()')),
        sa.Column('deleted_at', sa.TIMESTAMP(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['customer_id'], ['core.customers.id'], ondelete='CASCADE'),
        schema='core'
    )

    op.create_table(
        'messages',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('thread_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('direction', sa.String(10), nullable=False),  # 'inbound' or 'outbound'
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('sender_type', sa.String(20), nullable=False),  # 'customer', 'agent', 'ai', 'system'
        sa.Column('sender_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('metadata', postgresql.JSONB(), nullable=True),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text('NOW()')),
        sa.ForeignKeyConstraint(['thread_id'], ['core.message_threads.id'], ondelete='CASCADE'),
        sa.CheckConstraint("direction IN ('inbound', 'outbound')", name='check_message_direction'),
        sa.CheckConstraint("sender_type IN ('customer', 'agent', 'ai', 'system')", name='check_sender_type'),
        schema='core'
    )

    # Events schema tables
    op.create_table(
        'domain_events',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('aggregate_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('aggregate_type', sa.String(100), nullable=False),
        sa.Column('event_type', sa.String(100), nullable=False),
        sa.Column('payload', postgresql.JSONB(), nullable=False),
        sa.Column('version', sa.Integer(), nullable=False),
        sa.Column('occurred_at', sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text('NOW()')),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text('NOW()')),
        sa.Column('hash_previous', sa.String(64), nullable=True),
        sa.Column('hash_current', sa.String(64), nullable=False),
        schema='events'
    )

    # Index for event replay and audit trail
    op.create_index('ix_events_domain_events_aggregate', 'domain_events', ['aggregate_id', 'version'], schema='events')
    op.create_index('ix_events_domain_events_type', 'domain_events', ['event_type'], schema='events')
    op.create_index('ix_events_domain_events_occurred', 'domain_events', ['occurred_at'], schema='events')

    op.create_table(
        'outbox',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('event_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('target', sa.String(50), nullable=False),
        sa.Column('payload', postgresql.JSONB(), nullable=False),
        sa.Column('attempts', sa.Integer(), nullable=False, default=0),
        sa.Column('max_attempts', sa.Integer(), nullable=False, default=3),
        sa.Column('next_attempt_at', sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text('NOW()')),
        sa.Column('status', sa.Enum('pending', 'processing', 'completed', 'failed', 'cancelled', name='outbox_status', create_type=False), nullable=False, default='pending'),
        sa.Column('error', sa.Text(), nullable=True),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text('NOW()')),
        sa.Column('completed_at', sa.TIMESTAMP(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['event_id'], ['events.domain_events.id'], ondelete='CASCADE'),
        schema='events'
    )

    op.create_index('ix_events_outbox_status_next_attempt', 'outbox', ['status', 'next_attempt_at'], schema='events')

    op.create_table(
        'inbox',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('signature', sa.String(255), nullable=False),  # For webhook idempotency
        sa.Column('source', sa.String(50), nullable=False),
        sa.Column('payload', postgresql.JSONB(), nullable=False),
        sa.Column('processed', sa.Boolean(), nullable=False, default=False),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text('NOW()')),
        sa.Column('processed_at', sa.TIMESTAMP(timezone=True), nullable=True),
        schema='events'
    )

    op.create_index('ix_events_inbox_signature', 'inbox', ['signature'], unique=True, schema='events')

    # Integration schema tables
    op.create_table(
        'payment_events',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('provider', sa.Enum('stripe', 'plaid', 'manual', name='payment_provider', create_type=False), nullable=False),
        sa.Column('provider_id', sa.String(255), nullable=False),
        sa.Column('method', sa.Enum('card', 'ach', 'venmo', 'zelle', 'cash', 'check', name='payment_method', create_type=False), nullable=False),
        sa.Column('amount_cents', sa.Integer(), nullable=False),
        sa.Column('currency', sa.String(3), nullable=False, default='USD'),
        sa.Column('occurred_at', sa.TIMESTAMP(timezone=True), nullable=False),
        sa.Column('memo', sa.Text(), nullable=True),
        sa.Column('raw_data', postgresql.JSONB(), nullable=False),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text('NOW()')),
        sa.CheckConstraint('amount_cents > 0', name='check_payment_amount_positive'),
        schema='integra'
    )

    op.create_index('ix_integra_payment_events_provider_id', 'payment_events', ['provider', 'provider_id'], unique=True, schema='integra')
    op.create_index('ix_integra_payment_events_occurred', 'payment_events', ['occurred_at'], schema='integra')

    op.create_table(
        'payment_matches',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('payment_event_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('booking_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('confidence', sa.Numeric(3, 2), nullable=False),
        sa.Column('match_method', sa.String(50), nullable=False),
        sa.Column('status', sa.String(20), nullable=False, default='auto'),
        sa.Column('reviewed_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text('NOW()')),
        sa.ForeignKeyConstraint(['payment_event_id'], ['integra.payment_events.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['booking_id'], ['core.bookings.id'], ondelete='CASCADE'),
        sa.CheckConstraint('confidence >= 0 AND confidence <= 1', name='check_confidence_range'),
        sa.CheckConstraint("status IN ('auto', 'manual', 'ignored')", name='check_match_status'),
        schema='integra'
    )

    op.create_table(
        'call_sessions',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('booking_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('customer_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('direction', sa.String(10), nullable=False),
        sa.Column('phone_number', sa.String(20), nullable=False),
        sa.Column('duration_seconds', sa.Integer(), nullable=True),
        sa.Column('transcript', sa.Text(), nullable=True),
        sa.Column('outcome', sa.String(50), nullable=True),
        sa.Column('recording_url', sa.String(500), nullable=True),
        sa.Column('ringcentral_call_id', sa.String(255), nullable=True),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text('NOW()')),
        sa.Column('ended_at', sa.TIMESTAMP(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['booking_id'], ['core.bookings.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['customer_id'], ['core.customers.id'], ondelete='SET NULL'),
        sa.CheckConstraint("direction IN ('inbound', 'outbound')", name='check_call_direction'),
        schema='integra'
    )

    # Create indexes for performance
    op.create_index('ix_core_bookings_date_slot', 'bookings', ['date', 'slot'], schema='core')
    op.create_index('ix_core_bookings_customer_id', 'bookings', ['customer_id'], schema='core')
    op.create_index('ix_core_bookings_status', 'bookings', ['status'], schema='core')
    op.create_index('ix_core_messages_thread_created', 'messages', ['thread_id', 'created_at'], schema='core')
    op.create_index('ix_core_message_threads_customer', 'message_threads', ['customer_id'], schema='core')


def downgrade() -> None:
    """Drop CRM schemas and tables."""

    # Drop tables in reverse dependency order
    op.drop_table('call_sessions', schema='integra')
    op.drop_table('payment_matches', schema='integra')
    op.drop_table('payment_events', schema='integra')

    op.drop_table('inbox', schema='events')
    op.drop_table('outbox', schema='events')
    op.drop_table('domain_events', schema='events')

    op.drop_table('messages', schema='core')
    op.drop_table('message_threads', schema='core')
    op.drop_table('bookings', schema='core')
    op.drop_table('chefs', schema='core')
    op.drop_table('customers', schema='core')

    # Drop custom types
    op.execute("DROP TYPE IF EXISTS thread_status")
    op.execute("DROP TYPE IF EXISTS message_channel")
    op.execute("DROP TYPE IF EXISTS outbox_status")
    op.execute("DROP TYPE IF EXISTS payment_method")
    op.execute("DROP TYPE IF EXISTS payment_provider")
    op.execute("DROP TYPE IF EXISTS booking_status")

    # Drop schemas
    op.execute("DROP SCHEMA IF EXISTS read CASCADE")
    op.execute("DROP SCHEMA IF EXISTS integra CASCADE")
    op.execute("DROP SCHEMA IF EXISTS events CASCADE")
    op.execute("DROP SCHEMA IF EXISTS core CASCADE")
