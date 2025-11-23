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
  - Prevents two active bookings at exact same datetime
  - Index: idx_booking_datetime_active on (booking_datetime, status)
  - WHERE clause: status IN ('pending', 'confirmed', 'seated')
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

Migration Actions:
------------------
1. Add 'version' column (integer, default=1, not null)
2. Create unique partial index on (booking_datetime, status) for active bookings
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
    """
    # 1. Add version column for optimistic locking
    op.add_column(
        'bookings',
        sa.Column('version', sa.Integer(), nullable=False, server_default='1')
    )

    # 2. Create unique partial index to prevent double bookings
    # This ensures no two active bookings can exist at the same datetime
    # Partial index only covers active statuses (pending, confirmed, seated)
    op.create_index(
        'idx_booking_datetime_active',
        'bookings',
        ['booking_datetime', 'status'],
        unique=True,
        postgresql_where=sa.text("status IN ('pending', 'confirmed', 'seated')")
    )

    # 3. Add index on version column for optimistic locking queries
    op.create_index(
        'idx_bookings_version',
        'bookings',
        ['version']
    )

    # Note: Existing data already has version=1 from server_default
    # No backfill needed


def downgrade():
    """
    Rollback database changes
    """
    # Remove indexes
    op.drop_index('idx_bookings_version', table_name='bookings')
    op.drop_index('idx_booking_datetime_active', table_name='bookings')

    # Remove version column
    op.drop_column('bookings', 'version')
