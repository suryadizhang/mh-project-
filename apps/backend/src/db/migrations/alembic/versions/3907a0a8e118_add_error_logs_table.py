"""Add error_logs table

Revision ID: 3907a0a8e118
Revises: a1b2c3d4e5f6 (notification_groups)
Create Date: 2025-10-30 17:51:50.369544

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '3907a0a8e118'
down_revision = 'a1b2c3d4e5f6'  # notification_groups
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create error_logs table for admin monitoring
    op.create_table(
        'error_logs',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('correlation_id', sa.String(length=36), nullable=False),
        sa.Column('timestamp', sa.DateTime(), nullable=True),
        sa.Column('method', sa.String(length=10), nullable=True),
        sa.Column('path', sa.String(length=512), nullable=True),
        sa.Column('client_ip', sa.String(length=45), nullable=True),
        sa.Column('user_id', sa.Integer(), nullable=True),
        sa.Column('user_role', sa.String(length=50), nullable=True),
        sa.Column('error_type', sa.String(length=100), nullable=True),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('error_traceback', sa.Text(), nullable=True),
        sa.Column('status_code', sa.Integer(), nullable=True),
        sa.Column('request_body', sa.Text(), nullable=True),
        sa.Column('request_headers', sa.Text(), nullable=True),
        sa.Column('user_agent', sa.String(length=512), nullable=True),
        sa.Column('response_time_ms', sa.Integer(), nullable=True),
        sa.Column('level', sa.String(length=20), nullable=True),
        sa.Column('resolved', sa.Integer(), nullable=True),
        sa.Column('resolved_at', sa.DateTime(), nullable=True),
        sa.Column('resolved_by', sa.Integer(), nullable=True),
        sa.Column('resolution_notes', sa.Text(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create indexes
    op.create_index('ix_error_logs_correlation_id', 'error_logs', ['correlation_id'])
    op.create_index('ix_error_logs_timestamp', 'error_logs', ['timestamp'])
    op.create_index('ix_error_logs_user_id', 'error_logs', ['user_id'])
    op.create_index('ix_error_logs_level', 'error_logs', ['level'])


def downgrade() -> None:
    # Drop indexes
    op.drop_index('ix_error_logs_level', table_name='error_logs')
    op.drop_index('ix_error_logs_user_id', table_name='error_logs')
    op.drop_index('ix_error_logs_timestamp', table_name='error_logs')
    op.drop_index('ix_error_logs_correlation_id', table_name='error_logs')
    
    # Drop table
    op.drop_table('error_logs')