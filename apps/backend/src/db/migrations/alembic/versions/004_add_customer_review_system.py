"""Add Customer Review System

Revision ID: 004_add_customer_review_system
Revises: 9fd62e8ed3b4
Create Date: 2025-10-25 10:00:00.000000

"""
import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '004_add_customer_review_system'
down_revision = '9fd62e8ed3b4'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Add customer review and discount coupon system."""

    # Create review schema
    op.execute("CREATE SCHEMA IF NOT EXISTS feedback")

    # Create enums using native Alembic Enum with create_type=False since we'll create them manually if needed
    # First check and create enums - these will be created by the first Enum column that references them
    # No manual creation needed with create_type=False

    # Create customer_reviews table
    op.create_table(
        'customer_reviews',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('station_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('booking_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('customer_id', postgresql.UUID(as_uuid=True), nullable=False),
        
        # Review data
        sa.Column('rating', sa.Enum('great', 'good', 'okay', 'could_be_better', name='review_rating', schema='feedback'), nullable=False),
        sa.Column('status', sa.Enum('pending', 'submitted', 'escalated', 'resolved', 'archived', name='review_status', schema='feedback'), nullable=False, default='pending'),
        
        # For negative reviews
        sa.Column('complaint_text', sa.Text(), nullable=True),
        sa.Column('improvement_suggestions', sa.Text(), nullable=True),
        
        # External review tracking
        sa.Column('left_yelp_review', sa.Boolean(), nullable=False, default=False),
        sa.Column('left_google_review', sa.Boolean(), nullable=False, default=False),
        sa.Column('external_review_date', sa.TIMESTAMP(timezone=True), nullable=True),
        
        # SMS tracking
        sa.Column('sms_sent_at', sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column('sms_message_id', sa.String(100), nullable=True),
        sa.Column('review_link', sa.String(500), nullable=True),
        
        # Follow-up tracking
        sa.Column('admin_notified_at', sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column('ai_escalated_at', sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column('resolved_at', sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column('resolved_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('resolution_notes', sa.Text(), nullable=True),
        
        # Coupon issued
        sa.Column('coupon_issued', sa.Boolean(), nullable=False, default=False),
        sa.Column('coupon_id', postgresql.UUID(as_uuid=True), nullable=True),
        
        # Metadata
        sa.Column('ip_address', sa.String(45), nullable=True),
        sa.Column('user_agent', sa.String(500), nullable=True),
        sa.Column('metadata', postgresql.JSONB(), nullable=True),
        
        # Timestamps
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text('NOW()')),
        sa.Column('updated_at', sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text('NOW()')),
        sa.Column('submitted_at', sa.TIMESTAMP(timezone=True), nullable=True),
        
        # Foreign keys
        sa.ForeignKeyConstraint(['station_id'], ['identity.stations.id'], ondelete='RESTRICT'),
        sa.ForeignKeyConstraint(['booking_id'], ['core.bookings.id'], ondelete='RESTRICT'),
        sa.ForeignKeyConstraint(['customer_id'], ['core.customers.id'], ondelete='RESTRICT'),
        
        # Constraints
        sa.CheckConstraint(
            "(rating IN ('great', 'good') AND complaint_text IS NULL) OR "
            "(rating IN ('okay', 'could_be_better') AND complaint_text IS NOT NULL)",
            name='check_complaint_required_for_negative'
        ),
        
        schema='feedback'
    )

    # Create discount_coupons table
    op.create_table(
        'discount_coupons',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('station_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('customer_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('review_id', postgresql.UUID(as_uuid=True), nullable=True),
        
        # Coupon details
        sa.Column('coupon_code', sa.String(50), nullable=False, unique=True),
        sa.Column('discount_type', sa.String(20), nullable=False),  # 'percentage', 'fixed_amount'
        sa.Column('discount_value', sa.Integer(), nullable=False),  # e.g., 10 for 10%, or 1000 for $10.00
        sa.Column('description', sa.Text(), nullable=True),
        
        # Usage constraints
        sa.Column('minimum_order_cents', sa.Integer(), nullable=False, default=0),
        sa.Column('max_uses', sa.Integer(), nullable=False, default=1),
        sa.Column('times_used', sa.Integer(), nullable=False, default=0),
        
        # Status and validity
        sa.Column('status', sa.Enum('active', 'used', 'expired', 'cancelled', name='coupon_status', schema='feedback'), nullable=False, default='active'),
        sa.Column('valid_from', sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text('NOW()')),
        sa.Column('valid_until', sa.TIMESTAMP(timezone=True), nullable=False),
        
        # Usage tracking
        sa.Column('used_at', sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column('used_in_booking_id', postgresql.UUID(as_uuid=True), nullable=True),
        
        # Issue reason
        sa.Column('issue_reason', sa.String(100), nullable=False),  # 'negative_review', 'complaint_resolution', 'promotion'
        sa.Column('issued_by', postgresql.UUID(as_uuid=True), nullable=True),  # admin user or NULL for auto-issued
        
        # Metadata
        sa.Column('metadata', postgresql.JSONB(), nullable=True),
        
        # Timestamps
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text('NOW()')),
        sa.Column('updated_at', sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text('NOW()')),
        
        # Foreign keys
        sa.ForeignKeyConstraint(['station_id'], ['identity.stations.id'], ondelete='RESTRICT'),
        sa.ForeignKeyConstraint(['customer_id'], ['core.customers.id'], ondelete='RESTRICT'),
        sa.ForeignKeyConstraint(['review_id'], ['feedback.customer_reviews.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['used_in_booking_id'], ['core.bookings.id'], ondelete='SET NULL'),
        
        # Constraints
        sa.CheckConstraint('discount_value > 0', name='check_discount_positive'),
        sa.CheckConstraint('minimum_order_cents >= 0', name='check_min_order_non_negative'),
        sa.CheckConstraint('max_uses > 0', name='check_max_uses_positive'),
        sa.CheckConstraint('times_used >= 0', name='check_times_used_non_negative'),
        sa.CheckConstraint('times_used <= max_uses', name='check_times_used_within_limit'),
        sa.CheckConstraint('valid_until > valid_from', name='check_valid_date_range'),
        sa.CheckConstraint(
            "discount_type IN ('percentage', 'fixed_amount')",
            name='check_discount_type_valid'
        ),
        sa.CheckConstraint(
            "(discount_type = 'percentage' AND discount_value <= 100) OR discount_type = 'fixed_amount'",
            name='check_percentage_max_100'
        ),
        
        schema='feedback'
    )

    # Create review_escalations table for tracking escalation history
    op.create_table(
        'review_escalations',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('review_id', postgresql.UUID(as_uuid=True), nullable=False),
        
        # Escalation details
        sa.Column('escalation_type', sa.String(50), nullable=False),  # 'admin_notification', 'ai_agent', 'manual'
        sa.Column('priority', sa.String(20), nullable=False, default='medium'),  # 'low', 'medium', 'high', 'urgent'
        sa.Column('assigned_to', postgresql.UUID(as_uuid=True), nullable=True),
        
        # Content
        sa.Column('escalation_reason', sa.Text(), nullable=False),
        sa.Column('action_taken', sa.Text(), nullable=True),
        
        # Status
        sa.Column('status', sa.String(20), nullable=False, default='open'),  # 'open', 'in_progress', 'resolved', 'closed'
        sa.Column('resolved_at', sa.TIMESTAMP(timezone=True), nullable=True),
        
        # Timestamps
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text('NOW()')),
        sa.Column('updated_at', sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text('NOW()')),
        
        # Foreign keys
        sa.ForeignKeyConstraint(['review_id'], ['feedback.customer_reviews.id'], ondelete='CASCADE'),
        
        schema='feedback'
    )

    # Create indexes for performance
    op.create_index('ix_feedback_reviews_station_customer', 'customer_reviews', ['station_id', 'customer_id'], schema='feedback')
    op.create_index('ix_feedback_reviews_booking', 'customer_reviews', ['booking_id'], schema='feedback')
    op.create_index('ix_feedback_reviews_rating', 'customer_reviews', ['rating'], schema='feedback')
    op.create_index('ix_feedback_reviews_status', 'customer_reviews', ['status'], schema='feedback')
    op.create_index('ix_feedback_reviews_created', 'customer_reviews', ['created_at'], schema='feedback')
    
    op.create_index('ix_feedback_coupons_station_customer', 'discount_coupons', ['station_id', 'customer_id'], schema='feedback')
    op.create_index('ix_feedback_coupons_code', 'discount_coupons', ['coupon_code'], unique=True, schema='feedback')
    op.create_index('ix_feedback_coupons_status', 'discount_coupons', ['status'], schema='feedback')
    op.create_index('ix_feedback_coupons_valid_until', 'discount_coupons', ['valid_until'], schema='feedback')
    op.create_index('ix_feedback_coupons_review', 'discount_coupons', ['review_id'], schema='feedback')
    
    op.create_index('ix_feedback_escalations_review', 'review_escalations', ['review_id'], schema='feedback')
    op.create_index('ix_feedback_escalations_status', 'review_escalations', ['status'], schema='feedback')
    op.create_index('ix_feedback_escalations_priority', 'review_escalations', ['priority'], schema='feedback')

    # Create a view for admin dashboard
    op.execute("""
        CREATE VIEW feedback.review_analytics AS
        SELECT
            r.station_id,
            r.rating,
            r.status,
            COUNT(*) as review_count,
            COUNT(CASE WHEN r.left_yelp_review THEN 1 END) as yelp_reviews,
            COUNT(CASE WHEN r.left_google_review THEN 1 END) as google_reviews,
            COUNT(CASE WHEN r.coupon_issued THEN 1 END) as coupons_issued,
            COUNT(CASE WHEN r.status = 'escalated' THEN 1 END) as escalated_count,
            AVG(EXTRACT(EPOCH FROM (r.submitted_at - r.created_at))/3600) as avg_response_hours,
            DATE_TRUNC('day', r.created_at) as review_date
        FROM feedback.customer_reviews r
        GROUP BY r.station_id, r.rating, r.status, DATE_TRUNC('day', r.created_at)
    """)


def downgrade() -> None:
    """Remove customer review system."""
    
    # Drop views
    op.execute("DROP VIEW IF EXISTS feedback.review_analytics CASCADE")
    
    # Drop tables in reverse order
    op.drop_table('review_escalations', schema='feedback')
    op.drop_table('discount_coupons', schema='feedback')
    op.drop_table('customer_reviews', schema='feedback')
    
    # Drop enums
    op.execute("DROP TYPE IF EXISTS feedback.coupon_status")
    op.execute("DROP TYPE IF EXISTS feedback.review_status")
    op.execute("DROP TYPE IF EXISTS feedback.review_rating")
    
    # Drop schema
    op.execute("DROP SCHEMA IF EXISTS feedback CASCADE")
