"""Add deposit dual deadline system and manual confirmation

Revision ID: 013_add_deposit_deadline
Revises: 012_add_2fa_ip_verification
Create Date: 2025-11-15 00:00:00.000000

STRATEGY: Tell customers 2 hours (urgency), give them 24 hours (grace)
- customer_deposit_deadline: 2h - shown to customer
- internal_deadline: 24h - actual enforcement
- deposit_confirmed_at/by: Manual admin confirmation tracking
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "013_add_deposit_deadline"
down_revision = "012_add_2fa_ip_verification"
branch_labels = None
depends_on = None


def upgrade():
    """Add dual deadline system, manual confirmation, and hold fields to bookings table"""

    # Add customer-facing deposit deadline (2 hours - urgency)
    op.add_column("bookings", sa.Column("customer_deposit_deadline", sa.DateTime(), nullable=True), schema="core")

    # Add internal enforcement deadline (24 hours - grace period)
    op.add_column("bookings", sa.Column("internal_deadline", sa.DateTime(), nullable=True), schema="core")

    # Keep old deposit_deadline for backward compatibility
    op.add_column("bookings", sa.Column("deposit_deadline", sa.DateTime(), nullable=True), schema="core")

    # Add manual deposit confirmation tracking
    op.add_column("bookings", sa.Column("deposit_confirmed_at", sa.DateTime(), nullable=True), schema="core")
    op.add_column("bookings", sa.Column("deposit_confirmed_by", sa.String(255), nullable=True), schema="core")

    # Add hold fields for admin/CS to prevent auto-cancellation
    op.add_column(
        "bookings",
        sa.Column(
            "hold_on_request", sa.Boolean(), default=False, nullable=False, server_default="false"
        ),
        schema="core"
    )
    op.add_column("bookings", sa.Column("held_by", sa.String(255), nullable=True), schema="core")
    op.add_column("bookings", sa.Column("held_at", sa.DateTime(), nullable=True), schema="core")
    op.add_column("bookings", sa.Column("hold_reason", sa.Text(), nullable=True), schema="core")

    # Add indexes for efficient queries
    op.create_index(
        "ix_bookings_customer_deposit_deadline",
        "bookings",
        ["customer_deposit_deadline", "status"],
        unique=False,
        schema="core"
    )
    op.create_index(
        "ix_bookings_internal_deadline",
        "bookings",
        ["internal_deadline", "status", "hold_on_request", "deposit_confirmed_at"],
        unique=False,
        schema="core"
    )

    # Migrate existing PENDING bookings to dual deadline system
    # customer_deadline = created_at + 2h, internal_deadline = created_at + 24h
    op.execute(
        """
        UPDATE core.bookings 
        SET 
            customer_deposit_deadline = created_at + INTERVAL '2 hours',
            internal_deadline = created_at + INTERVAL '24 hours',
            deposit_deadline = created_at + INTERVAL '2 hours'
        WHERE status = 'deposit_pending' 
        AND created_at IS NOT NULL
    """
    )


def downgrade():
    """Remove dual deadline system, manual confirmation, and hold fields"""

    # Drop indexes
    op.drop_index("ix_bookings_internal_deadline", table_name="bookings", schema="core")
    op.drop_index("ix_bookings_customer_deposit_deadline", table_name="bookings", schema="core")

    # Drop hold columns
    op.drop_column("bookings", "hold_reason", schema="core")
    op.drop_column("bookings", "held_at", schema="core")
    op.drop_column("bookings", "held_by", schema="core")
    op.drop_column("bookings", "hold_on_request", schema="core")

    # Drop manual confirmation columns
    op.drop_column("bookings", "deposit_confirmed_by", schema="core")
    op.drop_column("bookings", "deposit_confirmed_at", schema="core")

    # Drop deadline columns
    op.drop_column("bookings", "deposit_deadline", schema="core")
    op.drop_column("bookings", "internal_deadline", schema="core")
    op.drop_column("bookings", "customer_deposit_deadline", schema="core")
