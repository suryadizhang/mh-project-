"""Add monitoring alert tables

Revision ID: 5f6cb2dfed84
Revises: 987eae60d297
Create Date: 2025-11-10 20:04:58.192492

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '5f6cb2dfed84'
down_revision = '987eae60d297'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create monitoring_alerts table
    op.create_table(
        'monitoring_alerts',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('alert_type', sa.String(length=100), nullable=False),
        sa.Column('category', sa.String(length=50), nullable=False),
        sa.Column('title', sa.String(length=255), nullable=False),
        sa.Column('message', sa.Text(), nullable=False),
        sa.Column('priority', sa.String(length=20), nullable=False),
        sa.Column('status', sa.String(length=20), nullable=False, server_default='active'),
        sa.Column('source', sa.String(length=100), nullable=True),
        sa.Column('resource', sa.String(length=255), nullable=True),
        sa.Column('metadata', sa.JSON(), nullable=True),
        sa.Column('metric_name', sa.String(length=100), nullable=True),
        sa.Column('metric_value', sa.String(length=50), nullable=True),
        sa.Column('threshold_value', sa.String(length=50), nullable=True),
        sa.Column('notification_channels', sa.JSON(), nullable=True),
        sa.Column('notification_sent_at', sa.DateTime(), nullable=True),
        sa.Column('notification_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('acknowledged_by', sa.String(length=255), nullable=True),
        sa.Column('acknowledged_at', sa.DateTime(), nullable=True),
        sa.Column('resolved_by', sa.String(length=255), nullable=True),
        sa.Column('resolved_at', sa.DateTime(), nullable=True),
        sa.Column('resolution_notes', sa.Text(), nullable=True),
        sa.Column('suppressed_until', sa.DateTime(), nullable=True),
        sa.Column('suppressed_by', sa.String(length=255), nullable=True),
        sa.Column('suppression_reason', sa.Text(), nullable=True),
        sa.Column('triggered_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.Column('expires_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create indexes for common queries
    op.create_index('idx_alerts_status', 'monitoring_alerts', ['status'])
    op.create_index('idx_alerts_priority', 'monitoring_alerts', ['priority'])
    op.create_index('idx_alerts_type', 'monitoring_alerts', ['alert_type'])
    op.create_index('idx_alerts_category', 'monitoring_alerts', ['category'])
    op.create_index('idx_alerts_triggered_at', 'monitoring_alerts', ['triggered_at'])
    op.create_index('idx_alerts_resource', 'monitoring_alerts', ['resource'])
    op.create_index('idx_alerts_active_priority', 'monitoring_alerts', ['status', 'priority'])
    
    # Create monitoring_alert_rules table
    op.create_table(
        'monitoring_alert_rules',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('alert_type', sa.String(length=100), nullable=False),
        sa.Column('category', sa.String(length=50), nullable=False),
        sa.Column('metric_name', sa.String(length=100), nullable=False),
        sa.Column('operator', sa.String(length=10), nullable=False),
        sa.Column('threshold', sa.Float(), nullable=False),
        sa.Column('duration_seconds', sa.Integer(), nullable=False, server_default='60'),
        sa.Column('priority', sa.String(length=20), nullable=False),
        sa.Column('notification_channels', sa.JSON(), nullable=True),
        sa.Column('cooldown_seconds', sa.Integer(), nullable=False, server_default='300'),
        sa.Column('is_enabled', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('last_triggered_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.Column('created_by', sa.String(length=255), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create indexes for alert rules
    op.create_index('idx_alert_rules_metric', 'monitoring_alert_rules', ['metric_name'])
    op.create_index('idx_alert_rules_enabled', 'monitoring_alert_rules', ['is_enabled'])
    op.create_index('idx_alert_rules_type', 'monitoring_alert_rules', ['alert_type'])


def downgrade() -> None:
    # Drop indexes first
    op.drop_index('idx_alert_rules_type', table_name='monitoring_alert_rules')
    op.drop_index('idx_alert_rules_enabled', table_name='monitoring_alert_rules')
    op.drop_index('idx_alert_rules_metric', table_name='monitoring_alert_rules')
    
    # Drop alert rules table
    op.drop_table('monitoring_alert_rules')
    
    # Drop alert indexes
    op.drop_index('idx_alerts_active_priority', table_name='monitoring_alerts')
    op.drop_index('idx_alerts_resource', table_name='monitoring_alerts')
    op.drop_index('idx_alerts_triggered_at', table_name='monitoring_alerts')
    op.drop_index('idx_alerts_category', table_name='monitoring_alerts')
    op.drop_index('idx_alerts_type', table_name='monitoring_alerts')
    op.drop_index('idx_alerts_priority', table_name='monitoring_alerts')
    op.drop_index('idx_alerts_status', table_name='monitoring_alerts')
    
    # Drop alerts table
    op.drop_table('monitoring_alerts')