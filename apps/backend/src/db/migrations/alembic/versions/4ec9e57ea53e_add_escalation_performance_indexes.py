"""add_escalation_performance_indexes

Revision ID: 4ec9e57ea53e
Revises: 73b5896f4fd5
Create Date: 2025-11-10 16:24:31.916827

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '4ec9e57ea53e'
down_revision = '73b5896f4fd5'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Add composite indexes for escalation query optimization."""
    # Check if escalations table exists before creating indexes
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    
    # Only create indexes if escalations table exists in support schema
    if 'support' in inspector.get_schema_names() and \
       'escalations' in [t for t in inspector.get_table_names(schema='support')]:
        
        # Index for status + priority queries
        op.create_index(
            'idx_escalations_status_priority',
            'escalations',
            ['status', 'priority', 'created_at'],
            schema='support'
        )
        
        # Index for admin assignment queries
        op.create_index(
            'idx_escalations_assigned_status',
            'escalations',
            ['assigned_to_id', 'status', 'updated_at'],
            schema='support'
        )
        
        # Index for customer escalation history
        op.create_index(
            'idx_escalations_customer_created',
            'escalations',
            ['customer_id', 'created_at'],
            schema='support'
        )
        
        # Index for time-based filtering with status
        op.create_index(
            'idx_escalations_created_status',
            'escalations',
            ['created_at', 'status'],
            schema='support'
        )


def downgrade() -> None:
    """Remove escalation performance indexes."""
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    
    # Only drop indexes if they exist
    if 'support' in inspector.get_schema_names():
        op.drop_index('idx_escalations_created_status', table_name='escalations', schema='support', if_exists=True)
        op.drop_index('idx_escalations_customer_created', table_name='escalations', schema='support', if_exists=True)
        op.drop_index('idx_escalations_assigned_status', table_name='escalations', schema='support', if_exists=True)
        op.drop_index('idx_escalations_status_priority', table_name='escalations', schema='support', if_exists=True)