"""
Alembic migration: Create notification groups tables

Revision ID: create_notification_groups
Creates: notification_groups, notification_group_members, notification_group_events
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
from datetime import datetime

# revision identifiers
revision = 'create_notification_groups'
down_revision = None  # Replace with your latest migration
branch_labels = None
depends_on = None


def upgrade():
    """Create notification groups tables"""
    
    # 1. Create notification_groups table
    op.create_table(
        'notification_groups',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('name', sa.String(100), nullable=False, unique=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('station_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('whatsapp_group_id', sa.String(100), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.Column('created_by', postgresql.UUID(as_uuid=True), nullable=False),
    )
    
    # Create indexes
    op.create_index('ix_notification_groups_name', 'notification_groups', ['name'])
    op.create_index('ix_notification_groups_station_id', 'notification_groups', ['station_id'])
    
    # 2. Create notification_group_members table
    op.create_table(
        'notification_group_members',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('group_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('phone_number', sa.String(20), nullable=False),
        sa.Column('name', sa.String(100), nullable=False),
        sa.Column('email', sa.String(255), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('receive_whatsapp', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('receive_sms', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('receive_email', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('joined_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.Column('added_by', postgresql.UUID(as_uuid=True), nullable=False),
        sa.ForeignKeyConstraint(['group_id'], ['notification_groups.id'], ondelete='CASCADE'),
    )
    
    # Create indexes
    op.create_index('ix_notification_group_members_group_id', 'notification_group_members', ['group_id'])
    op.create_index('ix_notification_group_members_user_id', 'notification_group_members', ['user_id'])
    op.create_index('ix_notification_group_members_phone_number', 'notification_group_members', ['phone_number'])
    
    # 3. Create notification_group_events table
    op.create_table(
        'notification_group_events',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('group_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('event_type', sa.Enum(
            'new_booking',
            'booking_edit',
            'booking_cancellation',
            'payment_received',
            'review_received',
            'complaint_received',
            'all',
            name='notificationeventtype'
        ), nullable=False),
        sa.Column('priority_filter', postgresql.JSONB(), nullable=True),
        sa.Column('custom_filters', postgresql.JSONB(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.Column('created_by', postgresql.UUID(as_uuid=True), nullable=False),
        sa.ForeignKeyConstraint(['group_id'], ['notification_groups.id'], ondelete='CASCADE'),
    )
    
    # Create indexes
    op.create_index('ix_notification_group_events_group_id', 'notification_group_events', ['group_id'])
    op.create_index('ix_notification_group_events_event_type', 'notification_group_events', ['event_type'])


def downgrade():
    """Drop notification groups tables"""
    
    op.drop_table('notification_group_events')
    op.drop_table('notification_group_members')
    op.drop_table('notification_groups')
    
    # Drop enum type
    op.execute('DROP TYPE IF EXISTS notificationeventtype')
