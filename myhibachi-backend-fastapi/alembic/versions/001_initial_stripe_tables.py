"""Initial Stripe integration tables

Revision ID: 001_initial_stripe_tables
Revises: 
Create Date: 2025-09-01 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '001_initial_stripe_tables'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create customers table
    op.create_table('customers',
    sa.Column('id', sa.String(), nullable=False),
    sa.Column('user_id', sa.String(), nullable=False),
    sa.Column('email', sa.String(), nullable=False),
    sa.Column('stripe_customer_id', sa.String(), nullable=False),
    sa.Column('name', sa.String(), nullable=True),
    sa.Column('phone', sa.String(), nullable=True),
    sa.Column('preferred_payment_method', sa.String(), nullable=True),
    sa.Column('total_spent', sa.Numeric(precision=10, scale=2), nullable=True),
    sa.Column('total_bookings', sa.Integer(), nullable=True),
    sa.Column('zelle_savings', sa.Numeric(precision=10, scale=2), nullable=True),
    sa.Column('loyalty_tier', sa.String(), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
    sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('email'),
    sa.UniqueConstraint('stripe_customer_id'),
    sa.UniqueConstraint('user_id')
    )
    op.create_index(op.f('ix_customers_email'), 'customers', ['email'], unique=False)
    op.create_index(op.f('ix_customers_stripe_customer_id'), 'customers', ['stripe_customer_id'], unique=False)
    op.create_index(op.f('ix_customers_user_id'), 'customers', ['user_id'], unique=False)

    # Create payments table
    op.create_table('payments',
    sa.Column('id', sa.String(), nullable=False),
    sa.Column('user_id', sa.String(), nullable=False),
    sa.Column('booking_id', sa.String(), nullable=True),
    sa.Column('stripe_payment_intent_id', sa.String(), nullable=True),
    sa.Column('stripe_customer_id', sa.String(), nullable=True),
    sa.Column('amount', sa.Numeric(precision=10, scale=2), nullable=False),
    sa.Column('currency', sa.String(), nullable=True),
    sa.Column('status', sa.String(), nullable=False),
    sa.Column('method', sa.String(), nullable=False),
    sa.Column('payment_type', sa.String(), nullable=True),
    sa.Column('description', sa.Text(), nullable=True),
    sa.Column('metadata_json', sa.Text(), nullable=True),
    sa.Column('stripe_fee', sa.Numeric(precision=10, scale=2), nullable=True),
    sa.Column('net_amount', sa.Numeric(precision=10, scale=2), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
    sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
    sa.ForeignKeyConstraint(['stripe_customer_id'], ['customers.stripe_customer_id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_payments_booking_id'), 'payments', ['booking_id'], unique=False)
    op.create_index(op.f('ix_payments_status'), 'payments', ['status'], unique=False)
    op.create_index(op.f('ix_payments_stripe_payment_intent_id'), 'payments', ['stripe_payment_intent_id'], unique=False)
    op.create_index(op.f('ix_payments_user_id'), 'payments', ['user_id'], unique=False)

    # Create invoices table
    op.create_table('invoices',
    sa.Column('id', sa.String(), nullable=False),
    sa.Column('user_id', sa.String(), nullable=False),
    sa.Column('booking_id', sa.String(), nullable=True),
    sa.Column('stripe_invoice_id', sa.String(), nullable=False),
    sa.Column('stripe_customer_id', sa.String(), nullable=True),
    sa.Column('amount_due', sa.Numeric(precision=10, scale=2), nullable=False),
    sa.Column('amount_paid', sa.Numeric(precision=10, scale=2), nullable=True),
    sa.Column('currency', sa.String(), nullable=True),
    sa.Column('status', sa.String(), nullable=False),
    sa.Column('hosted_invoice_url', sa.String(), nullable=True),
    sa.Column('invoice_pdf_url', sa.String(), nullable=True),
    sa.Column('due_date', sa.DateTime(timezone=True), nullable=True),
    sa.Column('paid_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
    sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
    sa.ForeignKeyConstraint(['stripe_customer_id'], ['customers.stripe_customer_id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_invoices_booking_id'), 'invoices', ['booking_id'], unique=False)
    op.create_index(op.f('ix_invoices_status'), 'invoices', ['status'], unique=False)
    op.create_index(op.f('ix_invoices_stripe_invoice_id'), 'invoices', ['stripe_invoice_id'], unique=False)
    op.create_index(op.f('ix_invoices_user_id'), 'invoices', ['user_id'], unique=False)

    # Create products table
    op.create_table('products',
    sa.Column('id', sa.String(), nullable=False),
    sa.Column('stripe_product_id', sa.String(), nullable=False),
    sa.Column('name', sa.String(), nullable=False),
    sa.Column('description', sa.Text(), nullable=True),
    sa.Column('active', sa.Boolean(), nullable=True),
    sa.Column('category', sa.String(), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
    sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_products_stripe_product_id'), 'products', ['stripe_product_id'], unique=False)

    # Create prices table
    op.create_table('prices',
    sa.Column('id', sa.String(), nullable=False),
    sa.Column('stripe_price_id', sa.String(), nullable=False),
    sa.Column('product_id', sa.String(), nullable=True),
    sa.Column('stripe_product_id', sa.String(), nullable=False),
    sa.Column('unit_amount', sa.Integer(), nullable=False),
    sa.Column('currency', sa.String(), nullable=True),
    sa.Column('active', sa.Boolean(), nullable=True),
    sa.Column('recurring_interval', sa.String(), nullable=True),
    sa.Column('recurring_interval_count', sa.Integer(), nullable=True),
    sa.Column('nickname', sa.String(), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
    sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
    sa.ForeignKeyConstraint(['product_id'], ['products.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_prices_stripe_price_id'), 'prices', ['stripe_price_id'], unique=False)

    # Create webhook_events table
    op.create_table('webhook_events',
    sa.Column('id', sa.String(), nullable=False),
    sa.Column('type', sa.String(), nullable=False),
    sa.Column('stripe_event_id', sa.String(), nullable=False),
    sa.Column('payload_json', sa.Text(), nullable=False),
    sa.Column('processed', sa.Boolean(), nullable=True),
    sa.Column('processing_error', sa.Text(), nullable=True),
    sa.Column('retry_count', sa.Integer(), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
    sa.Column('processed_at', sa.DateTime(timezone=True), nullable=True),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_webhook_events_stripe_event_id'), 'webhook_events', ['stripe_event_id'], unique=False)
    op.create_index(op.f('ix_webhook_events_type'), 'webhook_events', ['type'], unique=False)

    # Create refunds table
    op.create_table('refunds',
    sa.Column('id', sa.String(), nullable=False),
    sa.Column('stripe_refund_id', sa.String(), nullable=False),
    sa.Column('payment_id', sa.String(), nullable=True),
    sa.Column('amount', sa.Numeric(precision=10, scale=2), nullable=False),
    sa.Column('currency', sa.String(), nullable=True),
    sa.Column('status', sa.String(), nullable=False),
    sa.Column('reason', sa.String(), nullable=True),
    sa.Column('requested_by', sa.String(), nullable=True),
    sa.Column('notes', sa.Text(), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
    sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
    sa.ForeignKeyConstraint(['payment_id'], ['payments.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_refunds_stripe_refund_id'), 'refunds', ['stripe_refund_id'], unique=False)

    # Create disputes table
    op.create_table('disputes',
    sa.Column('id', sa.String(), nullable=False),
    sa.Column('stripe_dispute_id', sa.String(), nullable=False),
    sa.Column('payment_id', sa.String(), nullable=True),
    sa.Column('amount', sa.Numeric(precision=10, scale=2), nullable=False),
    sa.Column('currency', sa.String(), nullable=True),
    sa.Column('status', sa.String(), nullable=False),
    sa.Column('reason', sa.String(), nullable=True),
    sa.Column('evidence_details', sa.Text(), nullable=True),
    sa.Column('evidence_due_by', sa.DateTime(timezone=True), nullable=True),
    sa.Column('resolved_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('resolution', sa.String(), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
    sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
    sa.ForeignKeyConstraint(['payment_id'], ['payments.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_disputes_stripe_dispute_id'), 'disputes', ['stripe_dispute_id'], unique=False)

    # Create custom indexes for better performance
    op.create_index('idx_payments_user_booking', 'payments', ['user_id', 'booking_id'], unique=False)
    op.create_index('idx_payments_status_method', 'payments', ['status', 'method'], unique=False)
    op.create_index('idx_invoices_user_booking', 'invoices', ['user_id', 'booking_id'], unique=False)
    op.create_index('idx_webhook_events_type_processed', 'webhook_events', ['type', 'processed'], unique=False)


def downgrade() -> None:
    # Drop custom indexes
    op.drop_index('idx_webhook_events_type_processed', table_name='webhook_events')
    op.drop_index('idx_invoices_user_booking', table_name='invoices')
    op.drop_index('idx_payments_status_method', table_name='payments')
    op.drop_index('idx_payments_user_booking', table_name='payments')
    
    # Drop tables in reverse order
    op.drop_table('disputes')
    op.drop_table('refunds')
    op.drop_table('webhook_events')
    op.drop_table('prices')
    op.drop_table('products')
    op.drop_table('invoices')
    op.drop_table('payments')
    op.drop_table('customers')
