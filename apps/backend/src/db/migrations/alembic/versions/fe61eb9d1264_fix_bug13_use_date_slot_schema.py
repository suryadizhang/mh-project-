"""fix_bug13_use_date_slot_schema

Revision ID: fe61eb9d1264
Revises: 5f96b4ae0faf
Create Date: 2025-11-25 16:42:45.914921

Bug #13: Fix Race Condition with Production Schema (date + slot)
=================================================================

This migration fixes the old 7e38568a1d1b migration which used booking_datetime
column that doesn't exist in production. Production uses date + slot columns.

Changes:
1. Drop old index idx_booking_datetime_active (if exists)
2. Create new partial unique index on (date, slot, status)
3. Add version column for optimistic locking

Three-layer defense against race conditions:
- Layer 1: Unique constraint (idx_booking_date_slot_active)
- Layer 2: Optimistic locking (version column)
- Layer 3: SELECT FOR UPDATE row locking (in repository code)
"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'fe61eb9d1264'
down_revision = '5f96b4ae0faf'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Drop old index if it exists (from 7e38568a1d1b migration)
    op.execute("DROP INDEX IF EXISTS idx_booking_datetime_active")

    # Add version column for optimistic locking (Layer 2)
    op.add_column(
        'bookings',
        sa.Column('version', sa.Integer(), nullable=False, server_default='1'),
        schema='core'
    )

    # Create partial unique index on (date, slot, status) (Layer 1)
    # Only active bookings are unique - cancelled/completed can be reused
    op.create_index(
        'idx_booking_date_slot_active',
        'bookings',
        ['date', 'slot', 'status'],
        unique=True,
        schema='core',
        postgresql_where=sa.text(
            "status NOT IN ('cancelled', 'completed', 'no_show') AND deleted_at IS NULL"
        )
    )


def downgrade() -> None:
    # Remove new index
    op.drop_index(
        'idx_booking_date_slot_active',
        table_name='bookings',
        schema='core'
    )

    # Remove version column
    op.drop_column('bookings', 'version', schema='core')

    # Restore old index (even though it won't work with production schema)
    op.execute("""
        CREATE UNIQUE INDEX IF NOT EXISTS idx_booking_datetime_active
        ON bookings(booking_datetime)
        WHERE status NOT IN ('cancelled', 'no_show')
    """)
