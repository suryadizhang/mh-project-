"""create notification groups tables

Revision ID: a1b2c3d4e5f6
Revises: f069ddb440f7
Create Date: 2025-10-30 12:20:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
import uuid

# revision identifiers, used by Alembic.
revision = 'a1b2c3d4e5f6'
down_revision = 'f069ddb440f7'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create enum type for notification event types (if not exists)
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE notificationeventtype AS ENUM (
                'new_booking',
                'booking_edit',
                'booking_cancellation',
                'payment_received',
                'review_received',
                'complaint_received',
                'all'
            );
        EXCEPTION
            WHEN duplicate_object THEN null;
        END $$;
    """)
    
    # Create notification_groups table
    op.create_table(
        'notification_groups',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column('name', sa.String(100), nullable=False, unique=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('station_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('whatsapp_group_id', sa.String(100), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('created_by', postgresql.UUID(as_uuid=True), nullable=True)
    )
    
    # Create indexes for notification_groups
    op.create_index('idx_notification_groups_station_id', 'notification_groups', ['station_id'])
    op.create_index('idx_notification_groups_active', 'notification_groups', ['is_active'])
    
    # Create notification_group_members table
    op.create_table(
        'notification_group_members',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column('group_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('phone_number', sa.String(20), nullable=False),
        sa.Column('name', sa.String(100), nullable=False),
        sa.Column('email', sa.String(255), nullable=True),
        sa.Column('receive_whatsapp', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('receive_sms', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('receive_email', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('priority', sa.String(20), nullable=False, server_default='medium'),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('added_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('added_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.ForeignKeyConstraint(['group_id'], ['notification_groups.id'], ondelete='CASCADE')
    )
    
    # Create indexes for notification_group_members
    op.create_index('idx_notification_group_members_group_id', 'notification_group_members', ['group_id'])
    op.create_index('idx_notification_group_members_phone', 'notification_group_members', ['phone_number'])
    op.create_index('idx_notification_group_members_active', 'notification_group_members', ['is_active'])
    
    # Create notification_group_events table
    op.create_table(
        'notification_group_events',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column('group_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('event_type', sa.String(50), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('created_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.ForeignKeyConstraint(['group_id'], ['notification_groups.id'], ondelete='CASCADE'),
        sa.UniqueConstraint('group_id', 'event_type', name='uq_group_event')
    )
    
    # Create indexes for notification_group_events
    op.create_index('idx_notification_group_events_group_id', 'notification_group_events', ['group_id'])
    op.create_index('idx_notification_group_events_event_type', 'notification_group_events', ['event_type'])


def downgrade() -> None:
    # Drop tables
    op.drop_table('notification_group_events')
    op.drop_table('notification_group_members')
    op.drop_table('notification_groups')
