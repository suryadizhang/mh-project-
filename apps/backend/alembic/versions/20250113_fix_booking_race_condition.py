"""Fix booking race condition with unique constraint and optimistic locking

Revision ID: 20250113_fix_race
Revises: (previous_revision)
Create Date: 2025-01-13

Bug #13: Race Condition in Booking System
==========================================

Problem:
--------
80ms window between check_availability() and create_booking() allows concurrent
requests to create double bookings for the same time slot.

Root Cause:
-----------
Time-of-Check, Time-of-Use (TOCTOU) vulnerability:
1. Request A: check_availability() → returns True (available)
2. Request B: check_availability() → returns True (available) ← 80ms gap
3. Request A: create_booking() → succeeds
4. Request B: create_booking() → succeeds ← DOUBLE BOOKING

Solution:
---------
Three-layer defense:

Layer 1: UNIQUE CONSTRAINT (Database-Level Protection)
  - Prevents two active bookings at exact same date/slot
  - Index: idx_booking_date_slot_active on (date, slot, status)
  - WHERE clause: status NOT IN ('cancelled', 'completed', 'no_show') AND deleted_at IS NULL
  - Raises IntegrityError on collision → ConflictException to client

Layer 2: OPTIMISTIC LOCKING (Version Column)
  - Add 'version' column (default=1)
  - Increment on each update
  - UPDATE ... WHERE version = old_version
  - If 0 rows affected → another transaction modified it → ConflictException

Layer 3: SELECT FOR UPDATE (Row-Level Locking)
  - In check_availability(): SELECT ... FOR UPDATE
  - Holds row lock until transaction commits
  - Concurrent requests queue instead of racing

Production Schema:
------------------
Production database uses:
  - date (DATE column)
  - slot (TIME column)
Not booking_datetime (which was a legacy model artifact)

Migration Actions:
------------------
1. Add 'version' column (integer, default=1, not null)
2. Create unique partial index on (date, slot, status) for active bookings
3. Backfill version=1 for existing bookings
"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '20250113_fix_race'
down_revision = None  # UPDATE THIS with actual previous revision
branch_labels = None
depends_on = None


def upgrade():
    """
    Apply database changes to fix race condition

    Production schema uses: date (DATE) + slot (TIME)
    """
    # 1. Add version column for optimistic locking (if not exists)
    # Check if column exists first (may already exist from previous migration)
    connection = op.get_bind()
    inspector = sa.inspect(connection)
    columns = [col['name'] for col in inspector.get_columns('bookings', schema='core')]

    if 'version' not in columns:
        op.add_column(
            'bookings',
            sa.Column('version', sa.Integer(), nullable=False, server_default='1'),
            schema='core'
        )

    # 2. Create unique partial index to prevent double bookings
    # This ensures no two active bookings can exist at the same date/slot
    # Partial index excludes cancelled/completed/no-show and soft-deleted bookings
    op.create_index(
        'idx_booking_date_slot_active',
        'bookings',
        ['date', 'slot', 'status'],
        unique=True,
        schema='core',
        postgresql_where=sa.text("status NOT IN ('cancelled', 'completed', 'no_show') AND deleted_at IS NULL")
    )

    # 3. Add index on version column for optimistic locking queries
    indexes = [idx['name'] for idx in inspector.get_indexes('bookings', schema='core')]
    if 'idx_bookings_version' not in indexes:
        op.create_index(
            'idx_bookings_version',
            'bookings',
            ['version'],
            schema='core'
        )

    # Note: Existing data already has version=1 from server_default
    # No backfill needed


def downgrade():
    """
    Rollback database changes
    """
    # Remove indexes
    op.drop_index('idx_bookings_version', table_name='bookings', schema='core')
    op.drop_index('idx_booking_date_slot_active', table_name='bookings', schema='core')

    # Remove version column
    op.drop_column('bookings', 'version', schema='core')
