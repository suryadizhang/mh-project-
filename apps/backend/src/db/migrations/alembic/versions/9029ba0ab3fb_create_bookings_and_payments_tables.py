"""create_bookings_and_payments_tables

Creates core booking system tables:
- bookings: Customer reservation management with deposit tracking and race condition protection
- payments: Payment processing and reconciliation

This migration MUST run BEFORE the unique constraint migration (7e38568a1d1b).

Revision ID: 9029ba0ab3fb
Revises: caf902c5e081
Create Date: 2025-11-25 15:48:02.779947

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '9029ba0ab3fb'
down_revision = 'caf902c5e081'  # ← Changed from 7e38568a1d1b to caf902c5e081
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create booking status enum
    booking_status_enum = postgresql.ENUM(
        'pending', 'confirmed', 'seated', 'completed', 'cancelled', 'no_show',
        name='bookingstatus',
        create_type=False
    )
    booking_status_enum.create(op.get_bind(), checkfirst=True)

    # Create payment status enum
    payment_status_enum = postgresql.ENUM(
        'pending', 'completed', 'failed', 'refunded', 'cancelled',
        name='paymentstatus',
        create_type=False
    )
    payment_status_enum.create(op.get_bind(), checkfirst=True)

    # Create bookings table
    op.create_table(
        'bookings',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('customer_id', sa.String(), nullable=False),  # ← Changed from Integer to String (matches customers.id VARCHAR/UUID)
        sa.Column('booking_datetime', sa.DateTime(), nullable=False),
        sa.Column('party_size', sa.Integer(), nullable=False),
        sa.Column('status', booking_status_enum, nullable=False, server_default='pending'),
        sa.Column('version', sa.Integer(), nullable=False, server_default='1'),

        # Contact information
        sa.Column('contact_phone', sa.String(20), nullable=True),
        sa.Column('contact_email', sa.String(255), nullable=True),

        # TCPA compliance
        sa.Column('sms_consent', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('sms_consent_timestamp', sa.DateTime(), nullable=True),

        # Special requests
        sa.Column('special_requests', sa.Text(), nullable=True),
        sa.Column('internal_notes', sa.Text(), nullable=True),

        # Status timestamps
        sa.Column('confirmed_at', sa.DateTime(), nullable=True),
        sa.Column('seated_at', sa.DateTime(), nullable=True),
        sa.Column('completed_at', sa.DateTime(), nullable=True),
        sa.Column('cancelled_at', sa.DateTime(), nullable=True),
        sa.Column('cancellation_reason', sa.Text(), nullable=True),

        # Deposit deadline system
        sa.Column('customer_deposit_deadline', sa.DateTime(), nullable=True),
        sa.Column('internal_deadline', sa.DateTime(), nullable=True),
        sa.Column('deposit_deadline', sa.DateTime(), nullable=True),  # Deprecated

        # Manual deposit confirmation
        sa.Column('deposit_confirmed_at', sa.DateTime(), nullable=True),
        sa.Column('deposit_confirmed_by', sa.String(255), nullable=True),

        # Admin hold system
        sa.Column('hold_on_request', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('held_by', sa.String(255), nullable=True),
        sa.Column('held_at', sa.DateTime(), nullable=True),
        sa.Column('hold_reason', sa.Text(), nullable=True),

        # Table assignment
        sa.Column('table_number', sa.String(10), nullable=True),

        # Audit timestamps (from BaseModel)
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),

        # Primary key and foreign keys
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['customer_id'], ['customers.id'], ondelete='CASCADE'),
    )

    # Create indexes for bookings
    op.create_index('ix_bookings_customer_id', 'bookings', ['customer_id'])
    op.create_index('ix_bookings_booking_datetime', 'bookings', ['booking_datetime'])
    op.create_index('ix_bookings_status', 'bookings', ['status'])
    op.create_index('ix_bookings_customer_deposit_deadline', 'bookings', ['customer_deposit_deadline'])
    op.create_index('ix_bookings_internal_deadline', 'bookings', ['internal_deadline'])

    # Create payments table (skip if already exists - payments table was created earlier)
    # Check if table exists first
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    if 'payments' not in inspector.get_table_names():
        op.create_table(
            'payments',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('booking_id', sa.Integer(), nullable=False),

            # Payment details
            sa.Column('amount', sa.Numeric(10, 2), nullable=False),
            sa.Column('payment_method', sa.String(50), nullable=False),
            sa.Column('payment_reference', sa.String(255), nullable=True),
            sa.Column('status', payment_status_enum, nullable=False, server_default='pending'),

            # Payment source information
            sa.Column('sender_name', sa.String(255), nullable=True),
            sa.Column('sender_phone', sa.String(20), nullable=True),
            sa.Column('sender_email', sa.String(255), nullable=True),

            # Notification details
            sa.Column('received_at', sa.DateTime(), nullable=True),
            sa.Column('notification_email_id', sa.String(255), nullable=True),

            # Processing info
            sa.Column('processed_by', sa.String(100), nullable=True),
            sa.Column('processed_at', sa.DateTime(), nullable=True),
            sa.Column('confirmation_sent_at', sa.DateTime(), nullable=True),

            # Notes
            sa.Column('notes', sa.Text(), nullable=True),
            sa.Column('internal_notes', sa.Text(), nullable=True),

            # Audit timestamps (from BaseModel)
            sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
            sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),

            # Primary key and foreign keys
            sa.PrimaryKeyConstraint('id'),
            sa.ForeignKeyConstraint(['booking_id'], ['bookings.id'], ondelete='CASCADE'),
        )

        # Create indexes for payments
        op.create_index('ix_payments_booking_id', 'payments', ['booking_id'])
        op.create_index('ix_payments_status', 'payments', ['status'])
        op.create_index('ix_payments_received_at', 'payments', ['received_at'])


def downgrade() -> None:
    # Drop tables
    op.drop_table('payments')
    op.drop_table('bookings')

    # Drop enums
    op.execute('DROP TYPE IF EXISTS paymentstatus')
    op.execute('DROP TYPE IF EXISTS bookingstatus')
