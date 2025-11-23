"""create_booking_reminders_table

Revision ID: 0e81266c9503
Revises: 53bf4e839c3c
Create Date: 2025-11-20 20:37:41.303762

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID


# revision identifiers, used by Alembic.
revision = '0e81266c9503'
down_revision = '53bf4e839c3c'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create booking_reminders table in public schema
    op.create_table(
        'booking_reminders',
        sa.Column('id', UUID(as_uuid=True), nullable=False, server_default=sa.text('gen_random_uuid()')),
        sa.Column('booking_id', UUID(as_uuid=True), nullable=False),
        sa.Column('reminder_type', sa.String(length=50), nullable=False),
        sa.Column('scheduled_for', sa.DateTime(timezone=True), nullable=False),
        sa.Column('sent_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('status', sa.String(length=50), nullable=False, server_default='pending'),
        sa.Column('message', sa.Text(), nullable=True),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('NOW()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('NOW()')),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['booking_id'], ['core.bookings.id'], ondelete='CASCADE'),
        schema='public',
    )
    
    # Create indexes for performance
    op.create_index('idx_reminders_booking', 'booking_reminders', ['booking_id'], schema='public')
    op.create_index('idx_reminders_status', 'booking_reminders', ['status'], schema='public')
    op.create_index(
        'idx_reminders_scheduled',
        'booking_reminders',
        ['scheduled_for'],
        schema='public',
        postgresql_where=sa.text("status = 'pending'")
    )


def downgrade() -> None:
    # Drop indexes
    op.drop_index('idx_reminders_scheduled', table_name='booking_reminders', schema='public')
    op.drop_index('idx_reminders_status', table_name='booking_reminders', schema='public')
    op.drop_index('idx_reminders_booking', table_name='booking_reminders', schema='public')
    
    # Drop table
    op.drop_table('booking_reminders', schema='public')
    op.drop_index('idx_reminders_status', table_name='booking_reminders')
    op.drop_index('idx_reminders_booking', table_name='booking_reminders')
    
    # Drop table
    op.drop_table('booking_reminders')