"""
Add payment notification system tables

Revision ID: 009_payment_notifications
Revises: 008_add_user_roles
Create Date: 2025-10-30 00:00:00.000000

Tables:
- catering_bookings: Main booking entity for hibachi catering
- catering_payments: Payment transactions linked to bookings
- payment_notifications: Email notifications from payment providers

Features:
- Automatic payment detection from Gmail (Stripe, Venmo, Zelle, BofA)
- Smart matching using customer name, phone, amount
- Alternative payer support (friend/family payments)
- Manual review workflow for unmatched payments
- Comprehensive audit trail
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '009_payment_notifications'
down_revision = '008_add_user_roles'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create payment notification system tables"""
    
    # Create catering_bookings table
    op.create_table(
        'catering_bookings',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        
        # Customer Information
        sa.Column('customer_name', sa.String(length=255), nullable=False),
        sa.Column('customer_email', sa.String(length=255), nullable=False),
        sa.Column('customer_phone', sa.String(length=20), nullable=False),
        
        # Alternative payer (friend/family payments)
        sa.Column('alternative_payer_name', sa.String(length=255), nullable=True),
        sa.Column('alternative_payer_email', sa.String(length=255), nullable=True),
        sa.Column('alternative_payer_phone', sa.String(length=20), nullable=True),
        sa.Column('alternative_payer_venmo', sa.String(length=100), nullable=True),
        
        # Event Details
        sa.Column('event_date', sa.DateTime(), nullable=False),
        sa.Column('event_location', sa.Text(), nullable=False),
        sa.Column('guest_count', sa.Integer(), nullable=False),
        sa.Column('service_type', sa.String(length=100), nullable=True),
        
        # Pricing
        sa.Column('base_amount', sa.Numeric(precision=10, scale=2), nullable=False),
        sa.Column('tip_amount', sa.Numeric(precision=10, scale=2), nullable=True, server_default='0'),
        sa.Column('tax_amount', sa.Numeric(precision=10, scale=2), nullable=True, server_default='0'),
        sa.Column('total_amount', sa.Numeric(precision=10, scale=2), nullable=False),
        
        # Booking Status
        sa.Column('status', sa.String(length=50), nullable=True, server_default='pending'),
        
        # Special Requests
        sa.Column('special_requests', sa.Text(), nullable=True),
        sa.Column('dietary_restrictions', sa.Text(), nullable=True),
        sa.Column('internal_notes', sa.Text(), nullable=True),
        
        # Timestamps
        sa.Column('confirmed_at', sa.DateTime(), nullable=True),
        sa.Column('completed_at', sa.DateTime(), nullable=True),
        sa.Column('cancelled_at', sa.DateTime(), nullable=True),
        
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create indexes for catering_bookings
    op.create_index('idx_catering_booking_customer_name', 'catering_bookings', ['customer_name'])
    op.create_index('idx_catering_booking_customer_email', 'catering_bookings', ['customer_email'])
    op.create_index('idx_catering_booking_customer_phone', 'catering_bookings', ['customer_phone'])
    op.create_index('idx_catering_booking_event_date', 'catering_bookings', ['event_date'])
    op.create_index('idx_catering_booking_status', 'catering_bookings', ['status'])
    
    # Create catering_payments table
    op.create_table(
        'catering_payments',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        
        # Foreign Keys
        sa.Column('booking_id', sa.Integer(), nullable=False),
        sa.Column('notification_id', sa.Integer(), nullable=True),
        
        # Payment Details
        sa.Column('amount', sa.Numeric(precision=10, scale=2), nullable=False),
        sa.Column('payment_method', sa.Enum('STRIPE', 'VENMO', 'ZELLE', 'BANK_OF_AMERICA', 'PLAID', 'CASH', 'CHECK', 'OTHER', name='paymentprovider'), nullable=False),
        sa.Column('status', sa.String(length=50), nullable=True, server_default='pending'),
        
        # Transaction Information
        sa.Column('transaction_id', sa.String(length=255), nullable=True),
        sa.Column('sender_name', sa.String(length=255), nullable=True),
        sa.Column('sender_email', sa.String(length=255), nullable=True),
        sa.Column('sender_phone', sa.String(length=20), nullable=True),
        sa.Column('sender_username', sa.String(length=100), nullable=True),
        
        # Payment Type
        sa.Column('payment_type', sa.String(length=50), nullable=True, server_default='full'),
        
        # Processing
        sa.Column('processed_at', sa.DateTime(), nullable=True),
        sa.Column('confirmed_at', sa.DateTime(), nullable=True),
        sa.Column('confirmation_sent', sa.Boolean(), nullable=True, server_default='false'),
        
        # Notes
        sa.Column('payment_note', sa.Text(), nullable=True),
        sa.Column('admin_note', sa.Text(), nullable=True),
        
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['booking_id'], ['catering_bookings.id'], ondelete='CASCADE'),
    )
    
    # Create indexes for catering_payments
    op.create_index('idx_payment_booking_id', 'catering_payments', ['booking_id'])
    op.create_index('idx_payment_notification_id', 'catering_payments', ['notification_id'])
    op.create_index('idx_payment_method', 'catering_payments', ['payment_method'])
    op.create_index('idx_payment_status', 'catering_payments', ['status'])
    op.create_index('idx_payment_transaction_id', 'catering_payments', ['transaction_id'], unique=True)
    op.create_index('idx_payment_booking_status', 'catering_payments', ['booking_id', 'status'])
    op.create_index('idx_payment_method_status', 'catering_payments', ['payment_method', 'status'])
    
    # Create payment_notifications table
    op.create_table(
        'payment_notifications',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        
        # Email Details
        sa.Column('email_id', sa.String(length=255), nullable=False),
        sa.Column('email_subject', sa.String(length=500), nullable=False),
        sa.Column('email_from', sa.String(length=255), nullable=False),
        sa.Column('email_body', sa.Text(), nullable=True),
        sa.Column('received_at', sa.DateTime(), nullable=False),
        
        # Parsed Payment Information
        sa.Column('provider', sa.Enum('STRIPE', 'VENMO', 'ZELLE', 'BANK_OF_AMERICA', 'PLAID', 'CASH', 'CHECK', 'OTHER', name='paymentprovider'), nullable=False),
        sa.Column('amount', sa.Numeric(precision=10, scale=2), nullable=False),
        sa.Column('transaction_id', sa.String(length=255), nullable=True),
        
        # Sender Information
        sa.Column('sender_name', sa.String(length=255), nullable=True),
        sa.Column('sender_email', sa.String(length=255), nullable=True),
        sa.Column('sender_phone', sa.String(length=20), nullable=True),
        sa.Column('sender_username', sa.String(length=100), nullable=True),
        
        # Matching Information
        sa.Column('status', sa.Enum('DETECTED', 'PENDING_MATCH', 'MATCHED', 'CONFIRMED', 'MANUAL_REVIEW', 'IGNORED', 'ERROR', name='paymentnotificationstatus'), nullable=False, server_default='DETECTED'),
        sa.Column('match_score', sa.Integer(), nullable=True, server_default='0'),
        sa.Column('match_details', sa.JSON(), nullable=True),
        
        # Foreign Keys
        sa.Column('booking_id', sa.Integer(), nullable=True),
        sa.Column('payment_id', sa.Integer(), nullable=True),
        
        # Processing
        sa.Column('parsed_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('matched_at', sa.DateTime(), nullable=True),
        sa.Column('confirmed_at', sa.DateTime(), nullable=True),
        sa.Column('reviewed_by', postgresql.UUID(as_uuid=True), nullable=True),
        
        # Flags
        sa.Column('is_read', sa.Boolean(), nullable=True, server_default='false'),
        sa.Column('is_processed', sa.Boolean(), nullable=True, server_default='false'),
        sa.Column('requires_manual_review', sa.Boolean(), nullable=True, server_default='false'),
        sa.Column('is_duplicate', sa.Boolean(), nullable=True, server_default='false'),
        
        # Notes
        sa.Column('admin_notes', sa.Text(), nullable=True),
        sa.Column('error_message', sa.Text(), nullable=True),
        
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['booking_id'], ['catering_bookings.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['payment_id'], ['catering_payments.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['reviewed_by'], ['identity.users.id'], ondelete='SET NULL'),
    )
    
    # Create indexes for payment_notifications
    op.create_index('idx_notification_email_id', 'payment_notifications', ['email_id'], unique=True)
    op.create_index('idx_notification_email_from', 'payment_notifications', ['email_from'])
    op.create_index('idx_notification_received_at', 'payment_notifications', ['received_at'])
    op.create_index('idx_notification_provider', 'payment_notifications', ['provider'])
    op.create_index('idx_notification_status', 'payment_notifications', ['status'])
    op.create_index('idx_notification_sender_name', 'payment_notifications', ['sender_name'])
    op.create_index('idx_notification_sender_phone', 'payment_notifications', ['sender_phone'])
    op.create_index('idx_notification_transaction_id', 'payment_notifications', ['transaction_id'])
    op.create_index('idx_notification_booking_id', 'payment_notifications', ['booking_id'])
    op.create_index('idx_notification_payment_id', 'payment_notifications', ['payment_id'])
    op.create_index('idx_notification_is_processed', 'payment_notifications', ['is_processed'])
    op.create_index('idx_notification_requires_manual_review', 'payment_notifications', ['requires_manual_review'])
    op.create_index('idx_notification_status_processed', 'payment_notifications', ['status', 'is_processed'])
    op.create_index('idx_notification_provider_date', 'payment_notifications', ['provider', 'received_at'])
    op.create_index('idx_notification_manual_review', 'payment_notifications', ['requires_manual_review', 'is_processed'])
    
    # Add foreign key constraint for notification_id in catering_payments (after payment_notifications is created)
    op.create_foreign_key(
        'fk_catering_payments_notification_id',
        'catering_payments',
        'payment_notifications',
        ['notification_id'],
        ['id'],
        ondelete='SET NULL'
    )


def downgrade() -> None:
    """Drop payment notification system tables"""
    
    # Drop foreign key constraint first
    op.drop_constraint('fk_catering_payments_notification_id', 'catering_payments', type_='foreignkey')
    
    # Drop tables in reverse order
    op.drop_table('payment_notifications')
    op.drop_table('catering_payments')
    op.drop_table('catering_bookings')
    
    # Drop enums
    op.execute('DROP TYPE IF EXISTS paymentnotificationstatus')
    op.execute('DROP TYPE IF EXISTS paymentprovider')
