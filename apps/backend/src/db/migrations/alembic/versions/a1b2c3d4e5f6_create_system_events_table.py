"""create_system_events_table

Revision ID: a1b2c3d4e5f6
Revises: f069ddb440f7
Create Date: 2025-11-13 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSON

# revision identifiers, used by Alembic.
revision = 'a1b2c3d4e5f6'
down_revision = 'f069ddb440f7'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create system_events table for centralized event tracking."""
    
    op.create_table(
        'system_events',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('service', sa.String(length=100), nullable=False, comment='Service that logged the event'),
        sa.Column('action', sa.String(length=100), nullable=False, comment='Action performed'),
        sa.Column('entity_type', sa.String(length=50), nullable=True, comment='Type of entity'),
        sa.Column('entity_id', sa.Integer(), nullable=True, comment='ID of the entity'),
        sa.Column('user_id', sa.Integer(), nullable=True, comment='User who triggered the event'),
        sa.Column('metadata', JSON, nullable=False, server_default='{}', comment='Additional JSON data'),
        sa.Column('severity', sa.String(length=20), nullable=False, server_default='info', comment='Event severity'),
        sa.Column('timestamp', sa.DateTime(), nullable=False, server_default=sa.text('NOW()'), comment='When the event occurred'),
        sa.PrimaryKeyConstraint('id'),
        comment='System event tracking for analytics and audit trails'
    )
    
    # Create indexes for efficient querying
    op.create_index('ix_system_events_id', 'system_events', ['id'])
    op.create_index('ix_system_events_service', 'system_events', ['service'])
    op.create_index('ix_system_events_action', 'system_events', ['action'])
    op.create_index('ix_system_events_entity_type', 'system_events', ['entity_type'])
    op.create_index('ix_system_events_entity_id', 'system_events', ['entity_id'])
    op.create_index('ix_system_events_user_id', 'system_events', ['user_id'])
    op.create_index('ix_system_events_severity', 'system_events', ['severity'])
    op.create_index('ix_system_events_timestamp', 'system_events', ['timestamp'])
    
    # Composite indexes for common queries
    op.create_index('ix_system_events_entity_lookup', 'system_events', ['entity_type', 'entity_id', 'timestamp'])
    op.create_index('ix_system_events_user_timeline', 'system_events', ['user_id', 'timestamp'])
    op.create_index('ix_system_events_service_action', 'system_events', ['service', 'action', 'timestamp'])
    op.create_index('ix_system_events_severity_time', 'system_events', ['severity', 'timestamp'])
    op.create_index('ix_system_events_chronological', 'system_events', ['timestamp', 'service'])


def downgrade() -> None:
    """Drop system_events table and all indexes."""
    
    # Drop composite indexes
    op.drop_index('ix_system_events_chronological', table_name='system_events')
    op.drop_index('ix_system_events_severity_time', table_name='system_events')
    op.drop_index('ix_system_events_service_action', table_name='system_events')
    op.drop_index('ix_system_events_user_timeline', table_name='system_events')
    op.drop_index('ix_system_events_entity_lookup', table_name='system_events')
    
    # Drop single column indexes
    op.drop_index('ix_system_events_timestamp', table_name='system_events')
    op.drop_index('ix_system_events_severity', table_name='system_events')
    op.drop_index('ix_system_events_user_id', table_name='system_events')
    op.drop_index('ix_system_events_entity_id', table_name='system_events')
    op.drop_index('ix_system_events_entity_type', table_name='system_events')
    op.drop_index('ix_system_events_action', table_name='system_events')
    op.drop_index('ix_system_events_service', table_name='system_events')
    op.drop_index('ix_system_events_id', table_name='system_events')
    
    # Drop table
    op.drop_table('system_events')
