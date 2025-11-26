"""add_booking_datetime_unique_constraint_bug13

Revision ID: 7e38568a1d1b
Revises: 9029ba0ab3fb
Create Date: 2025-11-25 15:43:16.098329

Fixes Bug #13: Race condition allowing double bookings

Adds partial unique index on booking_datetime to prevent concurrent bookings
at the same time slot. Only enforces uniqueness for active bookings (excludes
cancelled and no_show statuses to allow rebooking).

This is Layer 1 defense (database-level) - works even if application code fails.
"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '7e38568a1d1b'
down_revision = '9029ba0ab3fb'  # ← Changed from 526069b41523 to 9029ba0ab3fb
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create partial unique index on booking_datetime
    # Prevents double bookings while allowing rebooking of cancelled slots
    op.execute("""
        CREATE UNIQUE INDEX idx_booking_datetime_active
        ON bookings(booking_datetime)
        WHERE status NOT IN ('cancelled', 'no_show')
    """)


def downgrade() -> None:
    # Remove unique index
    op.execute("DROP INDEX IF EXISTS idx_booking_datetime_active")
